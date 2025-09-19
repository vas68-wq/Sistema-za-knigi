import os, sys, sqlite3, zipfile, datetime, glob, tempfile

RETENTION = 30  # колко архивa да пазим

def app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

def main():
    base = app_dir()
    db_path = os.path.join(base, "library.db")
    if not os.path.exists(db_path):
        raise SystemExit(f"Не намирам {db_path}. Пусни този скрипт там, където е library.db.")

    backups_dir = os.path.join(base, "backups")
    os.makedirs(backups_dir, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tmp_copy = os.path.join(tempfile.gettempdir(), f"library_{ts}.sqlite")

    # Атомарен backup (без да спираме приложението)
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(tmp_copy)
    with dst:
        src.backup(dst)
    src.close(); dst.close()

    # Валидиране на целостта
    conn = sqlite3.connect(tmp_copy)
    ok = conn.execute("PRAGMA integrity_check;").fetchone()[0]
    conn.close()
    if ok != "ok":
        os.remove(tmp_copy)
        raise SystemExit(f"integrity_check не е OK: {ok}")

    # Компресиране
    zip_name = os.path.join(backups_dir, f"library_{ts}.sqlite.zip")
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tmp_copy, arcname=f"library_{ts}.sqlite")
    os.remove(tmp_copy)

    # Ротация
    zips = sorted(glob.glob(os.path.join(backups_dir, "library_*.sqlite.zip")))
    for old in zips[:-RETENTION]:
        try: os.remove(old)
        except: pass

    print(f"Backup OK -> {zip_name}")

if __name__ == "__main__":
    main()
