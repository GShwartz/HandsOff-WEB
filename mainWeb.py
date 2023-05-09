import threading
import time
import PIL
from flask import Flask, render_template, request, url_for, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
import PIL.ImageTk
import PIL.Image
import socketio
import eventlet
import psutil
import shutil
import socket
import base64
import queue
import glob
import os

from Modules.logger import init_logger
from Modules.server import Server


class Endpoints:
    def __init__(self, conn, client_mac, ip, ident, user, client_version, boot_time, connection_time):
        self.boot_time = boot_time
        self.conn = conn
        self.client_mac = client_mac
        self.ip = ip
        self.ident = ident
        self.user = user
        self.client_version = client_version
        self.connection_time = connection_time

    def __repr__(self):
        return f"Endpoint({self.conn}, {self.client_mac}, " \
               f"{self.ip}, {self.ident}, {self.user}, " \
               f"{self.client_version}, {self.boot_time}, {self.connection_time})"


class Screenshot:
    def __init__(self, path, log_path, endpoint):
        self.images = []
        self.endpoint = endpoint
        self.path = path
        self.log_path = log_path
        self.screenshot_path = fr"{self.path}\{self.endpoint.ident}"
        self.logger = init_logger(self.log_path, __name__)

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def make_dir(self):
        try:
            os.makedirs(self.screenshot_path)

        except FileExistsError:
            self.logger.debug(f"{self.screenshot_path} Exists.")
            pass

    def get_file_name(self):
        try:
            self.filename = self.endpoint.conn.recv(1024)
            self.filename = str(self.filename).strip("b'")
            self.endpoint.conn.send("Filename OK".encode())
            self.screenshot_file_path = os.path.join(self.screenshot_path, self.filename)

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def get_file_size(self):
        try:
            self.size = self.endpoint.conn.recv(4)
            # self.endpoint.conn.send("OK".encode())
            self.size = self.bytes_to_number(self.size)

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def get_file_content(self):
        current_size = 0
        buffer = b""
        try:
            self.logger.debug(f"Opening {self.filename} for writing...")
            with open(self.screenshot_file_path, 'wb') as file:
                self.logger.debug(f"Fetching file content...")
                while current_size < self.size:
                    data = self.endpoint.conn.recv(1024)
                    if not data:
                        break

                    if len(data) + current_size > self.size:
                        data = data[:self.size - current_size]

                    buffer += data
                    current_size += len(data)
                    file.write(data)

            self.logger.info(f"get_file_content completed.")

        except FileExistsError:
            self.logger.debug(f"Passing file exists error...")
            pass

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def confirm(self):
        try:
            self.logger.debug(f"Waiting for answer from client...")
            self.ans = self.endpoint.conn.recv(1024).decode()
            self.logger.debug(f"{self.endpoint.ip}: {self.ans}")

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}.")
            self.logger.debug(f"Calling app.server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def finish(self):
        try:
            self.logger.debug(f"Sorting jpg files by creation time...")
            self.images = glob.glob(fr"{self.screenshot_path}\*.jpg")
            self.images.sort(key=os.path.getmtime)
            self.logger.debug(f"Opening latest screenshot...")
            self.sc = PIL.Image.open(self.images[-1])
            self.logger.debug(f"Resizing to 650x350...")
            self.sc_resized = self.sc.resize((650, 350))
            self.last_screenshot = os.path.basename(self.images[-1])
            self.last_sc_path = os.path.join(self.screenshot_path, self.last_screenshot)
            os.startfile(self.last_sc_path)
            self.logger.info(f"Screenshot completed.")

        except IndexError:
            pass

    def run(self):
        self.logger.info(f"Running screenshot...")
        self.logger.debug(f"Calling make_dir...")
        self.make_dir()

        try:
            self.logger.debug(f"Sending screen command to client...")
            self.endpoint.conn.send('screen'.encode())

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}.")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint}...")
            server.remove_lost_connection(self.endpoint)
            return False

        self.logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        self.logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        self.logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        self.finish()


