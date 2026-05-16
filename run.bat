@echo off
title AI Paper Summarizer
echo ^
🚀 AI Paper Summarizer starting...
echo.

set PYTHON=C:\Users\haris\AppData\Local\Programs\Python\Python314\python.exe
set DIR=E:\Codes\ai-paper-summarizer

echo [1/2] Starting Backend on http://localhost:8000 ...
start "Backend" "%PYTHON%" -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend on http://localhost:8501 ...
start "Frontend" "%PYTHON%" -m streamlit run frontend/app.py --server.port 8501
timeout /t 5 /nobreak >nul

echo.
echo ^
✅ Both running! Open http://localhost:8501 in your browser.
start http://localhost:8501
echo.
echo Close this window to stop the app ^(or close the two terminal windows^)
pause
