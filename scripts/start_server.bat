@echo off
echo Starting PowerBI QA Agent API...
call venv\Scripts\activate
cd backend
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause