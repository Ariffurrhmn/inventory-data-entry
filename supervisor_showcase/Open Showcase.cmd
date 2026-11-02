@echo off
title Supervisor Showcase
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -Open
if errorlevel 1 pause
