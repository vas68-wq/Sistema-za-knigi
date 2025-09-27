# application/routes_readers.py

import csv
import io
from datetime import date
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
)
from .database import get_db
from .utils import login_required, log_activity, clean_date, clean_int

readers_bp = Blueprint('readers', __name__, template_folder='templates')

def add_new_entry(table_name, entry_value):
    if not entry_value or not entry_value.strip():
        return None
    formatted_value = entry_value.strip().capitalize()
    conn = get_db()
    query = f"SELECT name FROM {table_name} WHERE name = ? COLLATE NOCASE"
    exists = conn.execute(query, (formatted_value,)).fetchone()
    if not exists:
        conn.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (formatted_value,))
        conn.commit()
    return formatted_value

@readers_bp.route('/readers')
@login_required
def readers_list_page():
    """Рендерира страницата, като подава текущата година към шаблона."""
    current_year = date.today().year
    return render_template('readers_list.html', current_year=current_year)

@readers_bp.route('/api/readers')
@login_required
def api_readers():
    """API ендпойнт, който връща читателите като JSON."""
    conn = get_db()
    search_query = request.args.get('query', '').strip().lower()
    
    all_readers_sql = "SELECT * FROM readers ORDER BY full_name"
    all_readers = conn.execute(all_readers_sql).fetchall()

    if search_query:
        filtered_list = [
            dict(row) for row in all_readers
            if search_query in str(row['full_name']).lower() or search_query in str(row['reader_no']).lower()
        ]
    else:
        filtered_list = [dict(row) for row in all_readers]
        
    return jsonify(filtered_list)


@readers_bp.route('/reader/<string:reader_no>')
@login_required
def reader_details_page(reader_no):
    conn = get_db()
    reader = conn.execute('SELECT * FROM readers WHERE reader_no = ?', (reader_no,)).fetchone()
    if not reader:
        flash('Читател не е намерен!', 'danger')
        return redirect(url_for('readers.readers_list_page'))

    current_borrows = conn.execute("SELECT b.title, br.borrow_date, br.due_date, b.tom_no FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no WHERE br.reader_no = ? AND br.return_date IS NULL ORDER BY br.due_date", (reader_no,)).fetchall()
    unpaid_fines = conn.execute("SELECT b.title, br.return_date, br.fine_amount, br.borrow_id, b.tom_no FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no WHERE br.reader_no = ? AND br.fine_amount > 0 AND br.fine_paid_date IS NULL ORDER BY br.return_date", (reader_no,)).fetchall()
    borrow_history = conn.execute("SELECT b.title, br.borrow_date, br.return_date, br.fine_amount, br.fine_paid_date, b.tom_no FROM borrows br JOIN books b ON br.book_tom_no = b.tom_no WHERE br.reader_no = ? ORDER BY br.borrow_date DESC", (reader_no,)).fetchall()

    return render_template('reader_details.html', reader=reader, current_borrows=current_borrows, unpaid_fines=unpaid_fines, borrow_history=borrow_history)

@readers_bp.route('/add_reader', methods=['POST'])
@login_required
def add_reader_action():
    reader_data = request.form
    
    final_profession = add_new_entry('professions', reader_data.get('profession'))
    final_education = add_new_entry('educations', reader_data.get('education'))

    try:
        conn = get_db()
        current_year_val = date.today().year
        sql = "INSERT INTO readers (reader_no, full_name, city, address, phone, email, profession, education, gender, is_under_14, registration_date, last_registration_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE, ?)"
        params = (
            reader_data['reader_no'], reader_data['full_name'], reader_data['city'], 
            reader_data['address'], reader_data['phone'], reader_data['email'], 
            final_profession, final_education, reader_data['gender'], 
            1 if 'is_under_14' in reader_data else 0, current_year_val
        )
        conn.execute(sql, params)
        conn.commit()
        log_activity("Регистриран читател", f"Читател '{reader_data['full_name']}' (№ {reader_data['reader_no']})")
        flash('Читателят е регистриран успешно!', 'success')
    except Exception as e:
        flash(f'Грешка при регистрация на читател: {e}', 'danger')
        
    return redirect(url_for('readers.readers_list_page'))

