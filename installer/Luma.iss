; Compile with Inno Setup 6 after building and reviewing dist/Luma.
; Local verification installer only until release/release-gates.json is cleared.
#ifndef AppVersion
#define AppVersion "0.3.5-dev"
#endif
[Setup]
#ifdef VerificationBuild
AppId={{66CB1A30-EC57-45EA-8830-C44C620F93B8}
CreateUninstallRegKey=no
#else
AppId={{A3658D58-C019-45CB-A0AF-2CBC8871E6B9}
#endif
AppName=Luma Reader
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\Luma Reader
DefaultGroupName=Luma Reader
PrivilegesRequired=lowest
OutputDir=..\dist\installer
#ifdef VerificationBuild
OutputBaseFilename=Luma-{#AppVersion}-Verification-Setup
#else
OutputBaseFilename=Luma-{#AppVersion}-Setup
#endif
SetupIconFile=..\assets\luma.ico
UninstallDisplayIcon={app}\Luma.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

#include "obsolete-runtime.iss"

[Files]
Source: "..\dist\Luma\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Icons]
Name: "{group}\Luma Reader"; Filename: "{app}\Luma.exe"
Name: "{autodesktop}\Luma Reader"; Filename: "{app}\Luma.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Luma.exe"; Description: "Open Luma Reader"; Flags: nowait postinstall skipifsilent

; User notes, voices and %LOCALAPPDATA%/Luma Reader are deliberately preserved on uninstall.
