import os
from pathlib import Path

# 基础路径配置
DOWNLOADS_PATH = Path(os.path.expanduser("~/Downloads"))
SCRIPT_PATH = DOWNLOADS_PATH / "[SCRIPT] 自动整理"
LOGS_PATH = SCRIPT_PATH / "logs"
BACKUP_PATH = DOWNLOADS_PATH / "[BACKUP] 备份"

# 文件夹映射配置
FOLDER_MAPPING = {
    "[DOC] 文档": {
        "extensions": [
            # Office文档
            ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".rtf", ".odt", ".ods", ".odp",
            # PDF文档
            ".pdf",
            # 文本文件
            ".txt", ".md", ".log", ".csv",
            # 电子书
            ".epub", ".mobi", ".azw3",
            # 其他文档
            ".htm", ".html", ".xml", ".json"
        ],
        "auto_organize": True,
        "subfolders": {
            "Office": [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", 
                      ".rtf", ".odt", ".ods", ".odp"],
            "PDF": [".pdf"],
            "Text": [".txt", ".md", ".log", ".csv"],
            "Book": [".epub", ".mobi", ".azw3"],
            "Web": [".htm", ".html", ".xml", ".json"]
        }
    },
    "[MEDIA] 媒体": {
        "extensions": [
            # 视频文件
            ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
            # 音频文件
            ".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".ape",
            ".mid", ".midi",
            # 图片文件
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            ".raw", ".cr2", ".nef", ".arw", ".svg", ".ai", ".psd",
            # 字幕文件
            ".srt", ".ass", ".ssa"
        ],
        "auto_organize": True,
        "subfolders": {
            "Video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".ape",
                     ".mid", ".midi"],
            "Image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                     ".raw", ".cr2", ".nef", ".arw", ".svg", ".ai", ".psd"],
            "Subtitle": [".srt", ".ass", ".ssa"]
        }
    },
    "[APP] 应用": {
        "extensions": [
            # Windows应用
            ".exe", ".msi", ".appx", ".app",
            # 移动应用
            ".apk", ".ipa",
            # 插件扩展
            ".vsix", ".crx", ".xpi",
            # 系统文件
            ".dll", ".sys", ".drv", ".reg",
            # 系统镜像
            ".iso", ".img", ".vhd", ".vmdk"
        ],
        "auto_organize": True,
        "subfolders": {
            "Windows": [".exe", ".msi", ".appx", ".app"],
            "Mobile": [".apk", ".ipa"],
            "Plugin": [".vsix", ".crx", ".xpi"],
            "System": [".dll", ".sys", ".drv", ".reg", ".iso", ".img", ".vhd", ".vmdk"]
        }
    },
    "[ZIP] 压缩包": {
        "extensions": [
            ".zip", ".rar", ".7z", ".tar", ".gz", ".xz", ".bz2",
            ".tar.gz", ".tar.xz", ".tar.bz2", ".tgz", ".tbz"
        ],
        "auto_organize": True,
        "subfolders": {
            "ZIP": [".zip"],
            "RAR": [".rar"],
            "7Z": [".7z"],
            "TAR": [".tar", ".tar.gz", ".tar.xz", ".tar.bz2", ".tgz", ".tbz"],
            "Other": [".gz", ".xz", ".bz2"]
        }
    },
    "[DEV] 开发": {
        "extensions": [
            # 源代码
            ".py", ".java", ".cpp", ".c", ".h", ".cs", ".js", ".ts",
            ".php", ".asp", ".jsp", ".go", ".rb", ".pl", ".swift",
            # Web开发
            ".html", ".css", ".scss", ".less",
            # 配置文件
            ".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
            # 开发工具
            ".sln", ".csproj", ".vcxproj", ".gitignore"
        ],
        "auto_organize": True,
        "subfolders": {
            "Source": [".py", ".java", ".cpp", ".c", ".h", ".cs", ".js", ".ts",
                      ".php", ".asp", ".jsp", ".go", ".rb", ".pl", ".swift"],
            "Web": [".html", ".css", ".scss", ".less"],
            "Tool": [".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
                    ".sln", ".csproj", ".vcxproj", ".gitignore"]
        }
    }
}

# 受保护的文件夹
PROTECTED_FOLDERS = [
    "Clash for Windows",
    ".minecraft",
    "[SCRIPT] 自动整理",
    "[BACKUP] 备份",
    "Install-pkg",
    "themes"
]

# 用户配置
USER_CONFIG = {
    "auto_organize": True,  # 是否启用自动整理
    "organize_on_startup": True,  # 启动时是否整理现有文件
    "show_notification": True,  # 是否显示通知
    "minimize_on_startup": True,  # 启动时是否最小化到托盘
    "confirm_before_move": False,  # 移动文件前是否确认
}

# 清理配置
CLEANUP_CONFIG = {
    "enabled_folders": [
        "[ZIP] 压缩包",  # 默认清理压缩包
        "[APP] 应用"     # 和应用安装包
    ],
    "rules": {
        "age": {
            "enabled": True,
            "days": 30  # 超过30天的文件
        },
        "size": {
            "enabled": True,
            "max_size_mb": 1024  # 超过1GB的文件
        },
        "type": {
            "enabled": True,
            "extensions": [
                # 临时文件
                ".tmp", ".temp", ".bak", ".old",
                # 安装包
                ".exe", ".msi", ".appx",
                # 压缩包
                ".zip", ".rar", ".7z"
            ]
        }
    },
    "safe_mode": True,  # 安全模式：移动到回收站而不是直接删除
    "require_confirmation": True,  # 是否需要确认
    "backup_before_cleanup": True,  # 清理前是否备份
    "cleanup_empty_folders": True,  # 是否清理空文件夹
    "exclude_patterns": [  # 排除的文件名模式
        "*重要*", "*保留*", "*keep*", "*important*"
    ]
}

# 日志配置
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_ENCODING = "utf-8"

# 文件处理配置
FILE_BATCH_SIZE = 50  # 每批处理的文件数
MIN_FREE_SPACE_GB = 10  # 最小所需硬盘空间（GB）
FILE_AGE_THRESHOLD = 7  # 文件年龄阈值（天）

# GUI配置
GUI_TITLE = "ClearBOOM"
GUI_GEOMETRY = "800x600"
GUI_REFRESH_INTERVAL = 1000  # 毫秒

# 状态码
class Status:
    SUCCESS = 0
    FILE_IN_USE = 1
    INSUFFICIENT_SPACE = 2
    BACKUP_FAILED = 3
    MOVE_FAILED = 4
    INVALID_PATH = 5 