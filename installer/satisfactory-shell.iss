; Inno Setup 6 — compile after: poetry run build-exe
; Optional: powershell -File fetch-steamcmd.ps1  (vendors redist\steamcmd.zip)

#define MyAppName "Satisfactory Shell"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Satisfactory Shell"
#define MyAppExeName "satisfactory-shell.exe"
#define SteamAppId "1690800"

[Setup]
AppId={{8F2A1C6E-4D7B-4A91-B3E8-1C9F0D5A7E24}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SatisfactoryShell
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=SatisfactoryShell-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
UsedUserAreasWarning=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon"; Description: "Start the WebUI when I sign in to Windows"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\steamcmd"; Permissions: users-modify; Check: IsInstallSteamCmd
Name: "{app}\server"; Permissions: users-modify; Check: IsInstallServer
Name: "{userappdata}\SatisfactoryShell"; Permissions: users-modify
Name: "{userappdata}\SatisfactoryShell\data"; Permissions: users-modify

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "redist\steamcmd.zip"; DestDir: "{tmp}"; Flags: deleteafterinstall ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--bootstrap"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--bootstrap"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--bootstrap"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--bootstrap"; Description: "Start {#MyAppName} (starts the dedicated server and claims it if needed)"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\steamcmd"
Type: filesandordirs; Name: "{app}\server"

[Code]
const
  SteamCmdUrl = 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip';
  MinFreeBytes = 17179869184;
  SizeApp = '~20 MB';
  SizeSteamCmd = '~3 MB';
  SizeServer = '~15 GB';

var
  SourcePage: TInputOptionWizardPage;
  SizePage: TWizardPage;
  SizeMemo: TNewMemo;
  ExistingServerPage: TInputDirWizardPage;
  ExistingSteamPage: TInputFileWizardPage;
  SettingsPage: TWizardPage;
  ServerNameEdit: TNewEdit;
  AdminPassEdit: TPasswordEdit;
  ClientPassEdit: TPasswordEdit;
  GamePortEdit: TNewEdit;
  RelPortEdit: TNewEdit;
  WebPortEdit: TNewEdit;
  LanCheck: TNewCheckBox;

function IsInstallSteamCmd: Boolean;
begin
  Result := (SourcePage <> nil) and SourcePage.Values[0];
end;

function IsInstallServer: Boolean;
begin
  Result := (SourcePage <> nil) and SourcePage.Values[1];
end;

function InstallRoot: String;
begin
  { Application directory from the wizard edit; not the app constant (invalid before install). }
  Result := RemoveBackslash(WizardDirValue);
end;

function JsonEscape(const S: String): String;
var
  I: Integer;
  C: Char;
begin
  Result := '';
  for I := 1 to Length(S) do
  begin
    C := S[I];
    case C of
      '\': Result := Result + '\\';
      '"': Result := Result + '\"';
    else
      if C = Chr(8) then Result := Result + '\b'
      else if C = Chr(9) then Result := Result + '\t'
      else if C = Chr(10) then Result := Result + '\n'
      else if C = Chr(13) then Result := Result + '\r'
      else Result := Result + C;
    end;
  end;
end;

function WriteTextFile(const FileName, Content: String): Boolean;
var
  A: AnsiString;
begin
  ForceDirectories(ExtractFilePath(FileName));
  A := Utf8Encode(Content);
  Result := SaveStringToFile(FileName, A, False);
end;

function ServerRootPath: String;
begin
  if IsInstallServer then
    Result := InstallRoot + '\server'
  else
    Result := ExistingServerPage.Values[0];
end;

function SteamCmdPath: String;
begin
  if IsInstallSteamCmd then
    Result := InstallRoot + '\steamcmd\steamcmd.exe'
  else
    Result := ExistingSteamPage.Values[0];
end;

function WebHost: String;
begin
  if LanCheck.Checked then
    Result := '0.0.0.0'
  else
    Result := '127.0.0.1';
end;

function SizeNoticeText: String;
var
  AppDir, NL: String;
begin
  NL := #13#10;
  AppDir := InstallRoot;
  Result :=
    'Install folder' + NL +
    '  ' + AppDir + NL + NL +
    'Satisfactory Shell' + NL +
    '  Always copied, ' + SizeApp + NL + NL;

  Result := Result + 'SteamCMD' + NL;
  if IsInstallSteamCmd then
    Result := Result +
      '  Will be installed to:' + NL +
      '    ' + AppDir + '\steamcmd' + NL +
      '  Download: ' + SizeSteamCmd + ' zip. SteamCMD may self-update once.' + NL + NL
  else
    Result := Result +
      '  Not installing.' + NL +
      '  Next: choose an existing steamcmd.exe.' + NL + NL;

  Result := Result + 'Dedicated server' + NL;
  if IsInstallServer then
    Result := Result +
      '  Will be downloaded to:' + NL +
      '    ' + AppDir + '\server' + NL +
      '  Download: ' + SizeServer + ' (Satisfactory app 1690800).' + NL +
      '  Need about 16 GB free on this drive.' + NL +
      '  Close the Steam client if it might lock this folder (error 0x606).' + NL +
      '  A new server is claimed on first start (admin password on a later page).' + NL
  else
    Result := Result +
      '  Not installing.' + NL +
      '  Next: choose a folder that contains FactoryServer.exe.' + NL;

  if (not IsInstallSteamCmd) and (not IsInstallServer) then
    Result := Result + NL +
      'No extra download. Passwords you enter later should already be set on that server.' + NL +
      'The client password is stored so Home can query stats. The admin password is not stored.';
end;

procedure RefreshSizeMemo;
begin
  if SizeMemo <> nil then
    SizeMemo.Lines.Text := SizeNoticeText;
end;

procedure SizePageActivate(Sender: TWizardPage);
begin
  RefreshSizeMemo;
end;

procedure InitializeWizard;
var
  TopY: Integer;
begin
  SourcePage := CreateInputOptionPage(wpSelectDir,
    'What to install', 'Install SteamCMD and/or the dedicated server, or point at copies you already have.',
    'Unchecked items need a path on the following page(s). You can install one, both, or neither.',
    False, False);
  SourcePage.Add('Install SteamCMD');
  SourcePage.Add('Install the Satisfactory Dedicated Server');
  SourcePage.Values[0] := True;
  SourcePage.Values[1] := True;

  SizePage := CreateCustomPage(SourcePage.ID,
    'Download size', 'Approximate disk use for the items you chose to install.');
  SizePage.OnActivate := @SizePageActivate;
  SizeMemo := TNewMemo.Create(SizePage);
  SizeMemo.Parent := SizePage.Surface;
  SizeMemo.ReadOnly := True;
  SizeMemo.ScrollBars := ssVertical;
  SizeMemo.Left := 0;
  SizeMemo.Top := 0;
  SizeMemo.Width := SizePage.SurfaceWidth;
  SizeMemo.Height := SizePage.SurfaceHeight;
  RefreshSizeMemo;

  ExistingServerPage := CreateInputDirPage(SizePage.ID,
    'Existing dedicated server', 'Folder that contains FactoryServer.exe',
    'This is usually a Steam library folder or a previous SteamCMD install.',
    False, '');
  ExistingServerPage.Add('Dedicated server folder:');

  ExistingSteamPage := CreateInputFilePage(ExistingServerPage.ID,
    'Existing SteamCMD', 'steamcmd.exe used for updates',
    'The Updates page in the WebUI will call this executable.');
  ExistingSteamPage.Add('steamcmd.exe:', 'SteamCMD (steamcmd.exe)|steamcmd.exe|All files|*.*', '.exe');

  SettingsPage := CreateCustomPage(ExistingSteamPage.ID,
    'Server and WebUI', 'Ports, passwords, and whether the WebUI listens on the LAN.');

  TopY := 0;
  with TNewStaticText.Create(SettingsPage) do
  begin
    Parent := SettingsPage.Surface;
    Caption := 'Server name (used when claiming a new download):';
    Top := TopY;
    Width := SettingsPage.SurfaceWidth;
  end;
  TopY := TopY + ScaleY(16);
  ServerNameEdit := TNewEdit.Create(SettingsPage);
  ServerNameEdit.Parent := SettingsPage.Surface;
  ServerNameEdit.Top := TopY;
  ServerNameEdit.Width := SettingsPage.SurfaceWidth;
  ServerNameEdit.Text := 'Satisfactory Server';
  TopY := TopY + ScaleY(28);

  with TNewStaticText.Create(SettingsPage) do
  begin
    Parent := SettingsPage.Surface;
    Caption := 'Admin password (required to claim a new server; not stored in config.json):';
    Top := TopY;
    Width := SettingsPage.SurfaceWidth;
  end;
  TopY := TopY + ScaleY(16);
  AdminPassEdit := TPasswordEdit.Create(SettingsPage);
  AdminPassEdit.Parent := SettingsPage.Surface;
  AdminPassEdit.Top := TopY;
  AdminPassEdit.Width := SettingsPage.SurfaceWidth;
  TopY := TopY + ScaleY(28);

  with TNewStaticText.Create(SettingsPage) do
  begin
    Parent := SettingsPage.Surface;
    Caption := 'Client password (optional; stored so Home can call QueryServerState):';
    Top := TopY;
    Width := SettingsPage.SurfaceWidth;
  end;
  TopY := TopY + ScaleY(16);
  ClientPassEdit := TPasswordEdit.Create(SettingsPage);
  ClientPassEdit.Parent := SettingsPage.Surface;
  ClientPassEdit.Top := TopY;
  ClientPassEdit.Width := SettingsPage.SurfaceWidth;
  TopY := TopY + ScaleY(28);

  with TNewStaticText.Create(SettingsPage) do
  begin
    Parent := SettingsPage.Surface;
    Caption := 'Game / HTTPS API port:';
    Left := 0;
    Top := TopY;
  end;
  GamePortEdit := TNewEdit.Create(SettingsPage);
  GamePortEdit.Parent := SettingsPage.Surface;
  GamePortEdit.Left := ScaleX(180);
  GamePortEdit.Top := TopY - ScaleY(2);
  GamePortEdit.Width := ScaleX(80);
  GamePortEdit.Text := '7777';
  TopY := TopY + ScaleY(26);

  with TNewStaticText.Create(SettingsPage) do
  begin
    Parent := SettingsPage.Surface;
    Caption := 'Reliable messaging port:';
    Left := 0;
    Top := TopY;
  end;
  RelPortEdit := TNewEdit.Create(SettingsPage);
  RelPortEdit.Parent := SettingsPage.Surface;
  RelPortEdit.Left := ScaleX(180);
  RelPortEdit.Top := TopY - ScaleY(2);
  RelPortEdit.Width := ScaleX(80);
  RelPortEdit.Text := '8888';
  TopY := TopY + ScaleY(26);

  with TNewStaticText.Create(SettingsPage) do
  begin
    Parent := SettingsPage.Surface;
    Caption := 'WebUI port:';
    Left := 0;
    Top := TopY;
  end;
  WebPortEdit := TNewEdit.Create(SettingsPage);
  WebPortEdit.Parent := SettingsPage.Surface;
  WebPortEdit.Left := ScaleX(180);
  WebPortEdit.Top := TopY - ScaleY(2);
  WebPortEdit.Width := ScaleX(80);
  WebPortEdit.Text := '8080';
  TopY := TopY + ScaleY(28);

  LanCheck := TNewCheckBox.Create(SettingsPage);
  LanCheck.Parent := SettingsPage.Surface;
  LanCheck.Top := TopY;
  LanCheck.Width := SettingsPage.SurfaceWidth;
  LanCheck.Caption := 'WebUI reachable on the LAN (bind 0.0.0.0; opens TCP firewall for the WebUI port only)';
  LanCheck.Checked := False;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if (ExistingServerPage <> nil) and (PageID = ExistingServerPage.ID) then
    Result := IsInstallServer;
  if (ExistingSteamPage <> nil) and (PageID = ExistingSteamPage.ID) then
    Result := IsInstallSteamCmd;
end;

function ParsePort(const S: String; var Port: Integer): Boolean;
begin
  Port := StrToIntDef(Trim(S), -1);
  Result := (Port >= 1) and (Port <= 65535);
end;

function DriveHasSpace(const Path: String; const Need: Int64): Boolean;
var
  FreeB, TotalB: Int64;
  Drive: String;
begin
  Result := True;
  Drive := ExtractFileDrive(Path);
  if Drive = '' then
    Exit;
  if Length(Drive) = 2 then
    Drive := Drive + '\';
  if GetSpaceOnDisk64(Drive, FreeB, TotalB) then
    Result := FreeB >= Need;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ServerDir, SteamExe: String;
  GamePort, RelPort, WebPort: Integer;
begin
  Result := True;
  if (SizePage <> nil) and (CurPageID = SizePage.ID) then
  begin
    RefreshSizeMemo;
    if IsInstallServer then
    begin
      if not DriveHasSpace(InstallRoot, MinFreeBytes) then
      begin
        MsgBox('The install drive does not have about 16 GB free (needed to download the dedicated server). Free space or pick another folder.', mbError, MB_OK);
        Result := False;
      end;
    end;
  end;
  if (ExistingServerPage <> nil) and (CurPageID = ExistingServerPage.ID) and (not IsInstallServer) then
  begin
    ServerDir := AddBackslash(ExistingServerPage.Values[0]);
    if not FileExists(ServerDir + 'FactoryServer.exe') then
    begin
      MsgBox('FactoryServer.exe was not found in that folder.', mbError, MB_OK);
      Result := False;
    end;
  end;
  if (ExistingSteamPage <> nil) and (CurPageID = ExistingSteamPage.ID) and (not IsInstallSteamCmd) then
  begin
    SteamExe := ExistingSteamPage.Values[0];
    if (SteamExe = '') or (not FileExists(SteamExe)) then
    begin
      MsgBox('steamcmd.exe was not found.', mbError, MB_OK);
      Result := False;
    end;
  end;
  if (SettingsPage <> nil) and (CurPageID = SettingsPage.ID) then
  begin
    if not ParsePort(GamePortEdit.Text, GamePort) then
    begin
      MsgBox('Game port must be 1-65535.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParsePort(RelPortEdit.Text, RelPort) then
    begin
      MsgBox('Reliable port must be 1-65535.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParsePort(WebPortEdit.Text, WebPort) then
    begin
      MsgBox('WebUI port must be 1-65535.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if GamePort = RelPort then
    begin
      MsgBox('Game port and reliable port must differ.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if IsInstallServer then
    begin
      if Trim(ServerNameEdit.Text) = '' then
      begin
        MsgBox('Enter a server name for ClaimServer.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
      if AdminPassEdit.Text = '' then
      begin
        MsgBox('An admin password is required so Satisfactory Shell can claim a newly downloaded server.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
    end;
    if (AdminPassEdit.Text <> '') and (ClientPassEdit.Text <> '') and (AdminPassEdit.Text = ClientPassEdit.Text) then
    begin
      MsgBox('Admin and client passwords cannot be the same (Satisfactory rejects password_in_use).', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function ConfigJson: String;
begin
  Result :=
    '{' + #13#10 +
    '  "paths": {' + #13#10 +
    '    "server_root": "' + JsonEscape(ServerRootPath) + '",' + #13#10 +
    '    "steamcmd": "' + JsonEscape(SteamCmdPath) + '",' + #13#10 +
    '    "appmanifest": ""' + #13#10 +
    '  },' + #13#10 +
    '  "game": {' + #13#10 +
    '    "host": "127.0.0.1",' + #13#10 +
    '    "port": ' + Trim(GamePortEdit.Text) + ',' + #13#10 +
    '    "reliable_port": ' + Trim(RelPortEdit.Text) + ',' + #13#10 +
    '    "extra_args": ["-log", "-unattended", "-ini:Engine:[SystemSettings]:FG.DedicatedServer.AllowInsecureLocalAccess=1"],' + #13#10 +
    '    "client_password": "' + JsonEscape(ClientPassEdit.Text) + '"' + #13#10 +
    '  },' + #13#10 +
    '  "webui": {' + #13#10 +
    '    "host": "' + WebHost + '",' + #13#10 +
    '    "port": ' + Trim(WebPortEdit.Text) + ',' + #13#10 +
    '    "secret_key": ""' + #13#10 +
    '  },' + #13#10 +
    '  "process": {' + #13#10 +
    '    "auto_start": true,' + #13#10 +
    '    "auto_restart": true,' + #13#10 +
    '    "restart_delay_seconds": 10,' + #13#10 +
    '    "shutdown_timeout_seconds": 30' + #13#10 +
    '  },' + #13#10 +
    '  "steam": { "app_id": {#SteamAppId}, "beta": "", "validate": true },' + #13#10 +
    '  "metrics": { "interval_seconds": 5, "history_minutes": 60 }' + #13#10 +
    '}' + #13#10;
end;

function BootstrapJson: String;
begin
  Result :=
    '{' + #13#10 +
    '  "claim": true,' + #13#10 +
    '  "server_name": "' + JsonEscape(Trim(ServerNameEdit.Text)) + '",' + #13#10 +
    '  "admin_password": "' + JsonEscape(AdminPassEdit.Text) + '",' + #13#10 +
    '  "client_password": "' + JsonEscape(ClientPassEdit.Text) + '"' + #13#10 +
    '}' + #13#10;
end;

function EnsureSteamCmdZip: String;
var
  Zip: String;
begin
  Zip := ExpandConstant('{tmp}\steamcmd.zip');
  Result := Zip;
  if FileExists(Zip) then
    Exit;
  WizardForm.StatusLabel.Caption := 'Downloading SteamCMD (~3 MB)…';
  try
    DownloadTemporaryFile(SteamCmdUrl, 'steamcmd.zip', '', nil);
  except
    RaiseException('Could not download SteamCMD from ' + SteamCmdUrl + ': ' + GetExceptionMessage);
  end;
  if not FileExists(Zip) then
    RaiseException('steamcmd.zip is missing after download.');
end;

function ExtractZip(const Zip, Dest: String): Boolean;
var
  Code: Integer;
  Cmd: String;
begin
  ForceDirectories(Dest);
  Cmd := '-NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath ''' + Zip + ''' -DestinationPath ''' + Dest + '''"';
  Result := Exec('powershell.exe', Cmd, '', SW_HIDE, ewWaitUntilTerminated, Code) and (Code = 0);
end;

procedure InstallSteamCmdFiles;
var
  Zip, SteamDir: String;
begin
  WizardForm.StatusLabel.Caption := 'Installing SteamCMD…';
  WizardForm.ProgressGauge.Style := npbstMarquee;
  Zip := EnsureSteamCmdZip;
  SteamDir := InstallRoot + '\steamcmd';
  ForceDirectories(SteamDir);
  if not ExtractZip(Zip, SteamDir) then
    RaiseException('Failed to extract steamcmd.zip.');
  if not FileExists(SteamDir + '\steamcmd.exe') then
    RaiseException('steamcmd.exe missing after extract.');
  WizardForm.ProgressGauge.Style := npbstNormal;
end;

procedure DownloadDedicatedServer;
var
  SteamExe, SteamDir, ServerDir, Args: String;
  Code: Integer;
begin
  SteamExe := SteamCmdPath;
  SteamDir := ExtractFilePath(SteamExe);
  ServerDir := InstallRoot + '\server';
  if not FileExists(SteamExe) then
    RaiseException('steamcmd.exe not found at ' + SteamExe + '. Install SteamCMD or pick an existing copy.');
  ForceDirectories(ServerDir);
  WizardForm.ProgressGauge.Style := npbstMarquee;
  WizardForm.StatusLabel.Caption := 'Downloading dedicated server (~15 GB). First SteamCMD run may also update itself. This can take a long time…';
  Args := '+force_install_dir "' + ServerDir + '" +login anonymous +app_update {#SteamAppId} validate +quit';
  if not Exec(SteamExe, Args, SteamDir, SW_SHOW, ewWaitUntilTerminated, Code) then
    RaiseException('Could not start steamcmd.exe.');
  if Code <> 0 then
    Log('steamcmd exited with ' + IntToStr(Code) + ' (0x606 usually means Steam has the folder locked).');
  if not FileExists(ServerDir + '\FactoryServer.exe') then
    RaiseException('FactoryServer.exe was not found after SteamCMD. If you saw state 0x606, close Steam and run setup again.');
  WizardForm.ProgressGauge.Style := npbstNormal;
end;

procedure AddWebUiFirewall;
var
  Code: Integer;
  Port, Name: String;
begin
  Port := Trim(WebPortEdit.Text);
  Name := 'Satisfactory Shell WebUI';
  Exec('netsh', 'advfirewall firewall delete rule name="' + Name + '"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Exec('netsh',
    'advfirewall firewall add rule name="' + Name + '" dir=in action=allow protocol=TCP localport=' + Port,
    '', SW_HIDE, ewWaitUntilTerminated, Code);
end;

procedure WriteAppDataFiles;
var
  Dir: String;
begin
  Dir := ExpandConstant('{userappdata}\SatisfactoryShell');
  ForceDirectories(Dir + '\data');
  if not WriteTextFile(Dir + '\config.json', ConfigJson) then
    RaiseException('Could not write config.json under AppData.');
  if IsInstallServer then
  begin
    if not WriteTextFile(Dir + '\bootstrap.json', BootstrapJson) then
      RaiseException('Could not write bootstrap.json under AppData.');
  end
  else if FileExists(Dir + '\bootstrap.json') then
    DeleteFile(Dir + '\bootstrap.json');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if IsInstallSteamCmd then
      InstallSteamCmdFiles;
    if IsInstallServer then
      DownloadDedicatedServer;
    WriteAppDataFiles;
    if LanCheck.Checked then
      AddWebUiFirewall;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    if MsgBox('Also remove settings and logs in %APPDATA%\SatisfactoryShell? (Does not delete a dedicated server outside the install folder.)',
      mbConfirmation, MB_YESNO) = IDYES then
      DelTree(ExpandConstant('{userappdata}\SatisfactoryShell'), True, True, True);
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  Extra: String;
begin
  Extra := '';
  if IsInstallSteamCmd then
    Extra := Extra + 'SteamCMD: install into ' + InstallRoot + '\steamcmd (' + SizeSteamCmd + ')' + NewLine
  else
    Extra := Extra + 'SteamCMD: existing ' + SteamCmdPath + NewLine;
  if IsInstallServer then
    Extra := Extra + 'Server: download into ' + InstallRoot + '\server (' + SizeServer + ')' + NewLine +
      'First-run claim: yes (bootstrap.json)' + NewLine
  else
    Extra := Extra + 'Server: existing ' + ServerRootPath + NewLine +
      'First-run claim: no' + NewLine;
  Result :=
    MemoDirInfo + NewLine + NewLine +
    Extra + NewLine +
    'Game port: ' + Trim(GamePortEdit.Text) + '  Reliable: ' + Trim(RelPortEdit.Text) + NewLine +
    'WebUI: http://' + WebHost + ':' + Trim(WebPortEdit.Text) + NewLine +
    'Config: %APPDATA%\SatisfactoryShell\config.json';
end;
