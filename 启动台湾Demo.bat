@echo off
setlocal
title Taiwan Official Data Demo
cd /d "%~dp0"

where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo Windows PowerShell was not found.
  echo Please contact technical support.
  pause
  exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_demo.ps1"
set "DEMO_EXIT_CODE=%ERRORLEVEL%"

if not "%DEMO_EXIT_CODE%"=="0" (
  echo.
  echo Demo startup failed. Keep this window open and send the error above to technical support.
  pause
)

exit /b %DEMO_EXIT_CODE%
