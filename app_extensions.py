import os
from io import BytesIO
from flask import send_file, jsonify

from config import Config
import app as orig  # оригиналният ти app.py

# Зареждаме конфигурацията
try:
    orig.app.config.from_object(Config)
except Exception:
    pass

# PRAGMA пач за SQLite
_old_get_db = getattr(orig, "get_db", None)

def _patched_get_db():
    db = _old_get_db() if _old_get_db else None
    if db:
        try:
            db.execute("PRAGMA foreign_keys = ON;")
            db.execute("PRAGMA journal_mode = WAL;")
            db.execute("PRAGMA synchronous = NORMAL;")
        except Exception:
            pass
    return db

if _old_get_db:
    import sys as _sys
    _mod = _sys.modules.get('app')
    if _mod:
        _mod.get_db = _patched_get_db

# Опционално CSRF (включи с ENABLE_CSRF=1 в .env и добави {{ csrf_token() }} във всички POST форми)
if os.getenv("ENABLE_CSRF") == "1":
    try:
        from flask_wtf import CSRFProtect
        CSRFProtect(orig.app)
    except Exception as e:
        print("CSRF init error:", e)

# ---- Допълнителни маршрути ----

@orig.app.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

@orig.app.route('/export/reader_stats.xlsx')
def export_reader_stats_xlsx():
    """Експорт на демографска справка към Excel (XLSX)."""
    try:
        from openpyxl import Workbook
    except Exception:
        return "Липсва зависимост openpyxl. Инсталирай я от requirements_additions.txt", 500

    get_db = getattr(orig, "get_db", None)
    get_dates_from_request = getattr(orig, "get_dates_from_request", None)
    if not (get_db and get_dates_from_request):
        return "Не открих нужните функции (get_db/get_dates_from_request) в app.py", 500

    start_date, end_date, period_text = get_dates_from_request()
    db = get_db()

    def fetch(query, args):
        try:
            return db.execute(query, args).fetchall()
        except Exception:
            try:
                # fallback без WHERE ако колоните/филтрите са различни
                return db.execute(query.split(' WHERE')[0]).fetchall()
            except Exception:
                return []

    gender_stats = fetch(
        "SELECT gender, COUNT(*) AS count FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY gender",
        (start_date, end_date)
    )
    profession_stats = fetch(
        "SELECT profession, COUNT(*) AS count FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY profession ORDER BY count DESC",
        (start_date, end_date)
    )
    education_stats = fetch(
        "SELECT education, COUNT(*) AS count FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY education ORDER BY count DESC",
        (start_date, end_date)
    )

    wb = Workbook(); ws = wb.active; ws.title = "Статистика"
    ws.append(["Период", period_text]); ws.append([])
    ws.append(["По пол"]); ws.append(["Пол", "Брой"])
    for r in gender_stats:
        # r може да е sqlite3.Row (достъп и по индекс, и по ключ)
        ws.append([r["gender"] if "gender" in r.keys() else r[0],
                   r["count"] if "count" in r.keys() else r[1]])
    ws.append([])
    ws.append(["По професия"]); ws.append(["Професия", "Брой"])
    for r in profession_stats:
        ws.append([r["profession"] if "profession" in r.keys() else r[0],
                   r["count"] if "count" in r.keys() else r[1]])
    ws.append([])
    ws.append(["По образование"]); ws.append(["Образование", "Брой"])
    for r in education_stats:
        ws.append([r["education"] if "education" in r.keys() else r[0],
                   r["count"] if "count" in r.keys() else r[1]])

    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="reader_stats.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@orig.app.route('/export/reader_stats.pdf')
def export_reader_stats_pdf():
    """Експорт на демографска справка към PDF (ReportLab)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        return "Липсва зависимост reportlab. Инсталирай я от requirements_additions.txt", 500

    get_db = getattr(orig, "get_db", None)
    get_dates_from_request = getattr(orig, "get_dates_from_request", None)
    if not (get_db and get_dates_from_request):
        return "Не открих нужните функции (get_db/get_dates_from_request) в app.py", 500

    start_date, end_date, period_text = get_dates_from_request()
    db = get_db()

    def rows(q, args):
        try:
            return db.execute(q, args).fetchall()
        except Exception:
            try:
                return db.execute(q.split(' WHERE')[0]).fetchall()
            except Exception:
                return []

    gender = rows("SELECT gender, COUNT(*) c FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY gender", (start_date, end_date))
    prof   = rows("SELECT profession, COUNT(*) c FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY profession", (start_date, end_date))
    edu    = rows("SELECT education, COUNT(*) c FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY education", (start_date, end_date))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Демографска справка", styles['Title']))
    elements.append(Paragraph(f"Период: {period_text}", styles['Normal']))
    elements.append(Spacer(1, 12))

    def build_table(title, headers, data):
        elements.append(Paragraph(title, styles['Heading2']))
        table_data = [headers] + [[str(r[0] or 'Непосочено'), int(r[1])] for r in data]
        t = Table(table_data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(t); elements.append(Spacer(1, 12))

    build_table("По пол", ["Пол", "Брой"], gender)
    build_table("По професия", ["Професия", "Брой"], prof)
    build_table("По образование", ["Образование", "Брой"], edu)

    doc.build(elements)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="reader_stats.pdf", mimetype="application/pdf")
