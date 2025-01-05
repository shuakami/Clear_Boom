# ClearBOOM ( >_< )

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/ClearBOOM)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-red.svg)](https://www.microsoft.com/windows)

**ClearBOOM** 是一个专为 Windows 用户设计的下载文件夹自动整理工具。通过智能规则，ClearBOOM 能够实时监控下载文件夹的变化，将不同类型的文件分类存放到对应的文件夹中，并支持灵活的清理功能。让你的下载文件夹再也不用担心杂乱无章！

---

## ✨ 功能特点

- **实时文件监控**：自动监控下载文件夹，发现新文件后立即整理。
- **智能分类规则**：支持按扩展名自动分类，分类规则灵活可配。
- **动态文件夹生成**：程序会根据分类规则，自动创建对应的文件夹。
- **安全清理功能**：支持基于文件年龄、大小、类型等规则清理，且文件默认移动到回收站，确保安全。
- **详细日志记录**：完整记录整理和清理操作，方便排查问题。
- **资源占用低**：后台运行轻量流畅，支持系统托盘显示。
- **界面直观**：提供简洁易用的 GUI 操作界面。
- **开机自启动**：支持设置程序开机启动。

---

## 🔧 系统要求

- **操作系统**：Windows 10 或 Windows 11
- **Python 版本**：Python 3.10 或更高版本
- **管理员权限**：设置开机自启动或特定系统操作时需要管理员权限。

---

## 📦 安装方法

1. **准备 Python 环境**  
   确保已安装 Python 3.10 或更高版本，并正确配置环境变量。

2. **下载项目代码**  
   克隆或直接下载 ClearBOOM 的源码。

3. **安装依赖**  
   在项目根目录运行以下命令安装必要的依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. **运行程序**  
   使用以下命令启动程序：
   ```bash
   pythonw file_organizer.py
   ```

---

## 🚀 快速上手

### 自动整理功能

1. 启动程序后，ClearBOOM 会自动监控下载文件夹，按以下步骤整理文件：
   - **检查文件夹结构**：根据配置规则，自动创建分类文件夹。
   - **整理现有文件**：扫描下载文件夹内的文件，移动到对应分类文件夹。
   - **实时监控**：对下载文件夹中的新文件，实时执行分类操作。

2. 系统托盘功能：
   - **双击托盘图标**：打开主界面。
   - **右键托盘菜单**：可以访问更多操作选项，例如手动整理、查看日志等。

---

## 📁 文件分类规则

ClearBOOM 使用灵活的扩展名映射规则来实现文件分类。以下是默认的分类规则和文件夹结构：

### 默认分类映射

- **[DOC] 文档**  
  包括：`pdf`、`docx`、`xlsx`、`txt` 等。
  - 子分类：`Office`（办公文档）、`PDF`、`Text`（文本文件）、`Book`（电子书）、`Web`（网页相关）。

- **[MEDIA] 媒体**  
  包括：图片（`jpg`、`png`）、视频（`mp4`、`mkv`）、音频（`mp3`、`wav`）等。
  - 子分类：`Video`（视频文件）、`Audio`（音频文件）、`Image`（图片文件）、`Subtitle`（字幕文件）。

- **[APP] 应用**  
  包括：`exe`、`apk`、`iso` 等。
  - 子分类：`Windows`（Windows 程序）、`Mobile`（移动应用）、`Plugin`（插件扩展）、`System`（系统文件）。

- **[ZIP] 压缩包**  
  包括：`zip`、`rar`、`7z`、`tar.gz` 等。
  - 子分类：`ZIP`、`RAR`、`TAR`、`Other`（其他类型的压缩包）。

- **[DEV] 开发**  
  包括：源代码（`py`、`java`）、配置文件（`json`、`yaml`）等。
  - 子分类：`Source`（源码文件）、`Web`（前端开发文件）、`Tool`（工具配置）。

### 自定义规则

用户可以通过编辑 `config.py` 文件自定义分类规则，包括：
- 修改分类文件夹名称。
- 自定义扩展名映射。
- 配置子文件夹规则。

---

## 🧹 文件清理功能

ClearBOOM 提供丰富的文件清理功能，支持以下规则：

- **文件年龄清理**：清理超过设定天数（默认 30 天）的旧文件。
- **文件大小限制**：清理超过指定大小的文件（默认 1GB）。
- **按文件类型清理**：支持清理特定扩展名的文件（如 `.tmp`、`.bak`）。
- **排除规则**：设置不清理的文件名模式（如文件名包含“重要”、“保留”）。
- **安全模式**：默认清理的文件会移动到回收站，而非直接删除。

### 配置清理规则

清理功能的详细规则可通过 `config.py` 文件配置：
- 指定清理的文件夹。
- 启用或禁用某些清理规则。
- 设置文件清理的优先级和排除规则。

---

## 🛡️ 安全保护功能

为确保操作安全，ClearBOOM 提供以下保护机制：

1. **受保护文件夹**  
   默认不会整理以下文件夹：
   - `Clash for Windows`  
   - `.minecraft`  
   - `[SCRIPT] 自动整理`  
   - `[BACKUP] 备份`

2. **文件占用检测**  
   跳过正在使用的文件，避免整理失败或误删。

3. **路径安全验证**  
   确保目标路径合法，避免出现文件丢失。

4. **磁盘空间检查**  
   保证剩余磁盘空间不少于 10GB。

5. **智能跳过临时文件**  
   自动忽略 `.tmp`、`.crdownload` 等临时文件。

---

## 📂 项目结构

```plaintext
ClearBOOM/
├── file_organizer.py  # 主程序
├── config.py          # 配置文件
├── gui.py             # 图形界面
├── utils.py           # 工具函数
├── logs/              # 日志文件夹
├── requirements.txt   # 依赖文件
└── README.md          # 说明文档
```

---

## 📝 日志系统

ClearBOOM 会生成详细的操作日志，存储在 `logs/` 文件夹下：
- **整理日志**：记录文件的移动、分类等操作。
- **清理日志**：记录清理规则执行情况及被删除的文件。
- **错误日志**：记录程序运行中出现的异常。

日志支持自动轮转，可根据需要保留或清理旧日志。

---

## ⚠️ 注意事项

1. **首次运行**：需要管理员权限以设置开机自启动。
2. **安全清理模式**：默认启用安全模式，文件会移动到回收站。
3. **配置文件修改**：自定义分类或清理规则需编辑 `config.py` 文件。
4. **文件名冲突**：当移动的文件发生冲突时，程序会自动重命名以避免覆盖。

