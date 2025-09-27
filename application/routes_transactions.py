# application/routes_transactions.py

import os
import base64
from datetime import date, datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    jsonify, current_app, send_from_directory
)
from .database import get_db
from .utils import login_required, log_activity, calculate_fine, format_date_dmy, get_setting

transactions_bp = Blueprint('transactions', __name__, template_folder='templates')

@transactions_bp.route('/borrow', methods=['GET'])
@login_required
def borrow_page():
    selected_reader = request.args.get('selected_reader', None)
    current_year_val = date.today().year
    conn = get_db()
    
    available_books_sql = "SELECT * FROM books WHERE tom_no NOT IN (SELECT book_tom_no FROM borrows WHERE return_date IS NULL) ORDER BY title"
    available_books = conn.execute(available_books_sql).fetchall()
    
    all_readers_sql = "SELECT * FROM readers WHERE last_registration_year = ? ORDER BY full_name"
    all_readers = conn.execute(all_readers_sql, (current_year_val,)).fetchall()
    
    return render_template('borrow_book.html', books=available_books, readers=all_readers, selected_reader=selected_reader)

@transactions_bp.route('/process_borrow', methods=['POST'])
@login_required
def process_borrow():
    book_tom_no = request.form.get('book_tom_no')
    reader_no = request.form.get('reader_no')
    signature_data = request.form.get('signature')
    next_action = request.form.get('next_action')

    if not book_tom_no or not reader_no:
        flash('Липсват данни за книга или читател.', 'danger')
        return redirect(url_for('transactions.borrow_page'))

    borrow_date = datetime.now()
    
    borrow_period_days = int(get_setting('borrow_period', 20))
    due_date = borrow_date.date() + timedelta(days=borrow_period_days)
    
    signature_filename = None

    if signature_data and signature_data.startswith('data:image/png;base64,'):
        try:
            header, encoded = signature_data.split(",", 1)
            img_data = base64.b64decode(encoded)
            
            safe_reader_no = reader_no.replace('/', '-').replace('\\', '-')
            safe_tom_no = book_tom_no.replace('/', '-').replace('\\', '-')
            
            signature_filename = f"{borrow_date.strftime('%Y%m%d%H%M%S')}_{safe_reader_no}_{safe_tom_no}.png"
            signatures_folder_path = os.path.join(current_app.root_path, '..', current_app.config['SIGNATURES_FOLDER'])
            signature_path = os.path.join(signatures_folder_path, signature_filename)
            
            with open(signature_path, "wb") as f:
                f.write(img_data)
        except Exception as e:
            flash(f'Грешка при запазване на подпис: {e}', 'danger')
            return redirect(url_for('transactions.borrow_page'))

    conn = get_db()
    try:
        sql = 'INSERT INTO borrows (book_tom_no, reader_no, borrow_date, due_date, signature_path) VALUES (?, ?, ?, ?, ?)'
        conn.execute(sql, (book_tom_no, reader_no, borrow_date, due_date, signature_filename))
        conn.commit()
    except Exception as e:
       flash(f'Грешка при запис в базата данни: {e}', 'danger')
       return redirect(url_for('transactions.borrow_page'))

    book = conn.execute('SELECT title FROM books WHERE tom_no = ?', (book_tom_no,)).fetchone()
    reader = conn.execute('SELECT full_name FROM readers WHERE reader_no = ?', (reader_no,)).fetchone()
    if book and reader:
        log_activity("Заемане на книга", f"Книга '{book['title']}' заета от '{reader['full_name']}'")
        
        formatted_due_date = format_date_dmy(due_date.isoformat())
        success_message = f"Книга '{book['title']}' трябва да бъде върната на {formatted_due_date}."
        flash(success_message, 'success manual-close')

    if next_action == 'borrow_another':
        return redirect(url_for('transactions.borrow_page', selected_reader=reader_no))
    else:
        return redirect(url_for('main.index'))

@transactions_bp.route('/return')
@login_required
def return_page():
    """Рендерира само празната страница, данните се зареждат динамично."""
    return render_template('return_book.html')

@transactions_bp.route('/api/borrowed_books')
@login_required
def api_borrowed_books():
    """API ендпойнт, който връща заетите книги като JSON."""
    conn = get_db()
    search_query = request.args.get('query', '').strip()
    
    base_sql = """
        SELECT b.tom_no, b.title, b.author, r.full_name, r.reader_no, br.due_date, br.borrow_id, br.signature_path 
        FROM borrows br 
        JOIN books b ON br.book_tom_no = b.tom_no 
        JOIN readers r ON br.reader_no = r.reader_no 
        WHERE br.return_date IS NULL 
        ORDER BY br.due_date
    """
    
    all_borrowed = conn.execute(base_sql).fetchall()
    
    if search_query:
        search_lower = search_query.lower()
        filtered_list = [
            dict(row) for row in all_borrowed 
            if search_lower in str(row['full_name']).lower() or search_lower in str(row['tom_no']).lower()
        ]
    else:
        filtered_list = [dict(row) for row in all_borrowed]
    
    for row in filtered_list:
        row['fine'] = calculate_fine(row['due_date'])
        row['due_date_formatted'] = format_date_dmy(row['due_date'])
        
    return jsonify(filtered_list)

@transactions_bp.route('/return_book/<int:borrow_id>', methods=['POST'])
@login_required
def return_book(borrow_id):
    conn = get_db()
    borrow_info_sql = "SELECT b.title, r.full_name, br.due_date FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no JOIN readers r ON br.reader_no = r.reader_no WHERE br.borrow_id = ?"
    borrow_info = conn.execute(borrow_info_sql, (borrow_id,)).fetchone()
    
    if borrow_info:
        return_datetime = datetime.now()
        final_fine = calculate_fine(borrow_info['due_date'])
        conn.execute('UPDATE borrows SET return_date = ?, fine_amount = ? WHERE borrow_id = ?', (return_datetime, final_fine, borrow_id))
        conn.commit()
        log_activity("Връщане на книга", f"Книга '{borrow_info['title']}' върната от '{borrow_info['full_name']}'")
        flash(f"Книга '{borrow_info['title']}' е върната.", "success")
        if final_fine > 0:
            flash(f"Начислена е глоба от {final_fine:.2f} лв. за просрочие.", "warning")
            
    return redirect(url_for('transactions.return_page'))

@transactions_bp.route('/pay_fine/<int:borrow_id>', methods=['POST'])
@login_required
def pay_fine(borrow_id):
    conn = get_db()
    borrow_info = conn.execute("SELECT reader_no FROM borrows WHERE borrow_id = ?", (borrow_id,)).fetchone()
    if borrow_info:
        conn.execute("UPDATE borrows SET fine_paid_date = ? WHERE borrow_id = ?", (date.today(), borrow_id))
        conn.commit()
        flash("Глобата е маркирана като платена.", "success")
        return redirect(url_for('readers.reader_details_page', reader_no=borrow_info['reader_no']))
        
    flash("Грешка при обработка на плащането.", "danger")
    return redirect(url_for('readers.readers_list_page'))

@transactions_bp.route('/signatures/<path:filename>')
def serve_signature(filename):
    directory = os.path.abspath(os.path.join(current_app.root_path, '..', current_app.config['SIGNATURES_FOLDER']))
    return send_from_directory(directory, filename)