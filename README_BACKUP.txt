=============================
БЕКЪП ПАКЕТ ЗА "ПРОЕКТ ФИНАЛ 2"
=============================

Съдържание:
- backup_db.py       -> прави атомарен бекъп на library.db в папка backups/
- Backup_now.bat     -> стартира бекъп с 2 клика
- backups/           -> тук се създават zip архивите library_YYYY-MM-DD_HH-MM-SS.sqlite.zip

Как да направя бекъп веднага?
------------------------------
1) Двоен клик на "Backup_now.bat".
2) Ще се появи ZIP в папка "backups", например:
   backups\library_2025-08-15_21-00-00.sqlite.zip

Автоматичен ежедневен бекъп (Windows Task Scheduler)
----------------------------------------------------
1) Отвори Task Scheduler -> Create Task.
2) "Triggers": Daily (напр. 21:00).
3) "Actions": Start a program.
   Program/script:
     python
   Add arguments:
     "C:\Път\до\ПРОЕКТ ФИНАЛ 2\backup_db.py"
   Start in:
     C:\Път\до\ПРОЕКТ ФИНАЛ 2
(или посочи пълния път до venv\Scripts\python.exe, ако ползваш venv)

Възстановяване (Restore)
------------------------
1) Затвори приложението (ако работи).
2) Отвори папка "backups", избери архив по дата.
3) Разархивирай .sqlite файла от ZIP и го преименувай на "library.db".
4) Замести текущия "library.db" в папката на проекта.
5) Стартирай приложението.

Съвети
------
- Синхронизирай "backups" към OneDrive/Google Drive/Dropbox.
- Прави външно копие (USB) поне седмично.
- Периодично тествай restore в отделна папка.
