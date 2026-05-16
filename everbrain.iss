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

[Code]
function SendMessageTimeout(hWnd: HWND; Msg: Cardinal; wParam: Longint; lParam: String; Flags: Cardinal; Timeout: Cardinal; out lpdwResult: Longint): Longint;
  external 'SendMessageTimeoutW@user32.dll stdcall';

const
  WM_SETTINGCHANGE = $001A;
  SMTO_ABORTIFHUNG = $0002;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Path: string;
  AppPath: string;
  P: Integer;
  Response: Longint;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path) then
    begin
      AppPath := ExpandConstant('{app}');
      
      // Try to remove with preceding semicolon
      P := Pos(';' + AppPath, Path);
      if P > 0 then
      begin
        Delete(Path, P, Length(';' + AppPath));
        RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path);
      end
      else
      begin
        // Try to remove with trailing semicolon
        P := Pos(AppPath + ';', Path);
        if P > 0 then
        begin
          Delete(Path, P, Length(AppPath + ';'));
          RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path);
        end
        else
        begin
          // Try to remove if it's the only entry
          if Pos(AppPath, Path) > 0 then
          begin
            StringChangeEx(Path, AppPath, '', True);
            RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path);
          end;
        end;
      end;
      
      // Notify system of environment change
      SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 5000, Response);
    end;
  end;
end;
