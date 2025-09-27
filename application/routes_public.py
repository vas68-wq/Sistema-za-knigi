# application/routes_public.py

from datetime import date
from flask import (
    Blueprint, render_template, request, jsonify
)
from .database import get_db
from .utils import login_required, format_date_dmy, calculate_fine

main_bp = Blueprint('main', __name__, template_folder='templates')
public_bp = Blueprint('public', __name__, template_folder='templates')

@main_bp.route('/')
@login_required
def index():
    conn = get_db()
    current_year_val = date.today().year

    book_count = conn.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    reader_count = conn.execute('SELECT COUNT(*) FROM readers WHERE last_registration_year = ?', (current_year_val,)).fetchone()[0]
    borrowed_count = conn.execute('SELECT COUNT(*) FROM borrows WHERE return_date IS NULL').fetchone()[0]
    
    latest_books = conn.execute('SELECT tom_no, title, author, record_date, cover_image FROM books ORDER BY rowid DESC LIMIT 5').fetchall()
    latest_readers = conn.execute('SELECT * FROM readers ORDER BY rowid DESC LIMIT 5').fetchall()
    
    overdue_books_sql = "SELECT b.title, r.full_name, br.due_date, b.tom_no, r.reader_no FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no JOIN readers r ON br.reader_no = r.reader_no WHERE br.return_date IS NULL AND br.due_date < ? ORDER BY br.due_date"
    overdue_books = conn.execute(overdue_books_sql, (date.today().isoformat(),)).fetchall()
    
    genre_stats_data = conn.execute("SELECT genre, COUNT(*) as count FROM books WHERE genre IS NOT NULL GROUP BY genre ORDER BY count DESC").fetchall()
    chart_data = { "labels": [g['genre'] for g in genre_stats_data], "data": [g['count'] for g in genre_stats_data] }
    
    professions_for_modal = conn.execute('SELECT * FROM professions ORDER BY name').fetchall()
    educations_for_modal = conn.execute('SELECT * FROM educations ORDER BY name').fetchall()
    genres_for_modal = conn.execute('SELECT * FROM genres ORDER BY name').fetchall()

    # ПРОМЯНА: Добавяме заявка за извличане на читатели с неплатени глоби
    unpaid_fines_sql = """
        SELECT r.reader_no, r.full_name, SUM(br.fine_amount) as total_fine
        FROM readers r
        JOIN borrows br ON r.reader_no = br.reader_no
        WHERE br.fine_amount > 0 AND br.fine_paid_date IS NULL
        GROUP BY r.reader_no, r.full_name
        ORDER BY total_fine DESC
    """
    readers_with_fines = conn.execute(unpaid_fines_sql).fetchall()

    template_context = {
        'book_count': book_count, 'reader_count': reader_count, 'borrowed_count': borrowed_count,
        'latest_books': latest_books, 'latest_readers': latest_readers, 'overdue_books': overdue_books,
        'chart_data': chart_data, 'calculate_fine': calculate_fine,
        'professions_for_modal': professions_for_modal,
        'educations_for_modal': educations_for_modal,
        'genres_for_modal': genres_for_modal,
        'readers_with_fines': readers_with_fines  # Подаваме новите данни към шаблона
    }
    
    return render_template('index.html', **template_context)

@public_bp.route('/public_catalog')
def public_catalog_page():
    conn = get_db()
    search_query = request.args.get('query', '')
    genre_filter = request.args.get('genre', '')

    genres = conn.execute("SELECT name FROM genres ORDER BY name").fetchall()
    latest_books_sql = "SELECT * FROM books WHERE cover_image IS NOT NULL ORDER BY record_date DESC, rowid DESC LIMIT 15"
    latest_books = conn.execute(latest_books_sql).fetchall()
    popular_books_sql = "SELECT b.*, COUNT(br.book_tom_no) as borrow_count FROM books b JOIN borrows br ON b.tom_no = br.book_tom_no WHERE br.borrow_date >= date('now', '-1 year') AND b.cover_image IS NOT NULL GROUP BY b.tom_no ORDER BY borrow_count DESC LIMIT 15"
    popular_books = conn.execute(popular_books_sql).fetchall()

    return render_template(
        'public_catalog.html', 
        genres=genres, 
        latest_books=latest_books, 
        popular_books=popular_books,
        initial_query=search_query,
        initial_genre=genre_filter
    )

@public_bp.route('/api/public_search_books')
def api_public_search_books():
    search_query = request.args.get('query', '').strip()
    genre_filter = request.args.get('genre', '').strip()
    if len(search_query) < 2 and not genre_filter: return jsonify([])
    conn = get_db()
    base_sql = "SELECT DISTINCT b.title, b.author, b.cover_image, b.tom_no FROM books b"
    params, where_clauses = [], []
    if search_query:
        base_sql += " JOIN books_fts fts ON b.tom_no = fts.rowid"
        where_clauses.append("books_fts MATCH ?")
        params.append(' '.join([term + '*' for term in search_query.split()]))
    if genre_filter:
        where_clauses.append("b.genre = ?")
        params.append(genre_filter)
    if where_clauses: base_sql += " WHERE " + " AND ".join(where_clauses)
    base_sql += " LIMIT 100"
    matching_books = conn.execute(base_sql, params).fetchall()
    unique_books = list({book['tom_no']: book for book in matching_books}.values())
    books_for_template = []
    for book in unique_books:
        status_sql = "SELECT CASE WHEN br.borrow_id IS NULL THEN 'Налична' ELSE 'Заета' END as status, br.due_date FROM borrows br WHERE br.book_tom_no = ? AND br.return_date IS NULL"
        status_row = conn.execute(status_sql, (book['tom_no'],)).fetchone()
        status = status_row['status'] if status_row else 'Налична'
        due_date = status_row['due_date'] if status_row else None
        due_date_formatted = format_date_dmy(due_date) if due_date else None
        books_for_template.append({ 'tom_no': book['tom_no'], 'title': book['title'], 'author': book['author'], 'cover_image': book['cover_image'], 'status': status, 'due_date': due_date_formatted })
    return jsonify(books_for_template)

@main_bp.app_errorhandler(404)
def not_found_error(error): return render_template('404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    print(f"!!! Възникна вътрешна грешка: {error}")
    return render_template('500.html'), 500