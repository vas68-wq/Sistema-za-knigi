import threading
import webview
from waitress import serve
from app import app
import app_extensions  # важно: регистрира пачове и доп. маршрути

def run_server():
    serve(app, listen='127.0.0.1:5000')

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    webview.create_window("Библиотечна Система", "http://127.0.0.1:5000", width=1280, height=800)
    webview.start()
