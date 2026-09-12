@echo off
call ".venv\Scripts\activate.bat"
python -m swiggy.oauth_login
pause