@readers_bp.route('/edit_reader/<string:reader_no>', methods=['GET', 'POST'])
@login_required
def edit_reader_page(reader_no):
    conn = get_db()
    if request.method == 'POST':
        form_data = request.form
        
        profession_input = form_data.get('new_profession') or form_data.get('profession_select')
        education_input = form_data.get('new_education') or form_data.get('education_select')

        final_profession = add_new_entry('professions', profession_input)
        final_education = add_new_entry('educations', education_input)

        sql = "UPDATE readers SET full_name = ?, city = ?, address = ?, phone = ?, email = ?, profession = ?, education = ?, gender = ?, is_under_14 = ? WHERE reader_no = ?"
        params = (
            form_data['full_name'], form_data['city'], form_data['address'],
            form_data['phone'], form_data['email'], final_profession, final_education,
            form_data['gender'], 1 if 'is_under_14' in form_data else 0, reader_no
        )
        conn.execute(sql, params)
        conn.commit()
        log_activity("Редактиран читател", f"Читател '{form_data['full_name']}' (№ {reader_no})")
        flash("Данните за читателя са обновени.", "success")
        return redirect(url_for('readers.readers_list_page'))
        
    reader = conn.execute('SELECT * FROM readers WHERE reader_no = ?', (reader_no,)).fetchone()
    professions = conn.execute('SELECT * FROM professions ORDER BY name').fetchall()
    educations = conn.execute('SELECT * FROM educations ORDER BY name').fetchall()
    return render_template('edit_reader.html', reader=reader, professions=professions, educations=educations)

@readers_bp.route('/delete_reader/<string:reader_no>', methods=['POST'])
@login_required
def delete_reader(reader_no):
    conn = get_db()
    reader = conn.execute('SELECT full_name FROM readers WHERE reader_no = ?', (reader_no,)).fetchone()
    borrowed_books = conn.execute('SELECT 1 FROM borrows WHERE reader_no = ? AND return_date IS NULL', (reader_no,)).fetchone()
    
    if borrowed_books:
        flash(f"ГРЕШКА: Читателят '{reader['full_name']}' има незавърнати книги и не може да бъде изтрит.", "danger")
    else:
        conn.execute('DELETE FROM readers WHERE reader_no = ?', (reader_no,))
        conn.commit()
        if reader:
            log_activity("Изтрит читател", f"Читател '{reader['full_name']}' (№ {reader_no})")
            flash(f"Читател '{reader['full_name']}' е изтрит.", 'success')
            
    return redirect(url_for('readers.readers_list_page'))

@readers_bp.route('/renew_reader/<string:reader_no>', methods=['POST'])
@login_required
def renew_reader(reader_no):
    conn = get_db()
    current_year_val = date.today().year
    conn.execute("UPDATE readers SET last_registration_year = ? WHERE reader_no = ?", (current_year_val, reader_no))
    conn.commit()
    reader = conn.execute('SELECT full_name FROM readers WHERE reader_no = ?', (reader_no,)).fetchone()
    if reader:
        log_activity("Подновяване", f"Подновен абонамент за '{reader['full_name']}' (№ {reader_no}) за {current_year_val} г.")
        flash(f"Абонаментът на '{reader['full_name']}' е подновен за {current_year_val} г.", 'success')
    return redirect(url_for('readers.readers_list_page'))

@readers_bp.route('/import_readers', methods=['GET', 'POST'])
@login_required
def import_readers_page():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or file.filename == '':
            flash("Моля, изберете CSV файл за качване.", "warning")
            return redirect(request.url)
        try:
            file_content = file.stream.read()
            try:
                decoded_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_content = file_content.decode('windows-1251')
                
            dialect = csv.Sniffer().sniff(decoded_content.splitlines()[0])
            stream = io.StringIO(decoded_content, newline=None)
            csv_reader = csv.reader(stream, dialect)
            
            conn = get_db()
            cursor = conn.cursor()
            next(csv_reader) # Skip header
            
            readers_added = 0
            for row in csv_reader:
                if len(row) == 11:
                    reader_no, full_name, city, address, phone, email, profession, education, gender, registration_date, is_under_14 = row
                    
                    is_under_14_bool = 1 if is_under_14.lower() in ['да', 'yes', 'true', '1'] else 0
                    cleaned_date = clean_date(registration_date)
                    reg_year = clean_int(cleaned_date[:4]) if cleaned_date else date.today().year
                    
                    final_profession = add_new_entry('professions', profession)
                    final_education = add_new_entry('educations', education)

                    sql = "INSERT OR IGNORE INTO readers (reader_no, full_name, city, address, phone, email, profession, education, gender, registration_date, is_under_14, last_registration_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    params = (reader_no, full_name, city, address, phone, email, final_profession, final_education, gender, cleaned_date, is_under_14_bool, reg_year)
                    cursor.execute(sql, params)
                    readers_added += 1
            conn.commit()
            log_activity("Импорт на читатели", f"Импортирани са {readers_added} читатели.")
            flash(f"Импортирането завърши. Добавени са {readers_added} читатели.", "success")
            return redirect(url_for('readers.readers_list_page'))
        except Exception as e:
            flash(f"Възникна грешка при импортирането: {e}", "danger")
            return redirect(url_for('readers.import_readers_page'))
            
    return render_template('import_readers.html')