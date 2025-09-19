# application/database.py

import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash

def get_db():
    """
    Отваря нова връзка с базата данни, ако все още няма такава за текущия контекст.
    """
    if 'db' not in g:
        # КОРЕКЦИЯ: Премахваме detect_types, за да спрем автоматичното преобразуване на дати,
        # което причинява срив при повредени данни.
        g.db = sqlite3.connect(
            current_app.config['DATABASE']
            # detect_types=sqlite3.PARSE_DECLTYPES -> ТОВА Е ПРЕМАХНАТО
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """
    Затваря връзката с базата данни, ако съществува.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Изчиства съществуващите данни и създава нови таблици.
    """
    if not os.path.exists(current_app.config['DATABASE']):
        db = get_db()
        # Понеже database_schema.sql се намира в основната директория, трябва да се върнем една папка назад.
        schema_path = os.path.join(current_app.root_path, '..', 'database_schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        
        # Създаване на администраторски потребител и първоначални данни
        cursor = db.cursor()
        username = 'admin'
        password = 'admin'
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, 'admin'))
        
        initial_genres = []
        initial_professions = []
        initial_educations = []

        for item in initial_genres:
            cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (item,))
        for item in initial_professions:
            cursor.execute("INSERT OR IGNORE INTO professions (name) VALUES (?)", (item,))
        for item in initial_educations:
            cursor.execute("INSERT OR IGNORE INTO educations (name) VALUES (?)", (item,))
            
        db.commit()
        print("Базата данни е инициализирана успешно.")


def init_app(app):
    """
    Регистрира функциите за управление на базата данни в Flask приложението.
    """
    app.teardown_appcontext(close_db)