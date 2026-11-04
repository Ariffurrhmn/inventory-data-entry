@echo off
title Inventory Data Entry - end-to-end demo (phone mode)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -Open -Lan
if errorlevel 1 pause
