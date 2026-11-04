@echo off
title Inventory Data Entry - end-to-end demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -Open
if errorlevel 1 pause
