@echo off
echo Setting up Python Virtual Environment for PowerBI QA Agent...
python -m venv venv
call venv\Scripts\activate
echo Installing dependencies...
pip install -r requirements.txt
echo Installing Playwright Browsers...
playwright install chromium
echo Setup Complete!
pause