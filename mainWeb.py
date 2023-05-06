from flask import Flask, render_template, request, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
import socketio
import psutil
import socket
import base64
import os


app = Flask(__name__)
sio = SocketIO(app, async_mode='threading', cors_allowed_origins="*",
               transports=['websocket', 'polling'])


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
    connected_stations = len(endpoints)

    kwargs = {
        "serving_on": serving_on,
        "server_ip": server_ip,
        "server_port": server_port,
        "boot_time": boot_time,
        "connected_stations": connected_stations,
        "endpoints": endpoints
    }
    return render_template('index.html', **kwargs)


@app.route('/shell_data', methods=['POST'])
def shell_data():
    global shell_target
    selected_row_data = request.get_json()
    if len(shell_target) > 0:
        shell_target = []
    shell_target = [selected_row_data['id'], selected_row_data['ip_address'], selected_row_data['hostname']]
    room_id = shell_target[0]
    hostname = shell_target[2]
    print(f"Shell to: {room_id} | {selected_row_data['ip_address']} | {hostname}")

    # Return a response to the frontend, e.g. a success message
    return jsonify({'message': 'Selected row data received and saved successfully'})


@sio.on('client_info')
def handle_client_info(client_info):
    client_id = request.sid
    if endpoint_exists(client_id, client_info['ip_address']):
        return False

    fresh_endpoint = Endpoints(client_id,
                               client_info["ip_address"],
                               client_info["hostname"],
                               client_info["logged_user"],
                               client_info["boot_time"],
                               client_info['client_version'],
                               get_date())

    history[get_date()] = fresh_endpoint
    endpoints.append(fresh_endpoint)
    for count, endpoint in enumerate(endpoints):
        if count == 0:
            count += 1

    #     print(f"#{count} | ID: {endpoint.id} | IP: {endpoint.ip_address} | "
    #           f"Hostname: {endpoint.hostname} | "
    #           f"Logged User: {endpoint.logged_user} | "
    #           f"Boot Time: {endpoint.boot_time} | "
    #           f"Client_Version: {endpoint.client_version}")
    #
    # for t, endpoint in history.items():
    #     print(f"History\n{t} | IP: {endpoint.ip_address} | "
    #           f"Hostname: {endpoint.hostname} | "
    #           f"Logged User: {endpoint.logged_user} | "
    #           f"Boot Time: {endpoint.boot_time} | "
    #           f"Client_Version: {endpoint.client_version}")


@sio.on('connect')
def handle_connect():
    print('Client connected')


@sio.on('message')
def handle_message(message):
    print('Received message: ' + message)


@app.route('/controller', methods=['POST'])
def send_message():
    data = request.json.get('data')
    if data == 'screenshot':
        room_id = shell_target[0]
        sio.emit('message', 'screenshot', room=room_id)
        return jsonify({'message': 'Screenshot message sent.'})

    elif data == 'anydesk':
        room_id = list(shell_target.keys())[0]
        sio.emit('message', 'anydesk', room=room_id)
        return jsonify({'message': 'Anydesk message sent.'})

    elif data == 'sysinfo':
        room_id = list(shell_target.keys())[0]
        sio.emit('message', 'sysinfo', room=room_id)
        return jsonify({'message': 'Sysinfo message sent.'})

    elif data == 'tasks':
        room_id = list(shell_target.keys())[0]
        sio.emit('message', 'tasks', room=room_id)
        return jsonify({'message': 'Tasks message sent.'})

    elif data == 'restart':
        room_id = list(shell_target.keys())[0]
        sio.emit('message', 'restart', room=room_id)
        return jsonify({'message': 'Restart message sent.'})

    elif data == 'local':
        room_id = list(shell_target.keys())[0]
        sio.emit('message', 'local', room=room_id)
        return jsonify({'message': 'Local message sent.'})

    elif data == 'update':
        room_id = list(shell_target.keys())[0]
        sio.emit('message', 'update', room=room_id)
        return jsonify({'message': 'Update message sent.'})


@sio.on('file_upload')
def handle_file_upload(data):
    hostname = list(shell_target.values())[0][selected_row_data['ip_address']]
    path = fr"c:/HandsOff/{hostname}"
    if not os.path.exists(path):
        os.makedirs(path)

    # Get the file data from the data dictionary
    encoded_file_data = data['file_data']

    # Decode the file data from base64
    file_data = base64.b64decode(encoded_file_data.encode('utf-8'))

    # Save the file to disk
    filename = data['filename']
    with open(filename, 'wb') as f:
        f.write(file_data)

    # Send a response to the client
    emit('file_uploaded', {'status': 'OK'})


@sio.on('disconnect')
def handle_disconnect():
    global shell_target, endpoints
    new_endpoints = []
    for target, endpoint in zip(shell_target, endpoints):
        if target != endpoint.id:
            new_endpoints.append(endpoint)
    endpoints = new_endpoints
    print('Client disconnected')


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
    hands_off_path = 'c:\\HandsOff'
    if not os.path.exists(hands_off_path):
        os.makedirs(hands_off_path)

    endpoints = []
    history = {}
    shell_target = []
    sio.run(app, allow_unsafe_werkzeug=True)
