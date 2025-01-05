import os
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import threading
import win32event
import win32api
import winerror
import asyncio
from collections import OrderedDict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor
from config import *
from utils import (
    setup_logging,
    safe_move_file,
    get_file_category,
    is_file_in_use
)
from utils_win import add_to_startup, is_in_startup, show_welcome_notification
from gui import FileOrganizerGUI

# 互斥锁名称
MUTEX_NAME = "Global\\ClearBOOM_SingleInstance_Mutex"
# 全局互斥锁对象
g_mutex = None

class FileHandler(FileSystemEventHandler):
    def __init__(self, organizer):
        self.organizer = organizer
        self.cooldown = {}  # 文件事件冷却时间
        self.cooldown_time = 2  # 冷却时间（秒）

    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_event(event.src_path)

    def _handle_file_event(self, file_path):
        current_time = time.time()
        # 检查冷却时间
        if file_path in self.cooldown and current_time - self.cooldown[file_path] < self.cooldown_time:
            return
        self.cooldown[file_path] = current_time
        # 将文件添加到处理队列
        self.organizer.add_file_to_queue(Path(file_path))

class FileOrganizer:
    def __init__(self):
        self.running = False
        self.initialize_folders()
        self.gui: Optional[FileOrganizerGUI] = None
        
        # 使用OrderedDict实现LRU缓存
        self.cache_size = 10000  # 最大缓存条目数
        self.processed_files = OrderedDict()
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 创建处理队列
        self.process_queue = asyncio.Queue()
        
        # 创建文件系统监控
        self.event_handler = FileHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(DOWNLOADS_PATH), recursive=False)
        
        setup_logging()
        
        # 检查是否是首次运行
        if not is_in_startup():
            add_to_startup()

    def initialize_folders(self):
        """初始化所有必需的文件夹"""
        try:
            # 确保主要路径存在
            Path(DOWNLOADS_PATH).mkdir(exist_ok=True)
            Path(SCRIPT_PATH).mkdir(exist_ok=True)
            Path(LOGS_PATH).mkdir(exist_ok=True)
            Path(BACKUP_PATH).mkdir(exist_ok=True)
            
            # 创建分类文件夹
            for category, _ in FOLDER_MAPPING.items():
                folder_path = Path(DOWNLOADS_PATH) / category
                if not folder_path.exists():
                    folder_path.mkdir(exist_ok=True)
                    logging.info(f"创建分类文件夹: {category}")
                    
            logging.info("文件夹初始化完成")
        except Exception as e:
            logging.error(f"创建文件夹时出错: {e}")
            raise

    def set_gui(self, gui: FileOrganizerGUI):
        """设置GUI引用"""
        self.gui = gui

    def update_status(self, message: str):
        """更新GUI状态"""
        if self.gui:
            self.gui.update_status(message)

    def add_file_to_queue(self, file_path: Path):
        """添加文件到处理队列"""
        if self._should_process_file(file_path):
            asyncio.run_coroutine_threadsafe(
                self.process_queue.put(file_path),
                self.loop
            )

    def _should_process_file(self, file_path: Path) -> bool:
        """判断文件是否需要处理"""
        try:
            # 如果是文件夹或不存在，跳过
            if not file_path.exists() or file_path.is_dir():
                return False
            
            # 检查文件是否已在缓存中
            if str(file_path) in self.processed_files:
                return False
            
            # 检查文件名是否在保护列表中
            if file_path.name in PROTECTED_FOLDERS:
                return False
            
            # 检查父目录是否在保护列表中
            if any(parent.name in PROTECTED_FOLDERS for parent in file_path.parents):
                return False
            
            # 检查文件大小
            try:
                if file_path.stat().st_size > 1024 * 1024 * 1024:  # 1GB
                    logging.warning(f"文件过大，跳过处理: {file_path}")
                    return False
            except Exception:
                return False
                
            return True
            
        except Exception:
            return False

    async def process_file(self, file_path: Path) -> bool:
        """处理单个文件"""
        try:
            # 验证文件路径安全性
            if not is_safe_path(file_path):
                logging.error(f"文件路径不安全,跳过处理: {file_path}")
                return False
            
            category = get_file_category(file_path)
            if not category:
                logging.info(f"跳过未知类型文件: {file_path}")
                self._add_to_cache(str(file_path))
                return False

            dest_folder = DOWNLOADS_PATH / category
            # 验证目标文件夹路径安全性
            if not is_safe_path(dest_folder):
                logging.error(f"目标文件夹路径不安全: {dest_folder}")
                return False
            
            # 在线程池中执行文件移动操作
            result = await self.loop.run_in_executor(
                self.executor,
                safe_move_file,
                file_path,
                dest_folder
            )

            if result == Status.SUCCESS:
                self._add_to_cache(str(file_path))
                return True
            elif result == Status.FILE_IN_USE:
                logging.warning(f"文件被占用: {file_path}")
            elif result == Status.INSUFFICIENT_SPACE:
                logging.error("磁盘空间不足")
            elif result == Status.BACKUP_FAILED:
                logging.error(f"备份失败: {file_path}")
            elif result == Status.MOVE_FAILED:
                logging.error(f"移动失败: {file_path}")

        except Exception as e:
            logging.error(f"处理文件时出错 {file_path}: {e}")

        return False

    def _add_to_cache(self, file_path: str):
        """添加文件到LRU缓存"""
        self.processed_files[file_path] = time.time()
        if len(self.processed_files) > self.cache_size:
            self.processed_files.popitem(last=False)

    async def organize_files(self):
        """整理文件的主循环"""
        while self.running:
            try:
                # 处理队列中的文件
                while not self.process_queue.empty():
                    file_path = await self.process_queue.get()
                    if await self.process_file(file_path):
                        logging.info(f"成功处理文件: {file_path}")
                    else:
                        logging.info(f"跳过文件: {file_path}")
                    self.process_queue.task_done()
                
                # 定期清理
                await self.periodic_cleanup()
                
                # 等待新的文件
                await asyncio.sleep(1)

            except Exception as e:
                logging.error(f"整理文件时出错: {e}")
                self.update_status(f"整理出错: {e}")
                await asyncio.sleep(5)

    async def periodic_cleanup(self):
        """定期清理任务"""
        try:
            # 每小时执行一次
            current_time = time.time()
            if not hasattr(self, 'last_cleanup_time') or \
               current_time - self.last_cleanup_time > 3600:
                
                # 清理过期的缓存记录
                expired_time = current_time - 7 * 24 * 3600
                self.processed_files = OrderedDict(
                    (k, v) for k, v in self.processed_files.items()
                    if v > expired_time and os.path.exists(k)
                )
                
                self.last_cleanup_time = current_time
                
        except Exception as e:
            logging.error(f"定期清理任务出错: {e}")

    def scan_existing_files(self):
        """扫描现有文件"""
        try:
            logging.info("开始扫描现有文件...")
            
            # 先重新整理[TEMP]待清理文件夹
            from utils import reorganize_temp_folder
            reorganize_temp_folder()
            
            # 扫描下载文件夹中的文件
            count = 0
            for file_path in Path(DOWNLOADS_PATH).iterdir():
                if self._should_process_file(file_path):
                    self.add_file_to_queue(file_path)
                    count += 1
            logging.info(f"扫描完成，发现 {count} 个待处理文件")
        except Exception as e:
            logging.error(f"扫描现有文件时出错: {e}")

    def start(self):
        """开始整理"""
        if not self.running:
            self.running = True
            # 创建事件循环
            self.loop = asyncio.new_event_loop()
            # 在新线程中运行事件循环
            threading.Thread(target=self._run_event_loop, daemon=True).start()
            
            # 等待事件循环启动
            time.sleep(0.1)
            
            # 先扫描现有文件
            if USER_CONFIG["organize_on_startup"]:
                self.scan_existing_files()
            
            # 启动文件系统监控
            self.observer.start()
            
            logging.info("文件整理服务已启动")

    def _run_event_loop(self):
        """运行事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.organize_files())

    def stop(self):
        """停止整理"""
        self.running = False
        self.observer.stop()
        self.observer.join()
        self.executor.shutdown(wait=False)
        if hasattr(self, 'loop'):
            self.loop.stop()

def check_running_instance() -> bool:
    """检查是否已有实例在运行"""
    global g_mutex
    try:
        # 尝试创建一个命名互斥锁
        g_mutex = win32event.CreateMutex(None, True, MUTEX_NAME)
        last_error = win32api.GetLastError()
        
        # 如果互斥锁已存在，说明已有实例在运行
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            # 关闭我们的mutex句柄,因为我们不需要它
            if g_mutex:
                win32api.CloseHandle(g_mutex)
                g_mutex = None
            # 显示通知
            show_welcome_notification(
                on_click_callback=None,
                title="ClearBOOM 已在运行",
                message="程序已经在运行中，请检查系统托盘",
                sound="ms-winsoundevent:Notification.Default"
            )
            return True
            
        return False
        
    except Exception as e:
        logging.error(f"检查实例时出错: {e}")
        if g_mutex:
            win32api.CloseHandle(g_mutex)
            g_mutex = None
        return False

def verify_downloads_path() -> bool:
    """验证下载文件夹路径是否正确"""
    try:
        # 获取系统下载文件夹路径
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            system_downloads = Path(winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0])
        
        # 规范化路径进行比较
        downloads_path = Path(DOWNLOADS_PATH).resolve()
        system_downloads = system_downloads.resolve()
        
        if downloads_path != system_downloads:
            logging.error(f"配置的下载文件夹路径与系统下载文件夹不匹配!")
            logging.error(f"配置路径: {downloads_path}")
            logging.error(f"系统路径: {system_downloads}")
            return False
            
        logging.info(f"下载文件夹路径验证通过: {downloads_path}")
        return True
        
    except Exception as e:
        logging.error(f"验证下载文件夹路径时出错: {e}")
        return False

def is_safe_path(file_path: Path) -> bool:
    """检查文件路径是否安全(在下载文件夹内)"""
    try:
        # 规范化路径
        file_path = file_path.resolve()
        downloads_path = Path(DOWNLOADS_PATH).resolve()
        
        # 检查文件路径是否在下载文件夹内
        return str(file_path).startswith(str(downloads_path))
    except Exception as e:
        logging.error(f"检查路径安全性时出错: {e}")
        return False

def main():
    """主函数"""
    try:
        # 验证下载文件夹路径
        if not verify_downloads_path():
            logging.error("下载文件夹路径验证失败,程序退出")
            show_welcome_notification(
                on_click_callback=None,
                title="ClearBOOM 启动失败",
                message="下载文件夹路径验证失败,请检查配置",
                sound="ms-winsoundevent:Notification.Default"
            )
            sys.exit(1)
            
        # 检查是否已有实例在运行
        if check_running_instance():
            logging.info("程序已在运行")
            sys.exit(0)

        # 创建必要的目录
        for folder in FOLDER_MAPPING.keys():
            folder_path = DOWNLOADS_PATH / folder
            # 验证文件夹路径安全性
            if not is_safe_path(folder_path):
                logging.error(f"分类文件夹路径不安全: {folder_path}")
                sys.exit(1)
            folder_path.mkdir(exist_ok=True)
            
        # 验证备份和日志路径
        if not is_safe_path(BACKUP_PATH) or not is_safe_path(LOGS_PATH):
            logging.error("备份或日志文件夹路径不安全")
            sys.exit(1)
            
        BACKUP_PATH.mkdir(exist_ok=True)
        LOGS_PATH.mkdir(exist_ok=True)

        # 初始化组件
        organizer = FileOrganizer()
        gui = FileOrganizerGUI(organizer)
        organizer.set_gui(gui)

        # 运行GUI
        gui.run()

    except Exception as e:
        logging.error(f"程序启动失败: {e}")
        raise

if __name__ == "__main__":
    main() 