@echo off
chcp 65001 >nul
ECHO --- Стартиране на скрипт за бекъп ---

REM --- Първа папка (LibraryApp) ---
set "SOURCE_FOLDER_1=C:\LibraryApp"
set "DESTINATION_FOLDER_1=D:\backups\LibraryApp"

REM --- Втора папка (cloudflare) ---
set "SOURCE_FOLDER_2=C:\cloudflare"
set "DESTINATION_FOLDER_2=D:\backups\cloudflare"

REM --- Трета папка (LibraryBackup) ---
set "SOURCE_FOLDER_3=C:\LibraryBackup"
set "DESTINATION_FOLDER_3=D:\backups\LibraryBackup"

ECHO.
ECHO Копиране на LibraryApp...
robocopy "%SOURCE_FOLDER_1%" "%DESTINATION_FOLDER_1%" /E /MIR
ECHO.

ECHO Копиране на cloudflare...
robocopy "%SOURCE_FOLDER_2%" "%DESTINATION_FOLDER_2%" /E /MIR
ECHO.

ECHO Копиране на LibraryBackup...
robocopy "%SOURCE_FOLDER_2%" "%DESTINATION_FOLDER_3%" /E /MIR
ECHO.

ECHO --- Бекъпът приключи успешно! ---