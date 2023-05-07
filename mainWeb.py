import threading
from flask import Flask, render_template, request, url_for, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
import socketio
import eventlet
import psutil
import socket
import base64
import os

from Modules.logger import init_logger
from Modules.server import Server

app = Flask(__name__)
sio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", websocket=['websocket', 'polling'])


class Endpoints:
    def __init__(self, room, client_ip, hostname, logged_user, boot_time, version, login_time):
        self.id = room
        self.boot_time = boot_time
        self.ip_address = client_ip
        self.hostname = hostname
        self.logged_user = logged_user
        self.client_version = version
        self.connection_time = login_time

    def __repr__(self):
        return f"Endpoint({self.id}, {self.ip_address}, {self.hostname}, " \
               f"{self.logged_user}, {self.boot_time}, {self.client_version}, {self.connection_time})"


@sio.on('connect')
def handle_connect():
    print('Client connected')


# serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    serving_on = os.getenv('URL')
    hostname = socket.gethostname()
    server_ip = str(socket.gethostbyname(hostname))
    server_port = os.getenv('PORT')
    boot_time = last_boot()
    connected_stations = len(server.endpoints)

    kwargs = {
        "serving_on": serving_on,
        "server_ip": server_ip,
        "server_port": server_port,
        "boot_time": boot_time,
        "connected_stations": connected_stations,
        "endpoints": server.endpoints
    }

    return render_template('index.html', **kwargs)


@app.route('/controller', methods=['POST'])
def send_message():
    data = request.json.get('data')
    if data == 'screenshot':
        sio.emit('message', 'screenshot', room=room_id)
        return jsonify({'message': '.'})

    if data == 'anydesk':
        sio.emit('message', 'anydesk', room=room_id)
        return jsonify({'message': 'Anydesk message sent.'})

    if data == 'sysinfo':
        sio.emit('message', 'sysinfo', room=room_id)
        return jsonify({'message': 'Sysinfo message sent.'})

    if data == 'tasks':
        sio.emit('message', 'tasks', room=room_id)
        return jsonify({'message': 'Tasks message sent.'})

    if data == 'restart':
        sio.emit('message', 'restart', room=room_id)
        return jsonify({'message': 'Restart message sent.'})

    if data == 'local':
        sio.emit('message', 'local', room=room_id)
        return jsonify({'message': 'Local message sent.'})

    if data == 'update':
        sio.emit('message', 'update', room=room_id)
        return jsonify({'message': 'Update message sent.'})


@app.route('/shell_data', methods=['POST'])
def shell_data():
    global shell_target
    selected_row_data = request.get_json()
    if len(shell_target) > 0:
        shell_target = []
    shell_target = [selected_row_data['id'], selected_row_data['ip_address'], selected_row_data['hostname']]
    room_id = shell_target[0]
    ip = shell_target[1]
    hostname = shell_target[2]
    for endpoint in server.endpoints:
        if endpoint.ip == ip:
            print(f"Shell to: {endpoint.conn} | {ip} | {hostname}")

    # Return a response to the frontend, e.g. a success message
    return jsonify({'message': 'Selected row data received and saved successfully'})


def endpoint_exists(client_id, ip_address):
    for endpoint in endpoints:
        if client_id == endpoint.id or ip_address == endpoint.ip_address:
            return True
    return False


def last_boot():
    last_reboot = psutil.boot_time()
    bt = datetime.fromtimestamp(last_reboot).strftime('%d/%b/%y %H:%M:%S %p')
    return bt


def get_date() -> str:
    d = datetime.now().replace(microsecond=0)
    dt = str(d.strftime("%d/%b/%y %H:%M:%S"))
    return dt


if __name__ == '__main__':
    load_dotenv()
    hands_off_path = os.getenv('HANDSOFF_PATH')
    if not os.path.exists(hands_off_path):
        os.makedirs(hands_off_path)

    log_path = os.path.join(hands_off_path, 'server_log.txt')
    with open(log_path, 'w'):
        pass

    hostname = socket.gethostname()
    server_ip = str(socket.gethostbyname(hostname))
    server_port = os.getenv('PORT')
    server = Server(server_ip, server_port, log_path)
    logger = init_logger(log_path, __name__)
    shell_target = []
    threading.Thread(target=server.listener, name="Listener", daemon=True).start()
    sio.run(app, port=8000)

