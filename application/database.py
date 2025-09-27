# application/database.py

import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def execute_sql_from_file(db, filename):
    """Изпълнява SQL команди от файл."""
    with current_app.open_resource(filename) as f:
        db.executescript(f.read().decode('utf8'))

def get_db():
    """
    Получава връзка към базата данни. Ако връзката не съществува в
    контекста на заявката ('g'), тя се създава и съхранява там.
    """
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row

        # КОРЕКЦИЯ: Проверяваме и създаваме таблицата 'settings' ако липсва
        cursor = g.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if cursor.fetchone() is None:
            # Изпълняваме само частта от схемата, която създава новата таблица
            cursor.executescript("""
                CREATE TABLE settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT
                );
                INSERT OR IGNORE INTO settings (key, value, description) VALUES
                    ('borrow_period', '20', 'Срок за заемане на книга (в дни)'),
                    ('fine_per_day', '0.10', 'Глоба за просрочие на ден (в лв.)'),
                    ('books_per_page', '10', 'Брой книги, показвани на страница');
            """)
            g.db.commit()
            print("--- INFO: 'settings' table created and populated successfully. ---")

    return g.db

def close_db(e=None):
    """
    Затваря връзката към базата данни, ако съществува.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Изчиства съществуващите данни и създава новите таблици.
    """
    db = get_db()
    execute_sql_from_file(db, 'database_schema.sql')

@click.command('init-db')
@with_appcontext
def init_db_command():
    """
    Дефинира команда за командния ред 'flask init-db', която
    изпълнява 'init_db' функцията.
    """
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """
    Регистрира функциите за управление на базата данни в Flask приложението.
    """
    # Казва на Flask да извика 'close_db' след връщане на отговор
    app.teardown_appcontext(close_db)
    # Добавя новата команда, която може да бъде извикана с 'flask init-db'
    app.cli.add_command(init_db_command)