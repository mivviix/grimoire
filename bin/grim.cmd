@echo off
rem grim for Windows shells: runs lib\grim.py with the py launcher (or python), in UTF-8 mode.
where py >nul 2>nul
if %errorlevel%==0 (py -3 -X utf8 -I "%~dp0..\lib\grim.py" %*) else (python -X utf8 -I "%~dp0..\lib\grim.py" %*)
exit /b %errorlevel%
