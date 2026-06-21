# 批量文件工具箱
这是一个 Windows 桌面工具，用来批量处理 Word、Excel、PDF 和文件夹资料。
第一版功能：

- Word 翻译成英文
- Excel 翻译/整理（支持 `.xlsx`、`.xlsm`）
- PDF 提取文字并翻译成英文 Word（文字型 PDF）
- 文件批量重命名和整理

使用前需要在 `.env` 文件中配置：

```env
DEEPSEEK_API_KEY=你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

## 开发运行
```powershell
python -m pip install -e ".[dev]"
python -m file_toolbox.main
```

## 打包 EXE
```powershell
.\scripts\build_exe.ps1
```
打包完成后，EXE 在：
```text
dist\BatchFileToolbox\BatchFileToolbox.exe
```
