@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_classifier.ps1" -Open
if errorlevel 1 pause
