@echo off
REM Activate the virtual environment
call "%~dp0venv\Scripts\activate.bat"

REM Install required packages
@REM pip install opencv-python
pip install firebase_admin

REM Deactivate the virtual environment
deactivate
