# application/routes_reports.py

import io
import csv
from datetime import date, datetime
from flask import Blueprint, render_template, request, Response
from .database import get_db
from .utils import login_required

reports_bp = Blueprint('reports', __name__, template_folder='templates')

# --- Помощни функции само за този модул ---

def get_dates_from_request():
    """Извлича начална и крайна дата от параметрите на заявката."""
    filter_type = request.args.get('filter_type')
    year_str = request.args.get('year', str(date.today().year))
    start_date_req = request.args.get('start_date')
    end_date_req = request.args.get('end_date')

    # Уверяваме се, че годината е валидно число
    try:
        year = int(year_str)
    except (ValueError, TypeError):
        year = date.today().year

    if filter_type == 'period' and start_date_req and end_date_req:
        start_date = start_date_req
        end_date = end_date_req
        period_text = f"за периода от {start_date} до {end_date}"
    else:
        # Стойности по подразбиране - по година
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        period_text = f"за {year} г."
        
    return start_date, end_date, period_text

def generate_csv(data, headers):
    """Генерира CSV файл от данни и го връща като HTTP Response."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    
    return Response(
        output.getvalue().encode('utf-8-sig'), # utf-8-sig за правилна работа с кирилица в Excel
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=report.csv"}
    )

# --- Маршрути за справки (HTML) ---

@reports_bp.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@reports_bp.route('/report/new_books')
@login_required
def report_new_books():
    start_date, end_date, period_text = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT tom_no, title, author, is_donation, price, record_date FROM books WHERE record_date BETWEEN ? AND ? ORDER BY record_date", (start_date, end_date)).fetchall()
    
    total_count = len(results)
    donated_count = sum(1 for r in results if r['is_donation'])
    purchased_count = total_count - donated_count
    donated_value = sum(r['price'] or 0 for r in results if r['is_donation'])
    purchased_value = sum(r['price'] or 0 for r in results if not r['is_donation'])
    
    return render_template('report_new_books_summary.html', title=f"Отчет за нови книги {period_text}", 
                           results=results, start_date=start_date, end_date=end_date, total_count=total_count,
                           donated_count=donated_count, donated_value=donated_value,
                           purchased_count=purchased_count, purchased_value=purchased_value, year=start_date[:4])

@reports_bp.route('/report/under_14')
@login_required
def report_under_14():
    start_date, end_date, period_text = get_dates_from_request()
    year_to_check = datetime.strptime(start_date, '%Y-%m-%d').year
    conn = get_db()
    results = conn.execute(
        "SELECT reader_no, full_name, registration_date FROM readers WHERE is_under_14 = 1 AND last_registration_year = ? ORDER BY full_name",
        (year_to_check,)
    ).fetchall()
    title = f"Активни читатели до 14 г. {period_text}"
    return render_template('report_results.html', title=title, results=results, total_count=len(results), headers=['Читателски №', 'Име', 'Дата на регистрация'])

@reports_bp.route('/report/active_readers')
@login_required
def report_active_readers():
    start_date, end_date, period_text = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT r.full_name, r.reader_no, COUNT(br.borrow_id) as books_count FROM borrows br JOIN readers r ON br.reader_no = r.reader_no WHERE br.borrow_date BETWEEN ? AND ? GROUP BY r.reader_no ORDER BY books_count DESC", (start_date, end_date)).fetchall()
    return render_template('report_results.html', title=f"Най-активни читатели {period_text}", results=results, total_count=len(results), headers=['Име', 'Читателски №', 'Брой заети книги'])

@reports_bp.route('/report/popular_books')
@login_required
def report_popular_books():
    start_date, end_date, period_text = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT b.title, b.author, COUNT(br.borrow_id) as borrow_count FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no WHERE br.borrow_date BETWEEN ? AND ? GROUP BY b.tom_no ORDER BY borrow_count DESC", (start_date, end_date)).fetchall()
    total_borrows_row = conn.execute("SELECT COUNT(borrow_id) FROM borrows WHERE borrow_date BETWEEN ? AND ?", (start_date, end_date)).fetchone()
    total_borrows = total_borrows_row[0] or 0
    return render_template('report_results.html', title=f"Най-популярни книги {period_text}", results=results, total_count=len(results), total_borrows=total_borrows, headers=['Заглавие', 'Автор', 'Брой заемания'])

@reports_bp.route('/report/reader_stats')
@login_required
def report_reader_stats():
    start_date, end_date, period_text = get_dates_from_request()
    conn = get_db()
    gender_stats = conn.execute("SELECT gender, COUNT(*) as count FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY gender", (start_date, end_date)).fetchall()
    profession_stats = conn.execute("SELECT profession, COUNT(*) as count FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY profession ORDER BY count DESC", (start_date, end_date)).fetchall()
    education_stats = conn.execute("SELECT education, COUNT(*) as count FROM readers WHERE registration_date BETWEEN ? AND ? GROUP BY education ORDER BY count DESC", (start_date, end_date)).fetchall()
    return render_template('report_reader_stats.html', title=f"Демографска справка {period_text}", gender_stats=gender_stats, profession_stats=profession_stats, education_stats=education_stats)

@reports_bp.route('/report/activity')
@login_required
def activity_report_page():
    # ПРОМЯНА: Използваме помощната функция, за да вземем периода
    start_date, end_date, period_text = get_dates_from_request()
    conn = get_db()
    
    # Дефинираме SQL заявките с филтър по дата
    base_query = " FROM activity_log WHERE date(timestamp) BETWEEN ? AND ?"
    
    actions_by_user_sql = "SELECT username, COUNT(*) as action_count" + base_query + " GROUP BY username ORDER BY action_count DESC"
    actions_by_type_sql = "SELECT action, COUNT(*) as action_count" + base_query + " GROUP BY action ORDER BY action_count DESC"
    total_actions_sql = "SELECT COUNT(*)" + base_query
    logs_sql = "SELECT *" + base_query + " ORDER BY timestamp DESC LIMIT 1000"

    # Изпълняваме заявките с параметри за дата
    actions_by_user = conn.execute(actions_by_user_sql, (start_date, end_date)).fetchall()
    actions_by_type = conn.execute(actions_by_type_sql, (start_date, end_date)).fetchall()
    total_actions = conn.execute(total_actions_sql, (start_date, end_date)).fetchone()[0]
    logs = conn.execute(logs_sql, (start_date, end_date)).fetchall()

    return render_template(
        'report_activity.html', 
        title=f"Дневник на дейността {period_text}",
        logs=logs,
        actions_by_user=actions_by_user,
        actions_by_type=actions_by_type,
        total_actions=total_actions
    )

# --- Маршрути за експорт (CSV) ---

@reports_bp.route('/export/new_books')
@login_required
def export_report_new_books():
    start_date, end_date, _ = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT tom_no, title, author, CASE WHEN is_donation THEN 'Дарение' ELSE 'Покупка' END, price, record_date FROM books WHERE record_date BETWEEN ? AND ? ORDER BY record_date", (start_date, end_date)).fetchall()
    headers = ['Инв. №', 'Заглавие', 'Автор', 'Тип', 'Цена', 'Дата на запис']
    return generate_csv(results, headers)
    
@reports_bp.route('/export/under_14')
@login_required
def export_under_14():
    start_date, _, _ = get_dates_from_request()
    year_to_check = datetime.strptime(start_date, '%Y-%m-%d').year
    conn = get_db()
    results = conn.execute(
        "SELECT reader_no, full_name, registration_date FROM readers WHERE is_under_14 = 1 AND last_registration_year = ? ORDER BY full_name",
        (year_to_check,)
    ).fetchall()
    headers = ['Читателски №', 'Име', 'Дата на регистрация']
    return generate_csv(results, headers)

@reports_bp.route('/export/active_readers')
@login_required
def export_active_readers():
    start_date, end_date, _ = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT r.full_name, r.reader_no, COUNT(br.borrow_id) as books_count FROM borrows br JOIN readers r ON br.reader_no = r.reader_no WHERE br.borrow_date BETWEEN ? AND ? GROUP BY r.reader_no ORDER BY books_count DESC", (start_date, end_date)).fetchall()
    headers = ['Име', 'Читателски №', 'Брой заети книги']
    return generate_csv(results, headers)
    
@reports_bp.route('/export/popular_books')
@login_required
def export_popular_books():
    start_date, end_date, _ = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT b.title, b.author, COUNT(br.borrow_id) as borrow_count FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no WHERE br.borrow_date BETWEEN ? AND ? GROUP BY b.tom_no ORDER BY borrow_count DESC", (start_date, end_date)).fetchall()
    headers = ['Заглавие', 'Автор', 'Брой заемания']
    return generate_csv(results, headers)

@reports_bp.route('/export/activity')
@login_required
def export_report_activity():
    # ПРОМЯНА: Добавяме филтриране и при експорт
    start_date, end_date, _ = get_dates_from_request()
    conn = get_db()
    results = conn.execute("SELECT timestamp, username, action, details FROM activity_log WHERE date(timestamp) BETWEEN ? AND ? ORDER BY timestamp DESC", (start_date, end_date)).fetchall()
    headers = ['Дата и час', 'Потребител', 'Действие', 'Детайли']
    return generate_csv(results, headers)