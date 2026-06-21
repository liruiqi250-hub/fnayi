; 文件翻译工具箱 Installer
#define MyAppName "文件翻译工具箱"
#define MyAppDirName "FileTranslator"
#define MyAppVersion "1.1.1"
#define MyAppPublisher "Codex"
#define MyAppExeName "FileTranslator.exe"
#define ProjectRoot "D:\360MoveData\Users\ASUS\Desktop\deepseek-api-deepseek-api"

[Setup]
AppId={{B3F7A2D1-9E4C-4A5D-8F6E-2C1B3D4E5F6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppDirName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir={#ProjectRoot}\outputs
OutputBaseFilename={#MyAppDirName}_Setup_v{#MyAppVersion}
SetupIconFile={#ProjectRoot}\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "{#ProjectRoot}\dist\{#MyAppDirName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Run {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c del /q ""{app}\.env"" & del /q ""{app}\settings.json"" & del /q ""{app}\toolbox.log"""; Flags: runhidden

