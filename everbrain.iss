; EverBrain Inno Setup Script
#define MyAppName "EverBrain"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "EverBrain Team"
#define MyAppURL "https://everbrain.ai"
#define MyAppExeName "eb.exe"

[Setup]
AppId={{D3E8C1B2-7F6A-4A5D-B2E8-C1B27F6A4A5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=EverBrainInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Registry]
Root: HKCU; Subkey: "Environment"; \
    ValueType: expandsz; ValueName: "Path"; ValueData: "{reg:HKCU\Environment,Path|};{app}"; \
    Flags: preservestringtype

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
