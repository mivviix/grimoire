@echo off
rem Windows install: grim/inscribe launchers in %USERPROFILE%\.local\bin (added to your user PATH),
rem the skill linked into %USERPROFILE%\.claude\skills\grimoire. Source stays in this repo. No admin needed.
setlocal
set "here=%~dp0"
set "here=%here:~0,-1%"
set "bin=%USERPROFILE%\.local\bin"
set "skills=%USERPROFILE%\.claude\skills"

rem Prefer the py launcher, else python on PATH. -X utf8: vault files are UTF-8 whatever the Windows locale.
where py >nul 2>nul && (set "pyexe=py -3") || (
  where python >nul 2>nul && (set "pyexe=python") || (
    echo Python 3.11+ not found. Install it from python.org, then run this again.
    exit /b 1
  )
)

if not exist "%bin%" mkdir "%bin%"
if not exist "%skills%" mkdir "%skills%"
> "%bin%\grim.cmd" echo @%pyexe% -X utf8 "%here%\grim.py" %%*
> "%bin%\inscribe.cmd" echo @%pyexe% -X utf8 "%here%\inscribe.py" %%*

rem rmdir without /s only removes an old link; it refuses (safely) if a real folder is in the way.
if exist "%skills%\grimoire" rmdir "%skills%\grimoire"
mklink /J "%skills%\grimoire" "%here%\skill" >nul || (
  echo Could not link the skill: remove "%skills%\grimoire" and run this again.
  exit /b 1
)

rem Add bin to the user PATH once. Not setx: it truncates long PATHs and copies the system PATH in.
powershell -NoProfile -Command "$d=$env:BIN; $p=[Environment]::GetEnvironmentVariable('Path','User'); if (-not (($p -split ';') -contains $d)) { [Environment]::SetEnvironmentVariable('Path', (($p.TrimEnd(';') + ';' + $d).TrimStart(';')), 'User'); 'added to PATH: ' + $d + ' (open a new terminal)' }"
echo installed: grim, inscribe, skill grimoire
endlocal
