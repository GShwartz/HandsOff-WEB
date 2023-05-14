from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, redirect
from dotenv import load_dotenv, dotenv_values
from flask_socketio import SocketIO, emit
from datetime import datetime
from PIL import Image, ImageTk
import subprocess
import threading
import requests
import socketio
import eventlet
import psutil
import shutil
import socket
import glob
import time
import sys
import os

from Modules.logger import init_logger
from Modules.commands import Commands
from Modules.server import Server


class Tasks:
    def __init__(self, path, log_path, endpoint):
        self.endpoint = endpoint
        self.path = path
        self.log_path = log_path
        self.tasks_file_path = os.path.join(self.path, self.endpoint.ident)
        self.logger = init_logger(self.log_path, __name__)
        self.on_complete = None

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def display_text(self):
        logger.info(f"Running display_text...")
        os.startfile(self.full_file_path)

    def kill_task(self, taskname):
        logger.debug(f"Running kill_task...")
        try:
            logger.debug(f"Sending kill command to {self.endpoint.ip}...")
            self.endpoint.conn.send('kill'.encode())

        except (WindowsError, socket.error) as e:
            logger.debug(f"Error: {e}")
            logger.debug(f"Calling server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

        try:
            logger.debug(f"Sending {str(taskname)} to {self.endpoint.ip}...")
            self.endpoint.conn.send(str(taskname).encode())

        except (WindowsError, socket.error) as e:
            logger.debug(f"Error: {e}")
            logger.debug(f"Calling server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

        try:
            logger.debug(f"Waiting for confirmation from {self.endpoint.ip}...")
            msg = self.endpoint.conn.recv(1024).decode()
            logger.debug(f"{self.endpoint.ip}: {msg}")
            self.logger.debug(f"Displaying {msg} in popup window...")
            print(f"{self.endpoint.ip} | {self.endpoint.ident}: ", f"{msg}")
            return True

        except (WindowsError, socket.error) as e:
            logger.debug(f"Error: {e}")
            logger.debug(f"Calling server.remove_lost_connection({self.endpoint})...")
            server.remove_lost_connection(self.endpoint)
            return False

    def get_file_name(self):
        logger.info(f"Running get_file_name...")
        logger.debug(f"Waiting for filename from {self.endpoint.ip}...")
        self.endpoint.conn.settimeout(10)
        self.filenameRecv = self.endpoint.conn.recv(1024).decode()
        self.full_file_path = os.path.join(self.tasks_file_path, self.filenameRecv)
        self.endpoint.conn.settimeout(None)
        logger.debug(f"Filename: {self.filenameRecv}")

    def get_file_size(self):
        logger.info(f"Running get_file_size...")
        logger.debug(f"Waiting for file size from {self.endpoint.ip}...")
        self.endpoint.conn.settimeout(10)
        self.size = self.endpoint.conn.recv(4)
        self.endpoint.conn.settimeout(None)
        self.size = self.bytes_to_number(self.size)
        logger.debug(f"Size: {self.size}")

    def get_file_content(self):
        logger.info(f"Running get_file_content...")

        current_size = 0
        buffer = b""

        logger.debug(f"Writing content to {self.full_file_path}...")
        with open(self.full_file_path, 'wb') as tsk_file:
            self.endpoint.conn.settimeout(60)
            while current_size < self.size:
                data = self.endpoint.conn.recv(1024)
                if not data:
                    break

                if len(data) + current_size > self.size:
                    data = data[:self.size - current_size]

                buffer += data
                current_size += len(data)
                tsk_file.write(data)
            self.endpoint.conn.settimeout(None)

    def confirm(self):
        logger.info(f"Running confirm...")
        logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
        self.endpoint.conn.send(f"Received file: {self.filenameRecv}\n".encode())
        self.endpoint.conn.settimeout(10)
        msg = self.endpoint.conn.recv(1024).decode()
        self.endpoint.conn.settimeout(None)
        logger.debug(f"{self.endpoint.ip}: {msg}")

    def run(self):
        logger.info(f"Running run...")
        self.filepath = os.path.join(self.path, self.endpoint.ident)
        try:
            os.makedirs(self.filepath)

        except FileExistsError:
            logger.debug(f"{self.filepath} exists.")
            pass

        try:
            logger.debug(f"Sending tasks command to {self.endpoint.ip}...")
            self.endpoint.conn.send('tasks'.encode())

        except (WindowsError, socket.error) as e:
            logger.debug(f"Error: {e}")
            logger.debug(f"Calling server.remove_lost_connection({self.endpoint})")
            server.remove_lost_connection(self.endpoint)
            return False

        logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        logger.debug(f"Calling confirm...")
        self.confirm()

        src = os.path.join(self.filepath, self.filenameRecv)
        for endpoint in server.endpoints:
            if endpoint.conn == shell_target:
                endpoint_ident = endpoint.ident
                local_dir = create_local_dir(endpoint_ident)
                shutil.copy(src, local_dir)

        logger.debug(f"Calling display_text...")
        self.display_text()
        logger.info(f"run completed.")


class Backend:
    def __init__(self, logger, main_path, log_path, server, version, shell_target):
        self.logger = logger
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.version = version
        self.shell_target = shell_target

        self.app = Flask(__name__)
        self.sio = SocketIO(self.app)

        self.images = {}

        self.sio.event('event')(self.on_event)
        self.sio.event('connect')(self.handle_connect)

        self.app.route('/')(self.index)
        self.app.errorhandler(404)(self.page_not_found)

        self.app.route('/reload')(self.reload)
        self.app.route('/static/<path:path>')(self.serve_static)
        self.app.route('/static/images/<path:path>')(self.serve_images)
        self.app.route('/static/controller.js')(self.serve_controller_js)
        self.app.route('/get_images', methods=['GET'])(self.get_images)
        self.app.route('/controller', methods=['POST'])(self.send_message)
        self.app.route('/shell_data', methods=['POST'])(self.shell_data)

    def send_message(self):
        data = request.json.get('data')
        if data == 'screenshot':
            self.commands.call_screenshot()
            return jsonify({'message': 'Screenshot message sent.'})

        if data == 'anydesk':
            self.commands.call_anydesk()
            return jsonify({'message': 'Anydesk message sent.'})

        if data == 'sysinfo':
            self.commands.call_sysinfo()
            return jsonify({'message': 'Sysinfo message sent.'})

        if data == 'tasks':
            self.commands.call_tasks()
            return jsonify({'message': 'Tasks message sent.'})

        if data == 'kill_task':
            self.commands.tasks_post_run()
            # return jsonify({'message': 'Kill Task message sent.'})

        if data == 'restart':
            if self.commands.call_restart():
                self.reload()
            return jsonify({'message': 'Restart message sent.'})

        if data == 'local':
            matching_endpoint = self.find_matching_endpoint()
            if matching_endpoint:
                self.browse_local_files(matching_endpoint.ident)
            return jsonify({'message': 'Local message sent.'})

        if data == 'update':
            if self.commands.call_update_selected_endpoint():
                self.shell_target = []
            return jsonify({'message': 'Update message sent.'})

    def find_matching_endpoint(self):
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.shell_target:
                return endpoint
        return None

    def browse_local_files(self, ident) -> subprocess:
        self.logger.info(f'Running browse_local_files_command...')
        directory = os.path.join(self.main_path, ident)
        self.logger.debug(fr'Opening {directory}...')
        return subprocess.Popen(rf"explorer {directory}")

    def serve_static(self, path):
        return send_from_directory('static', path)

    def serve_controller_js(self):
        return self.app.send_static_file('controller.js'), 200, {'Content-Type': 'application/javascript'}

    def serve_images(self, path):
        return send_from_directory('static/images', path)

    def reload(self):
        return redirect(url_for('index'))

    def on_event(self, data):
        pass

    def handle_connect(self):
        pass

    def page_not_found(self, error):
        return jsonify({'error': 'Directory not found'}), 404

    def get_images(self):
        directory = request.args.get('directory')
        images = []

        if os.path.isdir(directory):
            file_names = [os.path.join(directory, f) for f in os.listdir(directory)]
            file_names_sorted = sorted(file_names, key=os.path.getctime)

            for filename in file_names_sorted:
                if filename.endswith('.jpg') or filename.endswith('.png'):
                    images.append({'path': filename})

        return jsonify({'images': images})

    def shell_data(self):
        selected_row_data = request.get_json()
        if isinstance(self.shell_target, list) or self.images:
            self.shell_target = []

        for endpoint in self.server.endpoints:
            if endpoint.ip == selected_row_data['ip_address']:
                self.shell_target = endpoint.conn
                self.commands = Commands(self.logger, self.main_path, self.log_path, self.server, self.shell_target)

                endpoint_ident = endpoint.ident

                dynamic_folder = request.args.get('folder')
                images = []

                # Check if the directory exists
                if os.path.isdir(str(dynamic_folder)):
                    for filename in os.listdir(dynamic_folder):
                        if filename.endswith('.jpg'):
                            images.append({'path': os.path.join(dynamic_folder, filename)})

                    # Return images as JSON response
                    return jsonify({'images': images})

                return jsonify({'message': 'Selected row data received and saved successfully'})

        return jsonify({'message': 'No endpoint found for the selected row data.'})

    def get_ident(self):
        print(self.shell_target)
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.shell_target:
                endpoint_ident = endpoint.ident
                return jsonify({'shell_target': endpoint_ident})

        return jsonify({'shell_target': 'None for now'})

    def index(self):
        self.shell_target = []
        boot_time = last_boot()
        connected_stations = len(self.server.endpoints)

        kwargs = {
            "serving_on": os.getenv('SERVER_URL'),
            "server_ip": os.getenv('SERVER_IP'),
            "server_port": os.getenv('SERVER_PORT'),
            "boot_time": boot_time,
            "connected_stations": connected_stations,
            "endpoints": self.server.endpoints,
            "history": self.server.connHistory,
            "server_version": self.version
        }

        return render_template('index.html', **kwargs)

    def run(self):
        port = int(sys.argv[1]) if len(sys.argv) > 1 else os.getenv('DEFAULT_PORT')
        self.sio.run(self.app, host='0.0.0.0', port=port)


def create_local_dir(endpoint_ident):
    local_dir = os.path.join('static', 'images', endpoint_ident)
    if not os.path.exists(local_dir):
        try:
            os.makedirs(str(local_dir), exist_ok=True)

        except Exception as e:
            print(f"Failed to create directory '{local_dir}': {e}")

    return local_dir


def last_boot():
    last_reboot = psutil.boot_time()
    bt = datetime.fromtimestamp(last_reboot).strftime('%d/%b/%y %H:%M:%S %p')
    return bt


def get_date() -> str:
    d = datetime.now().replace(microsecond=0)
    dt = str(d.strftime("%d/%b/%y %H:%M:%S"))
    return dt


def main():
    version = "1.00"

    load_dotenv()
    main_path = str(sys.argv[3]) if len(sys.argv) > 3 else os.getenv('MAIN_PATH')
    server_ip = str(sys.argv[4]) if len(sys.argv) > 4 else os.getenv('SERVER_IP')
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else os.getenv('SERVER_PORT')
    log_path = os.path.join(main_path, os.getenv('LOG_FILE'))

    try:
        os.makedirs(str(main_path), exist_ok=True)

    except Exception as e:
        print(f"Failed to create directory '{main_path}': {e}")

    try:
        with open(log_path, 'w'):
            pass

    except IOError as e:
        print(f"Failed to open file '{log_path}': {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An error occurred while trying to open file '{log_path}': {e}")
        sys.exit(1)

    shell_target = []

    server = Server(server_ip, server_port, log_path)
    logger = init_logger(log_path, __name__)
    backend = Backend(logger, main_path, log_path, server, version, shell_target)

    server.listener()
    backend.run()


if __name__ == '__main__':
    main()
