# application/routes_books.py

import os
import csv
import io
import sqlite3
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, send_from_directory, session, jsonify
)
from werkzeug.utils import secure_filename
from .database import get_db
# ПРОМЯНА: Импортираме новата функция
from .utils import login_required, log_activity, clean_int, clean_price, allowed_file, clean_date, get_setting

books_bp = Blueprint('books', __name__, template_folder='templates')

@books_bp.route('/books')
@login_required
def books_list_page():
    """Рендерира празната страница и подава жанровете за модалния прозорец."""
    conn = get_db()
    genres_data = conn.execute('SELECT * FROM genres ORDER BY name').fetchall()
    genres_for_modal = [dict(row) for row in genres_data]
    return render_template('books_list.html', genres_for_modal=genres_for_modal)

@books_bp.route('/api/books')
@login_required
def api_books():
    """API ендпойнт, който връща книгите като JSON."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('query', '').strip()
    
    # ПРОМЯНА: Използваме стойността от настройките
    per_page = int(get_setting('books_per_page', 10))
    
    offset = (page - 1) * per_page
    conn = get_db()
    
    books = []
    total_books = 0

    if search_query:
        query_for_fts = ' '.join([term + '*' for term in search_query.split()])
        sql_books = "SELECT b.* FROM books b JOIN books_fts fts ON b.tom_no = fts.rowid WHERE books_fts MATCH ? ORDER BY rank LIMIT ? OFFSET ?"
        sql_count = "SELECT COUNT(*) FROM books b JOIN books_fts fts ON b.tom_no = fts.rowid WHERE books_fts MATCH ?"
        total_books = conn.execute(sql_count, (query_for_fts,)).fetchone()[0]
        books_data = conn.execute(sql_books, (query_for_fts, per_page, offset)).fetchall()
    else:
        total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        books_data = conn.execute('SELECT * FROM books ORDER BY rowid DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()

    total_pages = (total_books + per_page - 1) // per_page
    
    genres_data = conn.execute('SELECT * FROM genres ORDER BY name').fetchall()
    
    return jsonify({
        'books': [dict(row) for row in books_data],
        'genres': [dict(row) for row in genres_data],
        'pagination': {
            'page': page,
            'total_pages': total_pages,
            'total_books': total_books
        }
    })

@books_bp.route('/api/book/<path:tom_no>')
@login_required
def api_get_book(tom_no):
    """API ендпойнт, който връща данните за една книга като JSON."""
    conn = get_db()
    book = conn.execute('SELECT * FROM books WHERE tom_no = ?', (tom_no,)).fetchone()
    if book:
        return jsonify(dict(book))
    return jsonify({'error': 'Book not found'}), 404


@books_bp.route('/book/<path:tom_no>')
def book_details_page(tom_no):
    conn = get_db()
    book = conn.execute('SELECT * FROM books WHERE tom_no = ?', (tom_no,)).fetchone()
    if not book:
        default_redirect = url_for('public.public_catalog_page') if 'user_id' not in session else url_for('books.books_list_page')
        flash('Книга не е намерена!', 'danger')
        return redirect(default_redirect)

    is_admin_view = 'user_id' in session
    
    borrow_history = []
    if is_admin_view:
        borrow_history_sql = "SELECT br.*, r.full_name, r.reader_no FROM borrows br JOIN readers r ON br.reader_no = r.reader_no WHERE br.book_tom_no = ? ORDER BY br.borrow_date DESC"
        borrow_history = conn.execute(borrow_history_sql, (tom_no,)).fetchall()
    
    back_url = request.args.get('back_url', None)

    return render_template('book_details.html', book=book, borrow_history=borrow_history, is_admin_view=is_admin_view, back_url=back_url)


@books_bp.route('/add_book', methods=['POST'])
@login_required
def add_book_action():
    conn = get_db()
    final_genre = request.form.get('genre')
    if final_genre:
        conn.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (final_genre,))

    cover_filename = None
    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            covers_folder_path = os.path.join(current_app.root_path, '..', current_app.config['COVERS_FOLDER'])
            cover_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(covers_folder_path, cover_filename))

    try:
        sql = "INSERT INTO books (tom_no, isbn, author, title, genre, publish_year, price, is_donation, record_date, cover_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE, ?)"
        params = (request.form['inv_number'], request.form['isbn'], request.form['author'], request.form['title'], final_genre, clean_int(request.form['publish_year']), clean_price(request.form['price']), 'is_donation' in request.form, cover_filename)
        conn.execute(sql, params)
        conn.commit()
        log_activity("Добавена книга", f"Книга '{request.form['title']}' (Инв.№ {request.form['inv_number']})")
        flash('Книгата е записана успешно!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Грешка при добавяне на книга: {e}', 'danger')
    return redirect(url_for('books.books_list_page'))

@books_bp.route('/edit_book/<path:tom_no>', methods=['POST'])
@login_required
def edit_book_action(tom_no):
    conn = get_db()
    
    final_genre = request.form.get('genre')
    if final_genre:
        conn.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (final_genre,))

    cover_filename = request.form.get('current_cover', None)
    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            covers_folder_path = os.path.join(current_app.root_path, '..', current_app.config['COVERS_FOLDER'])
            cover_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(covers_folder_path, cover_filename))

    sql = "UPDATE books SET title = ?, author = ?, isbn = ?, genre = ?, publish_year = ?, price = ?, is_donation = ?, cover_image = ? WHERE tom_no = ?"
    params = (request.form['title'], request.form['author'], request.form['isbn'], final_genre, clean_int(request.form['publish_year']), clean_price(request.form['price']), 'is_donation' in request.form, cover_filename, tom_no)
    conn.execute(sql, params)
    conn.commit()
    log_activity("Редактирана книга", f"Книга '{request.form['title']}' (Инв.№ {tom_no})")
    flash("Промените по книгата са запазени.", "success")
    
    return redirect(request.referrer or url_for('books.book_details_page', tom_no=tom_no))


@books_bp.route('/delete_book/<path:tom_no>', methods=['POST'])
@login_required
def delete_book(tom_no):
    conn = get_db()
    book = conn.execute('SELECT title, cover_image FROM books WHERE tom_no = ?', (tom_no,)).fetchone()
    if book:
        if book['cover_image']:
            try:
                cover_path = os.path.join(current_app.root_path, '..', current_app.config['COVERS_FOLDER'], book['cover_image'])
                os.remove(cover_path)
            except OSError as e:
                print(f"Error deleting cover file: {e}")
        conn.execute('DELETE FROM books WHERE tom_no = ?', (tom_no,))
        conn.commit()
        log_activity("Изтрита книга", f"Книга '{book['title']}' (Инв.№ {tom_no})")
        flash(f"Книга '{book['title']}' беше изтрита.", 'success')
    return redirect(url_for('books.books_list_page'))

@books_bp.route('/import_books', methods=['GET', 'POST'])
@login_required
def import_books_page():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or file.filename == '':
            flash("Моля, изберете CSV файл за качване.", "warning"); return redirect(request.url)
        try:
            file_content = file.stream.read()
            try: decoded_content = file_content.decode('utf-8')
            except UnicodeDecodeError: decoded_content = file_content.decode('windows-1251')
            dialect = csv.Sniffer().sniff(decoded_content.splitlines()[0]); stream = io.StringIO(decoded_content, newline=None); csv_reader = csv.reader(stream, dialect)
            conn = get_db(); cursor = conn.cursor(); next(csv_reader)
            books_added, errors_found = 0, 0
            for i, row in enumerate(csv_reader):
                try:
                    if not row or len(row) < 8: continue
                    tom_no, isbn, author, title, genre, publish_year, record_date, price = row[:8]
                    if not tom_no or not title: continue
                    params = (tom_no, isbn, author, title, genre, clean_int(publish_year), clean_date(record_date), clean_price(price))
                    cursor.execute("INSERT OR IGNORE INTO books (tom_no, isbn, author, title, genre, publish_year, record_date, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", params)
                    if genre: cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (genre.strip(),))
                    books_added += 1
                except sqlite3.Error as row_error:
                    errors_found += 1; print(f"!!! Грешка на ред {i+2}: {row_error} --> ДАННИ: {row}");
            conn.commit()
            print("Преизграждане на FTS индекса за книги..."); conn.execute("INSERT INTO books_fts(books_fts) VALUES('rebuild');"); conn.commit(); print("Индексът е преизграден.")
            log_activity("Импорт на книги", f"Импортирани са {books_added} книги.")
            flash(f"Импортирането завърши. Добавени са {books_added} книги.", "success")
            return redirect(url_for('books.books_list_page'))
        except Exception as e:
            flash(f"Възникна грешка при импортирането: {e}", "danger"); return redirect(url_for('books.import_books_page'))
    return render_template('import.html')

@books_bp.route('/covers/<path:filename>')
def serve_cover(filename):
    directory = os.path.abspath(os.path.join(current_app.root_path, '..', current_app.config['COVERS_FOLDER']))
    return send_from_directory(directory, filename)