import os
import shutil
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import psutil
from config import *
from logging.handlers import RotatingFileHandler
import fnmatch
import send2trash

def setup_logging() -> None:
    """配置日志系统"""
    try:
        # 确保日志目录存在
        Path(LOGS_PATH).mkdir(exist_ok=True)
        
        # 生成日志文件路径
        log_file = LOGS_PATH / f"organizer_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 创建 RotatingFileHandler
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=5*1024*1024,      # 5MB
            backupCount=5,             # 保留5个备份
            encoding=LOG_ENCODING
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 清除现有的处理器
        root_logger.handlers.clear()
        
        # 添加处理器
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # 清理旧日志文件
        clean_old_logs()
        
        logging.info("日志系统初始化完成")
        
    except Exception as e:
        print(f"设置日志系统时出错: {e}")
        raise

def clean_old_logs(max_days: int = 7):
    """清理旧的日志文件"""
    try:
        current_time = datetime.now()
        for log_file in Path(LOGS_PATH).glob("organizer_*.log*"):
            # 获取文件修改时间
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            # 如果文件超过指定天数,则删除
            if (current_time - file_time).days > max_days:
                log_file.unlink()
                print(f"已删除旧日志文件: {log_file}")
    except Exception as e:
        print(f"清理旧日志文件时出错: {e}")

def is_file_in_use(file_path: Path) -> bool:
    """检查文件是否被占用"""
    try:
        with open(file_path, 'rb'):
            return False
    except (IOError, PermissionError):
        return True

def get_file_category(file_path: Path) -> Optional[str]:
    """获取文件类别"""
    # 跳过临时文件
    if file_path.suffix.lower() in ['.tmp', '.crdownload', '.part']:
        logging.debug(f"跳过浏览器下载临时文件: {file_path}")
        return None
        
    extension = file_path.suffix.lower()
    for category, config in FOLDER_MAPPING.items():
        # 检查是否启用自动整理
        if not config.get("auto_organize", True):
            continue
            
        if extension in config["extensions"]:
            return category
    return None

def get_subfolder(category: str, file_path: Path) -> Optional[str]:
    """获取二级分类文件夹名称"""
    if category not in FOLDER_MAPPING:
        return None
        
    config = FOLDER_MAPPING[category]
    if "subfolders" not in config:
        return None
        
    extension = file_path.suffix.lower()
    for subfolder, extensions in config["subfolders"].items():
        if not extensions or extension in extensions:
            return subfolder
            
    return None

def check_disk_space(path: Path) -> bool:
    """检查磁盘空间是否足够"""
    try:
        # 将Path对象转换为字符串
        path_str = str(path)
        free_space = psutil.disk_usage(path_str).free
        return free_space > MIN_FREE_SPACE_GB * 1024 * 1024 * 1024
    except Exception as e:
        logging.error(f"检查磁盘空间时出错: {e}")
        return False

def create_backup(file_path: Path) -> Tuple[bool, Optional[Path]]:
    """创建文件备份"""
    try:
        backup_dir = BACKUP_PATH / datetime.now().strftime("%Y%m%d")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / file_path.name
        
        if backup_path.exists():
            backup_path = backup_dir / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
        
        shutil.copy2(file_path, backup_path)
        logging.info(f"已备份文件: {file_path} -> {backup_path}")
        return True, backup_path
    except Exception as e:
        logging.error(f"备份文件失败 {file_path}: {e}")
        return False, None

def safe_move_file(file_path: Path, dest_folder: Path) -> int:
    """安全地移动文件"""
    try:
        if not check_disk_space(dest_folder):
            return Status.INSUFFICIENT_SPACE

        if is_file_in_use(file_path):
            return Status.FILE_IN_USE

        # 创建备份
        success, backup_path = create_backup(file_path)
        if not success:
            return Status.BACKUP_FAILED

        # 获取文件分类
        category = get_file_category(file_path)
        if not category:
            return Status.INVALID_PATH
            
        # 检查是否需要二级分类
        subfolder = get_subfolder(category, file_path)
        if subfolder:
            dest_folder = dest_folder / subfolder
            
        dest_folder.mkdir(parents=True, exist_ok=True)
        dest_path = dest_folder / file_path.name
        
        # 处理目标位置已存在同名文件的情况
        if dest_path.exists():
            dest_path = dest_folder / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"

        # 移动文件
        shutil.move(str(file_path), str(dest_path))
        logging.info(f"已移动文件: {file_path} -> {dest_path}")
        
        # 移动成功后删除备份
        if backup_path and backup_path.exists():
            backup_path.unlink()
            logging.debug(f"已删除备份文件: {backup_path}")
            
        return Status.SUCCESS

    except Exception as e:
        logging.error(f"移动文件失败 {file_path}: {e}")
        # 移动失败时尝试从备份恢复
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, file_path)
                logging.info(f"已从备份恢复文件: {backup_path} -> {file_path}")
            except Exception as restore_error:
                logging.error(f"恢复备份失败: {restore_error}")
        return Status.MOVE_FAILED


