# application/extensions.py

from flask_socketio import SocketIO

# KOREКЦИЯ: async_mode='eventlet' е важен за правилното функциониране
# при deploy, както е било в оригиналния app.py
socketio = SocketIO(async_mode='eventlet')