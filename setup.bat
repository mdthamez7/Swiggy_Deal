@echo off
setlocal
echo ==============================================
echo LootDeal Swiggy - Local Setup
echo ==============================================
if not exist ".venv" (
    py -3.12 -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist ".env" copy ".env.example" ".env"
echo.
echo Setup complete.
echo Next:
echo   1. Edit .env for email alerts.
echo   2. Run: python -m swiggy.oauth_login
echo   3. Run: python run_scanner.py
pause
