@echo off
setlocal
cd /d "D:\Нова папка (2)\ПРОЕКТ_ФИНАЛ_2_with_backup\ПРОЕКТ ФИНАЛ 2"
set LOGDIR=backups
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\task_log.txt
echo === %date% %time% START >> "%LOGFILE%"

"C:\Users\VAS\AppData\Local\Programs\Python\Python311\python.exe" "backup_db.py" >> "%LOGFILE%" 2>&1

echo === %date% %time% END   >> "%LOGFILE%"
