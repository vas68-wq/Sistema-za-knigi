@echo off
setlocal
REM Стартира бекъп (трябва да е в същата папка, където е library.db и app.py)
if exist venv\Scripts\python.exe (
  call venv\Scripts\python.exe "%~dp0backup_db.py"
) else (
  python "%~dp0backup_db.py"
)
pause
