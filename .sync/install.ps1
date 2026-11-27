# Run once per device after cloning: starts the sync now and at every login.
$repo = Split-Path $PSScriptRoot -Parent
$script = Join-Path $PSScriptRoot 'grimoire-sync.ps1'
$name = 'grimoire-sync ' + (Split-Path $repo -Leaf) + '.lnk'
$lnk = Join-Path ([Environment]::GetFolderPath('Startup')) $name
$runArgs = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`" -Repo `"$repo`""

$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath = (Get-Command powershell.exe).Source
$s.Arguments = $runArgs
$s.WorkingDirectory = $repo
$s.WindowStyle = 7
$s.Save()

Start-Process powershell.exe -ArgumentList $runArgs -WindowStyle Hidden
"Sync running for $repo and set to start at login ($lnk). Log: $repo\.git\grimoire-sync.log"
