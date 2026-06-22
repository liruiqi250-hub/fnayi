; 文件翻译工具箱 Installer
#define MyAppName "文件翻译工具箱"
#define MyAppDirName "FileTranslator"
#define MyAppVersion "1.3.5"
#define MyAppPublisher "Codex"
#define MyAppExeName "FileTranslator.exe"
#define ProjectRoot "D:\360MoveData\Users\ASUS\Desktop\文件翻译工具箱 v1.3.2"

[Setup]
AppId={{B3F7A2D1-9E4C-4A5D-8F6E-2C1B3D4E5F6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppDirName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=D:\360MoveData\Users\ASUS\Desktop\文件翻译工具箱 v1.3.2\outputs
OutputBaseFilename={#MyAppDirName}_Setup_v{#MyAppVersion}
SetupIconFile=D:\360MoveData\Users\ASUS\Desktop\文件翻译工具箱 v1.3.2\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[CustomMessages]
NameAndVersion=%1 版本 %2
AdditionalIcons=附加图标：
CreateDesktopIcon=创建桌面(&D)
CreateQuickLaunchIcon=创建快速启动栏图标(&Q)
ProgramOnTheWeb=%1 官方网站
UninstallProgram=卸载 %1
LaunchProgram=运行 %1
AssocFileType=&关联 %1 文件类型
AssocFileTypeExt=关联 %1 文件类型

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："

[Files]
Source: "D:\360MoveData\Users\ASUS\Desktop\文件翻译工具箱 v1.3.2\dist\FileTranslator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "运行 {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c del /q ""{app}\.env"" & del /q ""{app}\settings.json"" & del /q ""{app}\toolbox.log"""; Flags: runhidden

