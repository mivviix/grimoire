@echo off
rem inscribe for Windows shells: runs lib\inscribe.py with the py launcher (or python), in UTF-8 mode.
where py >nul 2>nul
if %errorlevel%==0 (py -3 -X utf8 -I "%~dp0..\lib\inscribe.py" %*) else (python -X utf8 -I "%~dp0..\lib\inscribe.py" %*)
exit /b %errorlevel%
