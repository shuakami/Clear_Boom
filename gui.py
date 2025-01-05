import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime
from pathlib import Path
import pystray
from PIL import Image
import io
import base64
import customtkinter as ctk
from config import *
from utils import get_file_stats, get_recent_logs
from utils_win import show_welcome_notification
import logging
import queue

# 设置主题和外观
ctk.set_appearance_mode("light")  # 使用亮色主题
ctk.set_default_color_theme("blue")  # 使用蓝色主题

# 自定义颜色
COLORS = {
    "primary": "#2B7DE9",      # 主色调(蓝色)
    "success": "#28C840",      # 成功色(绿色)
    "warning": "#FFB302",      # 警告色(橙色)
    "error": "#FF3B30",        # 错误色(红色)
    "background": "#FFFFFF",   # 背景色(白色)
    "text": "#000000",         # 文本色(黑色)
    "text_secondary": "#666666" # 次要文本色(灰色)
}

# 系统托盘图标（base64编码的1x1像素透明PNG）
TRAY_ICON = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=='
)

class FileOrganizerGUI:
    def __init__(self, organizer):
        self.organizer = organizer
        self.root = ctk.CTk()
        self.root.title(GUI_TITLE)
        self.root.geometry(GUI_GEOMETRY)
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 设置窗口背景色
        self.root.configure(fg_color=COLORS["background"])
        
        # 创建消息队列
        self.msg_queue = queue.Queue()
        
        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # 立即隐藏窗口
        self.root.withdraw()
        
        self.setup_gui()
        self.is_organizing = False
        self.setup_tray()
        
        # 显示欢迎通知
        show_welcome_notification(lambda: self.msg_queue.put(("show_window", None)))
        
        # 启动时自动开始整理
        self.root.after(1000, self.start_organize)
        
        # 启动消息处理
        self.root.after(100, self.process_messages)
        
        # 启动日志和统计更新
        self.update_logs()
        self.update_stats()

    def process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg[0] == "show_window":
                    self.show_window()
                elif msg[0] == "start_organize":
                    self.start_organize()
                elif msg[0] == "stop_organize":
                    self.stop_organize()
                elif msg[0] == "quit":
                    self.root.quit()
        except queue.Empty:
            pass
        self.root.after(100, self.process_messages)

    def auto_start(self):
        """自动开始整理并最小化到托盘"""
        self.start_organize()
        self.minimize_to_tray()

    def setup_tray(self):
        """设置系统托盘"""
        # 创建托盘图标
        icon = Image.new('RGBA', (64, 64), color=(73, 109, 137, 255))
        
        menu = (
            pystray.MenuItem('显示主窗口', lambda: self.msg_queue.put(("show_window", None))),
            pystray.MenuItem('开始整理', lambda: self.msg_queue.put(("start_organize", None))),
            pystray.MenuItem('停止整理', lambda: self.msg_queue.put(("stop_organize", None))),
            pystray.MenuItem('退出程序', lambda: self.msg_queue.put(("quit", None)))
        )
        
        self.tray_icon = pystray.Icon(
            "file_organizer",
            icon,
            "文件自动整理",
            menu
        )
        
        # 添加双击回调
        self.tray_icon.on_activate = lambda: self.msg_queue.put(("show_window", None))
        
        # 在新线程中运行托盘图标
        threading.Thread(target=self.run_tray, daemon=True).start()

    def run_tray(self):
        """运行托盘图标"""
        try:
            self.tray_icon.run()
        except Exception as e:
            logging.error(f"托盘图标运行出错: {e}")
            # 如果托盘图标运行失败，显示主窗口
            self.root.after(0, self.show_window)

    def minimize_to_tray(self):
        """最小化到系统托盘"""
        self.root.withdraw()
        self.tray_icon.visible = True

    def show_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self):
        """退出应用"""
        self.stop_organize()
        self.tray_icon.visible = False
        self.tray_icon.stop()
        self.root.quit()

    def setup_gui(self):
        """设置GUI界面"""
        # 创建主框架
        main_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color=COLORS["background"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=COLORS["background"])
        status_frame.pack(fill=tk.X, padx=15, pady=15)
        
        status_label = ctk.CTkLabel(
            status_frame, 
            textvariable=self.status_var,
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=COLORS["text"]
        )
        status_label.pack(pady=10)

        # 控制按钮
        control_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=COLORS["background"])
        control_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        # 基础按钮样式
        button_style = {
            "font": ("Microsoft YaHei UI", 13),
            "corner_radius": 8,
            "border_width": 0,
            "height": 35
        }

        # 普通按钮样式
        normal_style = button_style.copy()
        normal_style.update({
            "fg_color": COLORS["primary"],
            "hover_color": "#1E6FD9"
        })

        # 警告按钮样式
        warning_style = button_style.copy()
        warning_style.update({
            "fg_color": COLORS["warning"],
            "hover_color": "#E5A102"
        })

        # 错误按钮样式
        error_style = button_style.copy()
        error_style.update({
            "fg_color": COLORS["error"],
            "hover_color": "#E5361E"
        })

        self.organize_btn = ctk.CTkButton(
            control_frame, 
            text="开始整理",
            command=self.toggle_organize,
            **normal_style
        )
        self.organize_btn.pack(side=tk.LEFT, padx=10, pady=10)

        ctk.CTkButton(
            control_frame,
            text="查看日志",
            command=self.show_logs,
            **normal_style
        ).pack(side=tk.LEFT, padx=10, pady=10)

        ctk.CTkButton(
            control_frame,
            text="刷新统计",
            command=self.update_stats,
            **normal_style
        ).pack(side=tk.LEFT, padx=10, pady=10)

        # 添加清理按钮
        ctk.CTkButton(
            control_frame,
            text="清理文件",
            command=self.show_cleanup_dialog,
            **warning_style
        ).pack(side=tk.LEFT, padx=10, pady=10)

        ctk.CTkButton(
            control_frame,
            text="最小化到托盘",
            command=self.minimize_to_tray,
            **normal_style
        ).pack(side=tk.LEFT, padx=10, pady=10)

        # 创建左右分栏
        content_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # 统计信息（左侧）
        stats_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color="#F8F9FA")
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=0)
        
        ctk.CTkLabel(
            stats_frame,
            text="文件统计",
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=COLORS["text"]
        ).pack(pady=15)
        
        self.stats_labels = {}
        self.setup_stats_labels(stats_frame)

        # 日志显示（右侧）
        log_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color="#F8F9FA")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=0)
        
        ctk.CTkLabel(
            log_frame,
            text="最近日志",
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=COLORS["text"]
        ).pack(pady=15)
        
        self.log_text = ctk.CTkTextbox(
            log_frame, 
            wrap=tk.WORD,
            font=("Microsoft YaHei UI", 12),
            corner_radius=8,
            fg_color="white",
            text_color=COLORS["text"]
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

    def setup_stats_labels(self, parent):
        """设置统计标签"""
        stats_container = ctk.CTkFrame(parent, corner_radius=8, fg_color="transparent")
        stats_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        for i, category in enumerate(FOLDER_MAPPING.keys()):
            label_frame = ctk.CTkFrame(stats_container, corner_radius=6, fg_color="white")
            label_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ctk.CTkLabel(
                label_frame,
                text=f"{category}:",
                font=("Microsoft YaHei UI", 13),
                text_color=COLORS["text_secondary"]
            ).pack(side=tk.LEFT, padx=10, pady=8)
            
            self.stats_labels[category] = tk.StringVar(value="0")
            ctk.CTkLabel(
                label_frame,
                textvariable=self.stats_labels[category],
                font=("Microsoft YaHei UI", 13, "bold"),
                text_color=COLORS["text"]
            ).pack(side=tk.RIGHT, padx=10, pady=8)

        # 添加未分类统计
        label_frame = ctk.CTkFrame(stats_container, corner_radius=6, fg_color="white")
        label_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(
            label_frame,
            text="未分类:",
            font=("Microsoft YaHei UI", 13),
            text_color=COLORS["text_secondary"]
        ).pack(side=tk.LEFT, padx=10, pady=8)
        
        self.stats_labels["未分类"] = tk.StringVar(value="0")
        ctk.CTkLabel(
            label_frame,
            textvariable=self.stats_labels["未分类"],
            font=("Microsoft YaHei UI", 13, "bold"),
            text_color=COLORS["text"]
        ).pack(side=tk.RIGHT, padx=10, pady=8)

    def toggle_organize(self):
        """切换整理状态"""
        if not self.is_organizing:
            self.start_organize()
        else:
            self.stop_organize()

    def start_organize(self):
        """开始整理"""
        self.is_organizing = True
        self.organize_btn.configure(text="停止整理")
        self.status_var.set("正在整理...")
        threading.Thread(target=self.organizer.start, daemon=True).start()

    def stop_organize(self):
        """停止整理"""
        self.is_organizing = False
        self.organize_btn.configure(text="开始整理")
        self.status_var.set("已停止")
        self.organizer.stop()

    def update_stats(self):
        """更新统计信息"""
        stats = get_file_stats()
        for category, count in stats.items():
            if category in self.stats_labels:
                self.stats_labels[category].set(str(count))
        self.root.after(GUI_REFRESH_INTERVAL, self.update_stats)

    def update_logs(self):
        """更新日志显示"""
        try:
            # 获取当前滚动位置
            current_pos = self.log_text.yview()
            
            # 获取当前文本和新日志
            current_text = self.log_text.get("1.0", tk.END).strip()
            new_logs = "".join(get_recent_logs(100)).strip()
            
            # 只有当日志内容变化时才更新
            if new_logs != current_text:
                # 判断是否在底部
                at_bottom = current_pos[1] >= 0.99
                
                # 更新文本
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert(tk.END, new_logs)
                
                # 只有在底部时才自动滚动
                if at_bottom:
                    self.log_text.after(10, lambda: self.log_text.see(tk.END))
        except Exception as e:
            logging.error(f"更新日志出错: {e}")
            
        self.root.after(GUI_REFRESH_INTERVAL, self.update_logs)

    def show_logs(self):
        """显示完整日志"""
        log_window = ctk.CTkToplevel(self.root)
        log_window.title("完整日志")
        log_window.geometry("800x600")
        log_window.minsize(600, 400)
        log_window.configure(fg_color=COLORS["background"])

        log_text = ctk.CTkTextbox(
            log_window, 
            wrap=tk.WORD,
            font=("Microsoft YaHei UI", 12),
            corner_radius=8,
            fg_color="white",
            text_color=COLORS["text"]
        )
        log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 使用after延迟插入文本,避免窗口大小调整时的闪烁
        def insert_logs():
            logs = get_recent_logs(1000)
            log_text.delete("1.0", tk.END)
            log_text.insert(tk.END, "".join(logs))
            log_text.after(10, lambda: log_text.see(tk.END))
            
        log_window.after(100, insert_logs)

    def show_cleanup_dialog(self):
        """显示清理对话框"""
        from utils import scan_files_for_cleanup, cleanup_files
        
        # 定义按钮样式
        button_style = {
            "font": ("Microsoft YaHei UI", 13),
            "corner_radius": 8,
            "border_width": 0,
            "height": 35
        }
        
        # 警告按钮样式
        warning_style = button_style.copy()
        warning_style.update({
            "fg_color": COLORS["warning"],
            "hover_color": "#E5A102"
        })
        
        # 扫描需要清理的文件
        progress_var = tk.StringVar(value="正在扫描文件...")
        progress_label = ctk.CTkLabel(
            self.root,
            textvariable=progress_var,
            font=("Microsoft YaHei UI", 12)
        )
        progress_label.pack(side=tk.BOTTOM, padx=10, pady=5)
        self.root.update()
        
        cleanup_list = scan_files_for_cleanup()
        progress_label.destroy()
        
        if not cleanup_list:
            tk.messagebox.showinfo("清理文件", "没有找到需要清理的文件")
            return
            
        # 创建清理对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("清理文件")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 文件列表
        list_frame = ctk.CTkFrame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建Treeview
        columns = ("文件名", "大小", "修改时间", "清理原因")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # 添加文件
        for file_path, reason in cleanup_list:
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                tree.insert("", tk.END, values=(
                    file_path.name,
                    f"{size_mb:.1f} MB",
                    mtime.strftime("%Y-%m-%d %H:%M"),
                    reason
                ))
            except Exception:
                continue
                
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 控制按钮
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 清理进度
        progress_var = tk.StringVar(value="准备清理...")
        progress_label = ctk.CTkLabel(
            btn_frame,
            textvariable=progress_var,
            font=("Microsoft YaHei UI", 12)
        )
        progress_label.pack(side=tk.LEFT, padx=10)
        
        def update_progress(current, total, file_path, reason):
            progress_var.set(f"正在清理 ({current}/{total}): {file_path.name}")
            dialog.update()
        
        def do_cleanup():
            if not tk.messagebox.askyesno(
                "确认清理",
                f"确定要清理这 {len(cleanup_list)} 个文件吗？\n"
                "文件将被移动到回收站，可以手动恢复。"
            ):
                return
                
            # 禁用按钮
            clean_btn.configure(state="disabled")
            cancel_btn.configure(state="disabled")
            
            try:
                # 执行清理
                stats = cleanup_files(cleanup_list, update_progress)
                
                # 显示结果
                tk.messagebox.showinfo(
                    "清理完成",
                    f"清理完成:\n"
                    f"- 成功: {stats['success']}\n"
                    f"- 失败: {stats['failed']}\n"
                    f"- 跳过: {stats['skipped']}"
                )
            except Exception as e:
                tk.messagebox.showerror(
                    "清理出错",
                    f"清理过程中出错:\n{str(e)}"
                )
            finally:
                # 关闭对话框
                dialog.destroy()
                
                # 刷新统计
                self.update_stats()
        
        # 添加按钮
        clean_btn = ctk.CTkButton(
            btn_frame,
            text="开始清理",
            command=do_cleanup,
            width=100,
            **warning_style
        )
        clean_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            command=dialog.destroy,
            width=100
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def run(self):
        """运行GUI"""
        self.root.mainloop()

    def update_status(self, message: str):
        """更新状态信息"""
        self.status_var.set(message) 