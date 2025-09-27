# application/utils.py

import re
from datetime import date, timedelta, datetime
from functools import wraps
from flask import current_app, session, redirect, url_for, flash, g
from .database import get_db

# --- НОВА ФУНКЦИЯ ЗА ЧЕТЕНЕ НА НАСТРОЙКИТЕ ---
def get_setting(key, default=None):
    """
    Извлича стойност на настройка от базата данни.
    Използва 'g' обекта на Flask за кеширане на настройките в рамките на една заявка.
    """
    if 'settings' not in g:
        conn = get_db()
        settings_data = conn.execute('SELECT key, value FROM settings').fetchall()
        g.settings = {row['key']: row['value'] for row in settings_data}
    
    return g.settings.get(key, default)


# --- Помощни функции за форматиране и почистване ---

def format_date_dmy(value):
    """
    Форматира дата към 'dd.mm.YYYY HH:MM:SS' или 'dd.mm.YYYY'.
    Тази версия е изключително устойчива на грешни или повредени данни.
    """
    if not value:
        return ""

    if isinstance(value, bytes):
        try:
            value = value.decode('utf-8')
        except UnicodeDecodeError:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Не може да се декодира byte string: {value!r}")
            return repr(value)

    date_obj = None
    try:
        if isinstance(value, datetime):
            date_obj = value
        elif isinstance(value, date):
            date_obj = datetime.combine(value, datetime.min.time())
        else:
            str_value = str(value)
            if '.' in str_value:
                str_value = str_value.split('.')[0]
            
            possible_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
            for fmt in possible_formats:
                try:
                    date_obj = datetime.strptime(str_value, fmt)
                    break
                except ValueError:
                    continue
            
            if not date_obj:
                raise ValueError("Нито един от форматите не съвпадна")

    except (ValueError, TypeError):
        print(f"ПРЕДУПРЕЖДЕНИЕ: Не може да се форматира стойност за дата: '{value}'")
        return value

    if date_obj.hour == 0 and date_obj.minute == 0 and date_obj.second == 0:
        return date_obj.strftime('%d.%m.%Y')
    else:
        return date_obj.strftime('%d.%m.%Y %H:%M:%S')

def allowed_file(filename):
    """Проверява дали разширението на файла е позволено."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def calculate_fine(due_date_str):
    """Изчислява глоба за просрочена книга. Устойчива версия."""
    if not due_date_str:
        return 0.0
    try:
        due_date = None
        if isinstance(due_date_str, date):
            due_date = due_date_str
        elif isinstance(due_date_str, datetime):
            due_date = due_date_str.date()
        else:
            date_part = str(due_date_str).split(" ")[0]
            due_date = datetime.strptime(date_part, '%Y-%m-%d').date()

        if date.today() > due_date:
            overdue_days = (date.today() - due_date).days
            # ПРОМЯНА: Използваме стойността от настройките
            fine_per_day = float(get_setting('fine_per_day', 0.10))
            return round(overdue_days * fine_per_day, 2)
    except (ValueError, TypeError):
        print(f"ПРЕДУПРЕЖДЕНИЕ: Невалидна дата за изчисляване на глоба: '{due_date_str}'")
        return 0.0
    return 0.0

def clean_price(p_str):
    """Почиства и преобразува стойност към float за цена."""
    if isinstance(p_str, (int, float)):
        return p_str
    if not p_str:
        return 0.0
    c_str = re.sub(r'[^\d,.]', '', str(p_str)).replace(',', '.')
    try:
        return float(c_str)
    except (ValueError, TypeError):
        return 0.0

def clean_date(d_str):
    """Почиства и преобразува стринг към дата във формат 'YYYY-MM-DD'."""
    if not d_str:
        return date.today().strftime('%Y-%m-%d')
    d_str = str(d_str).strip()
    m_map = {
        'януари': '01', 'февруари': '02', 'март': '03', 'април': '04', 'май': '05',
        'юни': '06', 'юли': '07', 'август': '08', 'септември': '09',
        'октомври': '10', 'ноември': '11', 'декември': '12'
    }
    try:
        parts = re.split(r'[.\s/-]', d_str)
        if len(parts) == 3:
            day, m_str, y_str = parts
            month = m_map.get(m_str.lower(), m_str)
            year = f"20{y_str}" if len(y_str) == 2 else y_str
            if month and month.isdigit() and year.isdigit() and day.isdigit():
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except Exception:
        pass
    try:
        return datetime.strptime(d_str, '%Y-%m-%d').strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return date.today().strftime('%Y-%m-%d')

def clean_int(i_str):
    """Почиства и преобразува стринг към цяло число."""
    if isinstance(i_str, int):
        return i_str
    if not i_str:
        return None
    c_str = re.sub(r'\D', '', str(i_str))
    if not c_str:
        return None
    try:
        return int(c_str)
    except (ValueError, TypeError):
        return None

# --- Декоратори за аутентикация и ауторизация ---

def login_required(f):
    """Декоратор, който изисква потребителят да е влязъл в системата."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Декоратор, който изисква потребителят да е администратор."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_page'))
        if session.get('role') != 'admin':
            flash('Нямате необходимите права за достъп до тази страница.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Логиране на дейности ---

def log_activity(action, details=""):
    """Записва дейност в базата данни."""
    conn = get_db()
    current_timestamp = datetime.now()
    conn.execute(
        "INSERT INTO activity_log (timestamp, username, action, details) VALUES (?, ?, ?, ?)",
        (current_timestamp, session.get('username', 'System'), action, details)
    )
    conn.commit()