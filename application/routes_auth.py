# application/routes_auth.py

import sqlite3
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db
from .utils import log_activity, admin_required, login_required

# Създаване на Blueprint с име 'auth'
auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if not user:
            flash('Грешно потребителско име или парола.', 'danger')
            return render_template('login.html')

        # Проверка за заключен акаунт
        if user['lockout_until'] and datetime.now() < datetime.fromisoformat(user['lockout_until']):
            lockout_time_end = datetime.fromisoformat(user['lockout_until'])
            remaining_time = lockout_time_end - datetime.now()
            minutes, seconds = divmod(remaining_time.seconds, 60)
            flash(f'Акаунтът е временно заключен. Опитайте след {minutes} мин. и {seconds} сек.', 'warning')
            return render_template('login.html')
        
        # Нулиране на заключването, ако времето е минало
        if user['lockout_until'] and datetime.now() >= datetime.fromisoformat(user['lockout_until']):
            cursor.execute('UPDATE users SET failed_login_attempts = 0, lockout_until = NULL WHERE username = ?', (username,))
            conn.commit()
            user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if check_password_hash(user['password'], password):
            # Успешен вход
            cursor.execute('UPDATE users SET failed_login_attempts = 0, lockout_until = NULL WHERE username = ?', (username,))
            conn.commit()
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            log_activity("Вход в системата")
            flash('Влязохте успешно!', 'success')
            return redirect(url_for('main.index'))
        else:
            # Неуспешен вход
            new_attempts = user['failed_login_attempts'] + 1
            limit = current_app.config['LOGIN_ATTEMPTS_LIMIT']
            lockout_minutes = current_app.config['LOGIN_LOCKOUT_MINUTES']

            if new_attempts >= limit:
                lockout_until = datetime.now() + timedelta(minutes=lockout_minutes)
                cursor.execute('UPDATE users SET failed_login_attempts = ?, lockout_until = ? WHERE username = ?', (new_attempts, lockout_until, username))
                flash(f'Превишихте броя опити. Акаунтът е заключен за {lockout_minutes} минути.', 'danger')
            else:
                cursor.execute('UPDATE users SET failed_login_attempts = ? WHERE username = ?', (new_attempts, username))
                remaining_attempts = limit - new_attempts
                flash(f'Грешна парола. Остават ви {remaining_attempts} опита.', 'warning')
            
            conn.commit()
            return render_template('login.html')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    log_activity("Изход от системата")
    session.clear()
    flash('Излязохте успешно от системата.', 'info')
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/users')
@admin_required
def users_page():
    conn = get_db()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY username").fetchall()
    return render_template('users.html', users=users)

@auth_bp.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                         (username, generate_password_hash(password), role))
            conn.commit()
            log_activity("Създаден потребител", f"Потребител '{username}' с роля '{role}'")
            flash(f"Потребител '{username}' е създаден успешно.", "success")
            return redirect(url_for('auth.users_page'))
        except sqlite3.IntegrityError:
            flash("Потребителското име вече съществува.", "danger")
            return render_template('add_user.html'), 400
    return render_template('add_user.html')

@auth_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db()
    if user_id == session.get('user_id'):
        flash("Не можете да изтриете собствения си акаунт.", "warning")
        return redirect(url_for('auth.users_page'))
    
    user_to_delete = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_to_delete:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        log_activity("Изтрит потребител", f"Потребител '{user_to_delete['username']}'")
        flash(f"Потребител '{user_to_delete['username']}' е изтрит.", "success")
    return redirect(url_for('auth.users_page'))

@auth_bp.route('/activity_log')
@login_required
def activity_log_page():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    conn = get_db()
    total_logs = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
    log_entries = conn.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT ? OFFSET ?",
                               (per_page, offset)).fetchall()
    total_pages = (total_logs + per_page - 1) // per_page
    return render_template('activity_log.html', log_entries=log_entries, page=page, total_pages=total_pages)