class Sysinfo:
    def __init__(self, path, log_path, endpoint):
        self.endpoint = endpoint
        self.app_path = path
        self.log_path = log_path
        self.path = os.path.join(self.app_path, self.endpoint.ident)

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def make_dir(self):
        try:
            os.makedirs(self.path)

        except FileExistsError:
            logger.debug(f"{self.path} exists.")
            pass

    def get_file_name(self):
        try:
            logger.debug(f"Sending si command to {self.endpoint.conn}...")
            self.endpoint.conn.send('si'.encode())
            logger.debug(f"Waiting for filename from {self.endpoint.conn}...")
            self.filename = self.endpoint.conn.recv(1024).decode()
            logger.debug(f"Sending confirmation to {self.endpoint.conn}...")
            self.endpoint.conn.send("OK".encode())
            logger.debug(f"{self.endpoint.ip}: {self.filename}")
            self.file_path = os.path.join(self.path, self.filename)
            logger.debug(f"File path: {self.file_path}")

        except (WindowsError, socket.error) as e:
            logger.debug(f"Connection error: {e}")
            logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def get_file_size(self):
        try:
            logger.debug(f"Waiting for filesize from {self.endpoint.ip}...")
            self.size = self.endpoint.conn.recv(4)
            logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
            self.endpoint.conn.send("OK".encode())
            self.size = self.bytes_to_number(self.size)
            logger.debug(f"File size: {self.size}")

        except (WindowsError, socket.error) as e:
            logger.debug(f"Connection error: {e}")
            logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def get_file_content(self):
        current_size = 0
        buffer = b""
        try:
            logger.debug(f"Receiving file content from {self.endpoint.ip}...")
            with open(self.file_path, 'wb') as tsk_file:
                while current_size < self.size:
                    data = self.endpoint.conn.recv(1024)
                    if not data:
                        break

                    if len(data) + current_size > self.size:
                        data = data[:self.size - current_size]

                    buffer += data
                    current_size += len(data)
                    tsk_file.write(data)

        except (WindowsError, socket.error) as e:
            logger.debug(f"Connection error: {e}")
            logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def confirm(self):
        try:
            logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
            self.endpoint.conn.send(f"Received file: {self.filename}\n".encode())

        except (WindowsError, socket.error) as e:
            logger.debug(f"Connection error: {e}")
            logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def file_validation(self):
        try:
            logger.debug(f"Running validation on {self.file_path}...")
            with open(self.file_path, 'r') as file:
                data = file.read()

            return True

        except Exception as e:
            logger.debug(f"File validation Error: {e}")
            return False

    def display_text(self):
        logger.info(f"Running display_text...")
        os.startfile(self.file_path)

    def run(self):
        logger.info(f"Running Sysinfo...")
        logger.debug(f"Calling make_dir...")
        self.make_dir()
        logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        logger.debug(f"Calling confirm...")
        self.confirm()
        logger.debug(f"Calling file_validation...")
        self.file_validation()
        logger.debug(f"Calling display_text...")
        self.display_text()
        logger.info(f"Sysinfo completed.")


app = Flask(__name__)
sio = SocketIO(app)


@sio.on('event')
def on_event(data):
    pass


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


def find_matching_endpoint(endpoint_list, shell_target):
    for endpoint in endpoint_list:
        if endpoint.conn == shell_target:
            return endpoint
    return None


def call_screenshot():
    matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
    if matching_endpoint:
        sc = Screenshot(hands_off_path, log_path, matching_endpoint)
        sc.run()


def call_anydesk() -> bool:
    logger.info(f'Running anydesk_command...')
    matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
    if matching_endpoint:
        try:
            logger.debug(f'Sending anydesk command to {matching_endpoint.conn}...')
            matching_endpoint.conn.send('anydesk'.encode())

            logger.debug(f'Waiting for response from {matching_endpoint.ip}......')
            msg = matching_endpoint.conn.recv(1024).decode()
            logger.debug(f'Client response: {msg}.')
            if "OK" not in msg:
                logger.debug(f'Updating statusbar message...')
                logger.debug(f'Display popup confirmation for install anydesk...')
                install_ad = input("Install Anydesk?")
                install_ad = install_ad == 'yes'

                logger.debug(f'Install anydesk: {install_ad}.')
                if install_ad:
                    logger.debug(f'Updating statusbar message...')
                    logger.debug(f'Sending install command to {matching_endpoint.conn}')
                    matching_endpoint.conn.send('y'.encode())
                    while "OK" not in msg:
                        logger.debug(f'Waiting for response from {matching_endpoint.ip}...')
                        msg = matching_endpoint.conn.recv(1024).decode()
                        logger.debug(f'{matching_endpoint.ip}: {msg}...')
                        print(f'{matching_endpoint.ip}: {msg}...')

                    logger.debug(f'End of OK in msg loop.')
                    print("Anydesk Running")
                    logger.info(f'anydesk_command completed.')

                else:
                    logger.debug(f'Sending cancel command to {matching_endpoint.conn}...')
                    matching_endpoint.conn.send('n'.encode())
                    return

            else:
                print("anydesk running...")
                logger.info(f'anydesk_command completed.')
                return True

        except (WindowsError, ConnectionError, socket.error, RuntimeError) as e:
            logger.error(f'Connection Error: {e}.')
            logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
            server.remove_lost_connection(matching_endpoint)
            return False


def call_sysinfo():
    matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
    if matching_endpoint:
        sysinfo = Sysinfo(hands_off_path, log_path, matching_endpoint)
        sysinfo.run()


@app.route('/controller', methods=['POST'])
def send_message():
    data = request.json.get('data')
    if data == 'screenshot':
        call_screenshot()
        return jsonify({'message': 'Screenshot message sent.'})

    if data == 'anydesk':
        call_anydesk()
        return jsonify({'message': 'Anydesk message sent.'})

    if data == 'sysinfo':
        call_sysinfo()
        return jsonify({'message': 'Sysinfo message sent.'})

    if data == 'tasks':
        return jsonify({'message': 'Tasks message sent.'})

    if data == 'restart':
        return jsonify({'message': 'Restart message sent.'})

    if data == 'local':
        return jsonify({'message': 'Local message sent.'})

    if data == 'update':
        return jsonify({'message': 'Update message sent.'})


def is_shell_target(endpoint_list, shell_target):
    for endpoint in endpoint_list:
        if endpoint.conn == shell_target:
            return True
    return False


@app.route('/shell_data', methods=['POST'])
def shell_data():
    global shell_target
    selected_row_data = request.get_json()
    if isinstance(shell_target, list):
        shell_target = []

    for endpoint in server.endpoints:
        if endpoint.ip == selected_row_data['ip_address']:
            print(f"Shell to: {endpoint.conn} | {endpoint.ip} | {endpoint.ident}")
            shell_target = endpoint.conn
            return jsonify({'message': 'Selected row data received and saved successfully'})


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

    server.listener()
    sio.run(app, port=8000)
