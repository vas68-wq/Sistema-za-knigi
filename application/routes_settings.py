# application/routes_settings.py

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from .database import get_db
from .utils import admin_required, log_activity

settings_bp = Blueprint('settings', __name__, template_folder='templates')

@settings_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings_page():
    conn = get_db()
    
    if request.method == 'POST':
        settings_to_update = request.form
        try:
            for key, value in settings_to_update.items():
                conn.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
            conn.commit()
            log_activity("Промяна на настройки", f"Администратор '{session.get('username')}' обнови системните настройки.")
            flash('Настройките бяха успешно запазени!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Възникна грешка при запазване на настройките: {e}', 'danger')
        
        return redirect(url_for('settings.settings_page'))

    # Зареждаме всички настройки за показване във формата
    settings_data = conn.execute("SELECT key, value, description FROM settings").fetchall()
    settings = {row['key']: row for row in settings_data}
    
    return render_template('settings.html', settings=settings)