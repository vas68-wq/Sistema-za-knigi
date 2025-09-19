from waitress import serve
from app import app
import app_extensions  # регистрира пачове и доп. маршрути

if __name__ == "__main__":
    serve(app, listen='127.0.0.1:5000')