def get_file_stats() -> dict:
    """获取文件统计信息"""
    stats = {category: 0 for category in FOLDER_MAPPING.keys()}
    stats["未分类"] = 0
    
    try:
        for file_path in DOWNLOADS_PATH.iterdir():
            if file_path.is_file():
                category = get_file_category(file_path)
                if category:
                    stats[category] += 1
                else:
                    stats["未分类"] += 1
    except Exception as e:
        logging.error(f"获取文件统计信息时出错: {e}")
    
    return stats

def get_recent_logs(lines: int = 100) -> List[str]:
    """获取最近的日志记录"""
    try:
        # 获取最新的日志文件
        log_files = sorted(Path(LOGS_PATH).glob("organizer_*.log*"), reverse=True)
        if not log_files:
            return []
            
        recent_logs = []
        remaining_lines = lines
        
        # 从最新的日志文件开始读取
        for log_file in log_files:
            if remaining_lines <= 0:
                break
                
            try:
                with open(log_file, 'r', encoding=LOG_ENCODING) as f:
                    # 读取所有行并反转,这样可以从最新的开始
                    file_lines = f.readlines()[::-1]
                    # 取需要的行数
                    recent_logs.extend(file_lines[:remaining_lines])
                    remaining_lines -= len(file_lines)
            except Exception as e:
                logging.error(f"读取日志文件出错 {log_file}: {e}")
                
        # 反转回正确的顺序并返回
        return recent_logs[::-1]
        
    except Exception as e:
        logging.error(f"获取最近日志时出错: {e}")
        return [] 

def reorganize_temp_folder() -> None:
    """重新整理[TEMP]待清理文件夹"""
    try:
        temp_folder = DOWNLOADS_PATH / "[TEMP] 待清理"
        if not temp_folder.exists():
            return
            
        logging.info("开始重新整理[TEMP]待清理文件夹...")
        count = 0
        
        # 获取所有文件（包括子文件夹中的文件）
        for file_path in temp_folder.rglob("*"):
            if not file_path.is_file():
                continue
                
            # 获取正确的子文件夹
            subfolder = get_subfolder("[TEMP] 待清理", file_path)
            if not subfolder:
                continue
                
            # 计算目标路径
            dest_folder = temp_folder / subfolder
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            # 如果文件已经在正确的子文件夹中，跳过
            if file_path.parent == dest_folder:
                continue
                
            try:
                # 处理目标位置已存在同名文件的情况
                dest_path = dest_folder / file_path.name
                if dest_path.exists():
                    dest_path = dest_folder / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
                
                # 移动文件
                shutil.move(str(file_path), str(dest_path))
                count += 1
                logging.info(f"已整理文件: {file_path.name} -> {subfolder}/")
                
            except Exception as e:
                logging.error(f"整理文件失败 {file_path}: {e}")
                
        if count > 0:
            logging.info(f"[TEMP]待清理文件夹整理完成，共处理 {count} 个文件")
        else:
            logging.info("[TEMP]待清理文件夹已是最新状态")
            
        # 清理空文件夹
        clean_empty_folders(temp_folder)
        
    except Exception as e:
        logging.error(f"整理[TEMP]待清理文件夹时出错: {e}")

def clean_empty_folders(folder: Path) -> None:
    """清理空文件夹"""
    try:
        for subfolder in folder.iterdir():
            if subfolder.is_dir():
                clean_empty_folders(subfolder)  # 递归清理子文件夹
                try:
                    subfolder.rmdir()  # 尝试删除文件夹（只有空文件夹才能删除）
                    logging.info(f"已删除空文件夹: {subfolder}")
                except OSError:
                    pass  # 文件夹不为空，忽略错误
    except Exception as e:
        logging.error(f"清理空文件夹时出错: {e}") 

