$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = "python"
$version = "1.0.0"
$appName = "BatchFileToolbox"

Write-Host "===== Batch File Toolbox 构建打包脚本 v$version =====" -ForegroundColor Cyan

# Step 1: Clean old build artifacts
Write-Host "`n[1/4] 清理旧构建..." -ForegroundColor Yellow
if (Test-Path "$projectRoot\build") { Remove-Item -Recurse -Force "$projectRoot\build" }
if (Test-Path "$projectRoot\dist\$appName") { Remove-Item -Recurse -Force "$projectRoot\dist\$appName" }
if (Test-Path "$projectRoot\$appName.spec") { Remove-Item -Force "$projectRoot\$appName.spec" }
Write-Host "      清理完成" -ForegroundColor Green

# Step 2: PyInstaller build
Write-Host "`n[2/4] PyInstaller 构建中（请耐心等待，约 2-5 分钟）..." -ForegroundColor Yellow
& $python -m PyInstaller `
    --name "$appName" `
    --noconfirm `
    --windowed `
    --onedir `
    --paths "$projectRoot\src" `
    --hidden-import "openpyxl" `
    --hidden-import "openpyxl.cell._writer" `
    --hidden-import "docx" `
    --hidden-import "pypdf" `
    --hidden-import "olefile" `
    --hidden-import "deep_translator" `
    --hidden-import "dotenv" `
    --hidden-import "openai" `
    --hidden-import "httpx" `
    --hidden-import "httpcore" `
    --hidden-import "PySide6" `
    --hidden-import "PySide6.QtCore" `
    --hidden-import "PySide6.QtWidgets" `
    --hidden-import "PySide6.QtGui" `
    --collect-all "PySide6" `
    "$projectRoot\src\file_toolbox\main.py"

if ($LASTEXITCODE -ne 0) { throw "PyInstaller 构建失败" }
Write-Host "      PyInstaller 构建完成" -ForegroundColor Green

# Step 3: Copy additional files
Write-Host "`n[3/4] 复制额外文件..." -ForegroundColor Yellow
$distDir = "$projectRoot\dist\$appName"
Copy-Item "$projectRoot\.env.example" "$distDir\" -Force
Write-Host "      已复制 .env.example" -ForegroundColor Green

# Step 4: Inno Setup installer
Write-Host "`n[4/4] 生成安装包..." -ForegroundColor Yellow
$iscc = "C:\Users\ASUS\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
$issFile = "$projectRoot\installer.iss"

$issContent = @"
; Batch File Toolbox Installer
#define MyAppName "Batch File Toolbox"
#define MyAppVersion "$version"
#define MyAppPublisher "Codex"
#define MyAppExeName "$appName.exe"
#define MyAppAssocName "Batch File Toolbox"

[Setup]
AppId={{B3F7A2D1-9E4C-4A5D-8F6E-2C1B3D4E5F6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir="$projectRoot\outputs"
OutputBaseFilename={#MyAppName}_Setup_v{#MyAppVersion}
SetupIconFile="$projectRoot\app.ico"
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："

[Files]
Source: "$projectRoot\dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "运行 {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c del /q ""{app}\.env"" & del /q ""{app}\settings.json"" & del /q ""{app}\toolbox.log"""; Flags: runhidden
"@

$issContent | Set-Content -Encoding UTF8 -LiteralPath $issFile

& $iscc $issFile
if ($LASTEXITCODE -ne 0) { throw "Inno Setup 打包失败" }

Write-Host "`n===== 构建完成！=====" -ForegroundColor Cyan
Write-Host "安装包位于：" -ForegroundColor Cyan
Get-ChildItem "$projectRoot\outputs\*_Setup_*.exe" | Select-Object Name, Length | Format-Table -AutoSize
