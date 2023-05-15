from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, redirect
from dotenv import load_dotenv, dotenv_values
from flask_socketio import SocketIO, emit
from datetime import datetime
import subprocess
import threading
import requests
import socketio
import eventlet
import psutil
import shutil
import socket
import time
import sys
import os

from Modules.logger import init_logger
from Modules.commands import Commands
from Modules.server import Server


class Backend:
    def __init__(self, main_path, log_path, server, version, port):
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.version = version
        self.port = port
        self.images = {}

        self.logger = init_logger(log_path, __name__)
        self.commands = Commands(self.main_path, self.log_path, self.server)

        self.app = Flask(__name__)
        self.sio = SocketIO(self.app)

        self.app.route('/static/<path:path>')(self.serve_static)
        self.app.route('/static/images/<path:path>')(self.serve_images)

        self.sio.event('event')(self.on_event)
        self.sio.event('connect')(self.handle_connect)

        self.app.route('/')(self.index)
        self.app.errorhandler(404)(self.page_not_found)

        self.app.route('/reload')(self.reload)
        self.app.route('/get_images', methods=['GET'])(self.get_images)
        self.app.route('/controller', methods=['POST'])(self.send_message)
        self.app.route('/shell_data', methods=['POST'])(self.shell_data)
        self.app.route('/kill_task', methods=['POST'])(self.commands.tasks_post_run)

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
            return jsonify({'message': 'Kill Task message sent.'})

        if data == 'restart':
            if self.commands.call_restart():
                self.reload()
                return jsonify({'message': 'Restart message sent.'})

            else:
                return jsonify({'message': 'Failed to send Restart message.'})

        if data == 'local':
            matching_endpoint = self.find_matching_endpoint()
            if matching_endpoint:
                self.browse_local_files(matching_endpoint.ident)
                return jsonify({'message': 'Local message sent.'})

            else:
                return jsonify({'message': 'Failed to send Local message.'})

        if data == 'update':
            if self.commands.call_update_selected_endpoint():
                self.commands.shell_target = []
                return jsonify({'message': 'Update message sent.'})

            else:
                return jsonify({'message': 'Failed to send Update message.'})

    def find_matching_endpoint(self):
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.commands.shell_target:
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
        if isinstance(self.commands.shell_target, list) or self.images:
            self.commands.shell_target = []

        for endpoint in self.server.endpoints:
            if endpoint.client_mac == selected_row_data['id']:
                self.commands.shell_target = endpoint.conn
                endpoint_ident = endpoint.ident
                dynamic_folder = request.args.get('folder')
                images = []

                if os.path.isdir(str(dynamic_folder)):
                    for filename in os.listdir(dynamic_folder):
                        if filename.endswith('.jpg'):
                            images.append({'path': os.path.join(dynamic_folder, filename)})

                    return jsonify({'images': images})

        return jsonify({'message': 'No endpoint found for the selected row data.'})

    def get_ident(self):
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.commands.shell_target:
                endpoint_ident = endpoint.ident
                return jsonify({'shell_target': endpoint_ident})

        return jsonify({'shell_target': 'None'})

    def index(self):
        self.commands.shell_target = []
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
        self.sio.run(self.app, host=os.getenv('SERVER_IP'), port=self.port)


def last_boot(format_str='%d/%b/%y %H:%M:%S %p'):
    last_reboot = psutil.boot_time()
    last_reboot_str = datetime.fromtimestamp(last_reboot).strftime(format_str)
    return last_reboot_str


def main():
    load_dotenv()

    web_port = int(sys.argv[1]) if len(sys.argv) > 1 else os.getenv('WEB_PORT')
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else os.getenv('SERVER_PORT')
    main_path = str(sys.argv[3]) if len(sys.argv) > 3 else os.getenv('MAIN_PATH')
    server_ip = str(sys.argv[4]) if len(sys.argv) > 4 else os.getenv('SERVER_IP')
    log_path = os.path.join(main_path, os.getenv('LOG_FILE'))
    version = os.getenv('SERVER_VERSION')

    try:
        os.makedirs(str(main_path), exist_ok=True)

    except Exception as e:
        print(f"Failed to create directory '{main_path}': {e}")
        sys.exit(1)

    try:
        with open(log_path, 'w'):
            pass

    except IOError as e:
        print(f"Failed to open file '{log_path}': {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An error occurred while trying to open file '{log_path}': {e}")
        sys.exit(1)

    server = Server(server_ip, server_port, log_path)
    backend = Backend(main_path, log_path, server, version, web_port)

    server.listener()
    backend.run()


if __name__ == '__main__':
    main()
