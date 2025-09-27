@echo off
chcp 65001 > nul
title LibraryApp
cd /d "C:\Users\user\Desktop\НОВА СИСТЕМА\LibraryApp\"
echo Starting Library Application... please wait.
echo To stop the server, close this window.

call venv\Scripts\activate.bat
py run.py
