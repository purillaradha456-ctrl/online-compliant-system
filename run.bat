@echo off
echo ========================================================
echo   Starting Online Complaint Management System (ResolveDesk)
echo ========================================================
echo.
echo Initializing database...
py database.py
echo.
echo Starting Flask web server at http://127.0.0.1:5000 ...
echo Press Ctrl+C to terminate the server.
echo.
py app.py
pause
