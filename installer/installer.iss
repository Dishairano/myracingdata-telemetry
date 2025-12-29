; Inno Setup script for MyRacingData Telemetry Capture
#define AppName "MyRacingData Telemetry Capture"
#define AppVersion "1.0.0"
#define AppPublisher "MyRacingData"
#define AppExe GetString("AppExe", "dist\\MyRacingData-Telemetry.exe")
#define OutputDir GetString("OutputDir", "dist")

[Setup]
AppId={{6F8B5A7E-8D50-4CB5-86CC-3D3A4D1F2CE4}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf64}\\MyRacingData\\Telemetry
DefaultGroupName=MyRacingData
OutputDir={#OutputDir}
OutputBaseFilename=MyRacingData-Telemetry-Installer
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\MyRacingData Telemetry"; Filename: "{app}\\MyRacingData-Telemetry.exe"
Name: "{commondesktop}\\MyRacingData Telemetry"; Filename: "{app}\\MyRacingData-Telemetry.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\\MyRacingData-Telemetry.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
