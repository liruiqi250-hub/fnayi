# 文件翻译工具箱

> 一款 Windows 桌面工具，批量翻译 Word/Excel/PDF 文件、粘贴文字翻译、文件自动整理。

---

## ✨ 功能

### 📄 文件翻译
- **Word 翻译** — 批量翻译 .docx 文件，保留原格式
- **Excel 翻译/整理** — 批量翻译 .xlsx / .xlsm，相同文本自动缓存加速
- **PDF 转文本翻译** — 提取文字型 PDF 内容，翻译后输出 Word 文档

### 📝 文本翻译
- 粘贴文字直接翻译，类似谷歌翻译
- 支持所有翻译引擎

### 📁 文件整理
- 按文件类型自动分类（Word、Excel、PDF、图片、视频、代码等）
- 支持替换空格为下划线

---

## 🔤 支持的翻译引擎

| 引擎 | 是否需要配置 | 说明 |
|------|-------------|------|
| **Google 翻译** | 无需 Key，免费 | 需挂 VPN |
| **MyMemory 翻译** | 无需 Key，免费 | 无需网络特殊设置 |
| **Pons 翻译** | 无需 Key，免费 | 适合欧洲语言 |
| **自定义大模型** | 需 API Key | 支持任何 OpenAI 兼容接口（DeepSeek、通义千问、OpenAI 等） |

> 选「自定义大模型」时，需在 **设置 → API 设置** 中配置 API Key 和接口地址。

---

## 🎨 主题

- **浅色模式** — 默认
- **深色模式** — 护眼
- **自动模式** — 跟随 Windows 系统设置

点击标题栏的 ☾ / ☀ 按钮切换。

---

## 🚀 下载安装

从 GitHub Releases 下载最新安装包：

➡ https://github.com/liruiqi250-hub/fnayi/releases

安装后运行 **文件翻译工具箱** 即可使用。

---

## 🔄 检查更新

软件内置了更新检测功能：

**设置 → 其他 → 检查更新**

会自动检测 GitHub 上是否有新版本。

---

## 🛠 开发运行

`powershell
# 安装依赖
pip install -e ".[dev]"

# 运行
python -m file_toolbox.main
`

### 打包 EXE

`powershell
.\scriptsuild_exe.ps1
`

打包完成后 EXE 在：
`
dist\FileTranslator\FileTranslator.exe
`

---

## 🐞 反馈问题

打开 https://github.com/liruiqi250-hub/fnayi/issues 提交 Issue。
