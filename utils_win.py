import os
import sys
import winreg
import logging
from pathlib import Path
from win11toast import toast

def show_welcome_notification(on_click_callback=None, title=None, message=None, sound=None):
    """显示通知"""
    try:
        def callback(args):
            if on_click_callback:
                on_click_callback()
                
        toast(
            title or "ClearBOOM 已启动",
            message or "程序将在后台自动整理您的下载文件夹\n点击此通知显示主窗口",
            on_click=callback if on_click_callback else None,
            duration="short",
            app_id="ClearBOOM",
            icon=None,
            audio={"src": sound} if sound else None
        )
    except Exception as e:
        logging.error(f"显示通知失败: {e}")

def add_to_startup(file_path: str = None) -> bool:
    """添加程序到开机自启动"""
    try:
        if file_path is None:
            file_path = sys.argv[0]
        
        if not os.path.exists(file_path):
            return False

        # 获取完整路径
        file_path = os.path.abspath(file_path)
        
        # 如果是Python文件，使用pythonw.exe运行（无控制台窗口）
        if file_path.endswith('.py'):
            python_path = os.path.join(sys.prefix, 'pythonw.exe')
            command = f'"{python_path}" "{file_path}"'
        else:
            command = f'"{file_path}"'

        # 打开注册表项
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        # 写入注册表
        winreg.SetValueEx(
            key,
            "FileOrganizer",
            0,
            winreg.REG_SZ,
            command
        )

        winreg.CloseKey(key)
        logging.info("已添加到开机自启动")
        return True

    except Exception as e:
        logging.error(f"添加开机自启动失败: {e}")
        return False

def remove_from_startup() -> bool:
    """从开机自启动中移除程序"""
    try:
        # 打开注册表项
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        # 删除注册表项
        winreg.DeleteValue(key, "FileOrganizer")
        winreg.CloseKey(key)
        logging.info("已从开机自启动中移除")
        return True

    except Exception as e:
        logging.error(f"从开机自启动移除失败: {e}")
        return False

def is_in_startup() -> bool:
    """检查程序是否在开机自启动中"""
    try:
        # 打开注册表项
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )

        # 检查是否存在
        try:
            winreg.QueryValueEx(key, "FileOrganizer")
            exists = True
        except WindowsError:
            exists = False

        winreg.CloseKey(key)
        return exists

    except Exception:
        return False 