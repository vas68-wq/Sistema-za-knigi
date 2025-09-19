# application/websockets.py

from flask import Blueprint, render_template, request
from flask_socketio import emit
from .extensions import socketio

ws_bp = Blueprint('ws', __name__, template_folder='templates')

# --- Управление на WebSocket клиенти ---
clients = {
    'tablet_sid': None
}

def update_tablet_status():
    """Изпраща актуалния статус на таблета до всички клиенти."""
    is_connected = clients['tablet_sid'] is not None
    # 'broadcast=True' изпраща съобщението до всички свързани клиенти
    emit('tablet_status_update', {'connected': is_connected}, broadcast=True)
    print(f"Status update sent: Tablet connected = {is_connected}")

@ws_bp.route('/tablet')
def tablet_page():
    return render_template('tablet.html')

# --- WEBSOCKET ЛОГИКА ---

@socketio.on('connect')
def on_connect():
    print(f"Client connected: {request.sid}")
    # Когато нов клиент се свърже, му изпращаме актуалния статус на таблета
    is_connected = clients['tablet_sid'] is not None
    emit('tablet_status_update', {'connected': is_connected})


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")
    if clients.get('tablet_sid') == sid:
        clients['tablet_sid'] = None
        print("Tablet client disconnected.")
        # Когато таблетът се разкачи, уведомяваме всички останали
        update_tablet_status()

@socketio.on('register_client')
def on_register_client(data):
    client_type = data.get('type')
    if client_type == 'tablet':
        clients['tablet_sid'] = request.sid
        print(f"Tablet client registered: {request.sid}")
        # Когато таблетът се регистрира, уведомяваме всички
        update_tablet_status()

@socketio.on('request_signature')
def on_request_signature(data):
    tablet_sid = clients.get('tablet_sid')
    if tablet_sid:
        # Добавяме ID-то на браузъра към данните, преди да ги изпратим
        data['browser_sid'] = request.sid
        print(f"Forwarding signature request from browser {request.sid} to tablet {tablet_sid}")
        emit('show_signature_pad', data, to=tablet_sid)
    else:
        print("Signature request received, but no tablet is connected.")
        emit('no_tablet_available', to=request.sid)

@socketio.on('submit_signature')
def on_submit_signature(data):
    # Извличаме ID-то на браузъра, на който да върнем подписа
    browser_to_notify = data.get('browser_sid')
    if browser_to_notify:
        print(f"Signature received from tablet, forwarding to browser {browser_to_notify}")
        emit('signature_received', {'signature': data.get('signature')}, to=browser_to_notify)
    else:
        print("Signature received from tablet, but could not determine which browser to send it to.")