def check_cleanup_rules(file_path: Path) -> Tuple[bool, str]:
    """检查文件是否符合清理规则
    返回: (是否应该清理, 原因)"""
    try:
        # 检查排除模式
        for pattern in CLEANUP_CONFIG.get("exclude_patterns", []):
            if fnmatch.fnmatch(file_path.name, pattern):
                return False, "文件名匹配排除模式"
        
        # 检查文件年龄
        if CLEANUP_CONFIG.get("rules", {}).get("age", {}).get("enabled", False):
            days = CLEANUP_CONFIG["rules"]["age"].get("days", 30)
            age = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
            if age > days:
                return True, f"文件超过{days}天未修改"
        
        # 检查文件大小
        if CLEANUP_CONFIG.get("rules", {}).get("size", {}).get("enabled", False):
            max_size = CLEANUP_CONFIG["rules"]["size"].get("max_size_mb", 1024)  # 默认1GB
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > max_size:
                return True, f"文件大小超过{max_size}MB"
        
        # 检查文件类型
        if CLEANUP_CONFIG.get("rules", {}).get("type", {}).get("enabled", False):
            extensions = CLEANUP_CONFIG["rules"]["type"].get("extensions", [])
            if file_path.suffix.lower() in extensions:
                return True, f"文件类型{file_path.suffix}在清理列表中"
        
        return False, "文件不符合清理规则"
        
    except Exception as e:
        logging.error(f"检查清理规则时出错 {file_path}: {str(e)}")
        return False, f"检查规则出错: {str(e)}"

def scan_files_for_cleanup() -> List[Tuple[Path, str]]:
    """扫描需要清理的文件
    返回: [(文件路径, 清理原因)]"""
    cleanup_files = []
    try:
        logging.info("开始扫描需要清理的文件...")
        # 只扫描启用的文件夹
        for folder_name in CLEANUP_CONFIG["enabled_folders"]:
            folder_path = DOWNLOADS_PATH / folder_name
            if not folder_path.exists():
                logging.info(f"跳过不存在的文件夹: {folder_name}")
                continue

            logging.info(f"正在扫描文件夹: {folder_name}")
            # 扫描文件夹中的所有文件
            for file_path in folder_path.rglob("*"):
                if not file_path.is_file():
                    continue

                should_cleanup, reason = check_cleanup_rules(file_path)
                if should_cleanup:
                    cleanup_files.append((file_path, reason))
                    logging.info(f"找到需要清理的文件: {file_path} (原因: {reason})")

        logging.info(f"扫描完成，共找到 {len(cleanup_files)} 个需要清理的文件")

    except Exception as e:
        logging.error(f"扫描清理文件时出错: {e}")

    return cleanup_files

def cleanup_files(files: List[Tuple[Path, str]], callback=None) -> Dict[str, int]:
    """清理文件
    参数:
        files: 要清理的文件列表
        callback: 进度回调函数
    返回: 清理结果统计"""
    stats = {
        "total": len(files),
        "success": 0,
        "failed": 0,
        "skipped": 0
    }

    if not files:
        logging.info("没有需要清理的文件")
        return stats

    try:
        logging.info(f"开始清理文件，共 {len(files)} 个文件")
        
        # 记录是否有回调函数
        logging.info(f"回调函数状态: {'已设置' if callback else '未设置'}")
        logging.info(f"是否需要确认: {CLEANUP_CONFIG['require_confirmation']}")
        
        # 如果需要确认且没有回调函数，直接返回
        if CLEANUP_CONFIG["require_confirmation"] and not callback:
            logging.info("需要用户确认但没有回调函数，跳过清理")
            stats["skipped"] = len(files)
            return stats

        for i, (file_path, reason) in enumerate(files, 1):
            try:
                # 更新进度
                if callback:
                    callback(i, len(files), file_path, reason)
                logging.info(f"正在处理第 {i}/{len(files)} 个文件: {file_path}")

                # 如果文件不存在，跳过
                if not file_path.exists():
                    logging.info(f"文件不存在，跳过: {file_path}")
                    stats["skipped"] += 1
                    continue

                # 如果文件被占用，跳过
                if is_file_in_use(file_path):
                    logging.info(f"文件被占用，跳过: {file_path}")
                    stats["skipped"] += 1
                    continue

                # 删除文件
                try:
                    if CLEANUP_CONFIG["safe_mode"]:
                        logging.info(f"移动到回收站: {file_path}")
                        send2trash.send2trash(str(file_path))
                    else:
                        logging.info(f"直接删除文件: {file_path}")
                        file_path.unlink()

                    stats["success"] += 1
                    logging.info(f"已清理文件: {file_path} (原因: {reason})")
                except Exception as e:
                    logging.error(f"删除文件失败 {file_path}: {e}")
                    stats["failed"] += 1

            except Exception as e:
                logging.error(f"处理文件失败 {file_path}: {e}")
                stats["failed"] += 1

        # 如果需要清理空文件夹
        if CLEANUP_CONFIG["cleanup_empty_folders"]:
            logging.info("开始清理空文件夹...")
            for folder_name in CLEANUP_CONFIG["enabled_folders"]:
                folder_path = DOWNLOADS_PATH / folder_name
                if folder_path.exists():
                    clean_empty_folders(folder_path)

        logging.info(f"清理完成。成功: {stats['success']}, 失败: {stats['failed']}, 跳过: {stats['skipped']}")

    except Exception as e:
        logging.error(f"清理文件时出错: {e}")

    return stats 