@echo off
setlocal
set DIR=%~dp0
cd /d "%DIR%"

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"

set PYTHONPATH=%DIR%;%PYTHONPATH%
streamlit run app.py
endlocal
