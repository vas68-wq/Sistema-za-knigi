# run.py

from application import create_app
from application.extensions import socketio
from application.database import init_db
import os

# Създаваме приложението, използвайки нашата "фабрика"
app = create_app()

if __name__ == '__main__':
    # Проверяваме дали базата данни съществува, преди да я инициализираме
    db_path = app.config['DATABASE']
    if not os.path.exists(db_path):
        with app.app_context():
            print(f"Базата данни не е намерена на '{db_path}'. Инициализирам нова база...")
            init_db()
    
    # Стартираме приложението чрез SocketIO, за да работят WebSockets
    # host='0.0.0.0' позволява достъп до сървъра от други устройства в мрежата (за таблета)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)