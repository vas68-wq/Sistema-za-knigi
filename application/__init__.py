# application/__init__.py

import os
from flask import Flask
from datetime import date

# КОРЕКЦИЯ: eventlet.monkey_patch() трябва да е абсолютно първото нещо,
# което се изпълнява, дори преди импортирането на Flask.
import eventlet
eventlet.monkey_patch()

def create_app(test_config=None):
    """
    Фабрика за създаване и конфигуриране на Flask приложението.
    """
    # 1. Създаване на инстанция на приложението
    # instance_relative_config=True казва на Flask да търси конфигурационни
    # файлове спрямо 'instance' папката.
    app = Flask(__name__, instance_relative_config=True)

    # 2. Зареждане на конфигурацията
    # Зарежда конфигурацията от ../config.py
    app.config.from_object('config.Config')

    if test_config is None:
        # Зареждане на конфигурация от instance folder, ако съществува
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Зареждане на тестова конфигурация, ако е подадена
        app.config.from_mapping(test_config)
    
    # 3. Създаване на необходимите директории (ако не съществуват)
    for folder_key in ['SIGNATURES_FOLDER', 'COVERS_FOLDER']:
        folder_path = os.path.join(app.instance_path, '..', app.config[folder_key])
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # 4. Инициализация на разширенията (база данни, сокети)
    from . import database
    database.init_app(app)
    
    from .extensions import socketio
    socketio.init_app(app)

    # 5. Регистрация на Blueprints (модулите с маршрути)
    from .routes_auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes_books import books_bp
    app.register_blueprint(books_bp)

    from .routes_readers import readers_bp
    app.register_blueprint(readers_bp)

    from .routes_transactions import transactions_bp
    app.register_blueprint(transactions_bp)

    from .routes_reports import reports_bp
    app.register_blueprint(reports_bp)

    from .routes_public import main_bp, public_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(public_bp)
    
    from .websockets import ws_bp
    app.register_blueprint(ws_bp)

    # КОРЕКЦИЯ: Регистрираме новия модул за настройки
    from .routes_settings import settings_bp
    app.register_blueprint(settings_bp)

    # 6. Добавяне на филтри и контекст процесори към Jinja2
    from .utils import format_date_dmy, calculate_fine
    app.jinja_env.filters['dmy'] = format_date_dmy
    app.jinja_env.filters['format_date_dmy'] = format_date_dmy
    
    # Добавяме глобални променливи/функции, които да са достъпни във всички шаблони
    @app.context_processor
    def inject_global_vars():
        return {
            'current_year': date.today().year,
            'calculate_fine': calculate_fine
        }

    return app