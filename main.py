"""
    HandsOff
    A C&C for IT Admins
    Copyright (C) 2023 Gil Shwartz

    This work is licensed under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    You should have received a copy of the GNU General Public License along with this work.
    If not, see <https://www.gnu.org/licenses/>.
"""

from flask import Flask, render_template, request, jsonify, \
    send_from_directory, url_for, redirect, send_file, session
from dotenv import load_dotenv, dotenv_values
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone, timedelta
import subprocess
import threading
import requests
import socketio
import platform
import argparse
import psutil
import socket
import json
import time
import sys
import os

from Modules.logger import init_logger
from Modules.commands import Commands
from Modules.server import Server
from Modules.utils import Handlers
from Modules.controller import Controller


class Backend:
    def __init__(self, logger, main_path, log_path, server, version, server_ip, port):
        self.logger = logger
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.version = version
        self.server_ip = server_ip
        self.port = port

        self.station = False
        self.images = {}
        self.rows = []
        self.temp = []
        self.temp_rows = []

        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('SECRET_KEY')
        self.app.config['SESSION_TIMEOUT'] = 3600
        self.sio = SocketIO(self.app)

        self.controller = Controller(self.main_path, self.log_path, self.server,
                                     self.reload)
        self.handlers = Handlers(self.log_path, self.main_path)

        self._routes()

    def _routes(self):
        self.logger.info(f"Defining app routes...")
        self.sio.event('event')(self.on_event)
        self.sio.event('connect')(self.handle_connect)

        self.app.route('/static/<path:path>')(self.serve_static)
        self.app.route('/static/images/<path:path>')(self.serve_images)
        self.app.route('/static/checkboxes.js')(self.serve_checkboxes_js)
        self.app.route('/download/<filename>')(self.download_file)
        self.app.errorhandler(404)(self.page_not_found)
        self.app.route('/')(self.index)

        self.app.route('/reload')(self.reload)
        self.app.route('/get_files', methods=['GET'])(self.get_files)
        self.app.route('/get_file_content', methods=['GET'])(self.get_file_content)
        self.app.route('/control', methods=['POST'])(self.control)
        self.app.route('/shell_data', methods=['POST', 'GET'])(self.shell_data)
        self.app.route('/kill_task', methods=['POST'])(self.task_kill)
        self.app.route('/clear_local', methods=['POST'])(self.clear_local)
        self.app.route('/login', methods=['POST', 'GET'])(self.login)
        self.app.route('/logout', methods=['POST'])(self.logout)
        self.app.route('/discover', methods=['POST'])(self.discover)
        self.app.route('/ex_ip', methods=['GET'])(self.get_ex_ip)
        self.app.route('/wifi', methods=['POST'])(self.get_wifi)

    def on_event(self, data):
        pass

    def handle_connect(self):
        pass

    def login(self):
        self.logger.info("running login()...")
        self.failed_attempts_key = 'failed_login_attempts'
        self.max_attempts = 3

        if request.method == 'POST':
            username = request.form['username']
            password = request.form["password"]

            if username == os.getenv('USER') and password == os.getenv('PASSWORD'):
                self.logger.info('Authentication successful, redirect to the index page')
                session['logged_in'] = True
                session['login_time'] = datetime.now(timezone.utc)
                session['username'] = username
                session.pop(self.failed_attempts_key, None)
                error_message = None
                login_disabled = False
                return redirect(url_for('index'))

            else:
                self.failed_attempts = session.get(self.failed_attempts_key, 0) + 1
                session[self.failed_attempts_key] = self.failed_attempts
                if session.get(self.failed_attempts_key, 0) >= self.max_attempts:
                    self.error_message = "Too many failed login attempts. Please try again later."
                    login_disabled = True

                else:
                    self.error_message = "Invalid credentials. Please try again."
                    login_disabled = True

                return render_template('login.html',
                                       error_message=self.error_message,
                                       failed_attempts=session.get(self.failed_attempts_key, 0),
                                       login_disabled=login_disabled)

        return render_template('login.html', error_message=None, failed_attempts=None)

    def logout(self):
        self.logger.info("running logout()...")
        try:
            session.pop('logged_in', None)
            session.pop('login_time', None)
            session.pop('username', None)
            return redirect('/login')

        except Exception as e:
            self.logger.error(e)
            return redirect('/login')

    def serve_static(self, path):
        return send_from_directory('static', path)

    def serve_images(self, path):
        return send_from_directory('static/images', path)

    def serve_checkboxes_js(self):
        return self.app.send_static_file('checkboxes.js'), 200, {'Content-Type': 'application/javascript'}

    def download_file(self, filename):
        self.logger.debug(f"Serving file: {filename}...")
        return send_from_directory('static', filename, as_attachment=True)

    def page_not_found(self, error) -> jsonify:
        self.logger.info(fr'Error 404: Directory not found.')
        return jsonify({'error': 'Directory not found'}), 404

    def find_matching_endpoint(self, data) -> str:
        self.logger.debug("Finding matching endpoint...")
        try:
            matching_endpoints = [endpoint for endpoint in self.server.endpoints if
                                  endpoint.conn == self.commands.shell_target]
            return next(iter(matching_endpoints), None)

        except AttributeError as e:
            self.logger.error(e)
            return data['checkedItems']

    def get_files(self) -> jsonify:
        self.logger.info(f'Running get_images...')
        self.logger.debug(fr'Waiting for directory from the frontend...')
        directory = request.args.get('directory')
        self.logger.debug(fr'directory: {directory}')
        images = []
        sysinfo_files = []
        tasks_files = []

        if os.path.isdir(directory):
            file_names = [os.path.join(directory, f) for f in os.listdir(directory)]
            file_names_sorted = sorted(file_names, key=os.path.getctime)

            for filename in file_names_sorted:
                if filename.endswith('.jpg') or filename.endswith('.png'):
                    images.append({'path': filename})

                if filename.endswith('txt') and 'systeminfo' in filename:
                    sysinfo_files.append(filename)

                if filename.endswith('txt') and 'tasks' in filename:
                    tasks_files.append(filename)

        return jsonify({'images': images, 'info': sysinfo_files, 'tasks': tasks_files})

    def get_file_content(self):
        self.logger.info("Running get_file_content()...")
        filename = request.args.get('filename')
        with open(filename, 'r') as file:
            file_content = file.read()

        return jsonify({'fileContent': file_content})

    def count_files(self):
        self.logger.info("Running count_files()...")
        selected_id = self.selected_row_data['id']
        matching_endpoints = [ep for ep in self.server.endpoints if ep.client_mac == selected_id]

        if matching_endpoints:
            endpoint = matching_endpoints[0]
            self.commands.shell_target = endpoint.conn
            dir_path = os.path.join('static', 'images', endpoint.ident)
            file_list = os.listdir(dir_path)
            return len(file_list)

        return None

    def control(self):
        self.logger.info(f"<Control>")

        restarted = []
        updated = []
        data = request.get_json()
        self.logger.debug(f"Command: {data}")

        matching_endpoint = self.find_matching_endpoint(data)
        self.logger.debug(f"Matching Endpoint: {matching_endpoint}.")
        if matching_endpoint:
            handler, message = self.controller.handle_controller_action(
                data, restarted, updated, matching_endpoint)
            self.logger.debug(f"Handler: {handler} | Message: {message}\n")

            if handler:
                try:
                    if message['type']:
                        return jsonify(message)

                except TypeError:
                    return jsonify({'message': message})

            self.logger.error(f"Unknown command: {data}")
            return jsonify({'message': f'Unknown command: {data}'})

        return jsonify({'message:': 'No matching endpoint found.'})

    def discover(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        self.logger.debug(f"Calling self.commands.discover()...")
        netMap = self.commands.call_discover(matching_endpoint)
        files = self.count_files()
        self.logger.info(f"Netmap: {netMap}\nFiles: {files}\n")
        return jsonify({'map': netMap, 'files': files})

    def get_ex_ip(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        self.logger.info("Calling commands.get_ex_ip()...")
        ip = self.commands.ex_ip(matching_endpoint)
        return jsonify({'ip': ip})

    def get_wifi(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        if not matching_endpoint:
            return jsonify({'wifi': 'No endpoint found.'})

        self.logger.info("Calling commands.get_nearby_wifi()...")
        networks_data, files = self.commands.get_nearby_wifi(matching_endpoint)
        return jsonify({'wifi': networks_data, 'files': files})

    def clear_local(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        path = self.handlers.clear_local(matching_endpoint)
        if path:
            return jsonify({'message': f'Local dir cleared'})

        return jsonify({'error': f'Something went wrong'})

    def task_kill(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        message = self.controller.handle_task_kill(matching_endpoint)
        return jsonify({'message': message})

    def last_boot(self, format_str='%d/%b/%y %H:%M:%S %p'):
        last_reboot = psutil.boot_time()
        last_reboot_str = datetime.fromtimestamp(last_reboot).strftime(format_str)
        return last_reboot_str

    def reload(self):
        self.logger.info("Reloading...")
        self.temp.clear()
        self.temp_rows.clear()
        self.rows.clear()
        return redirect(url_for('index'))

    def shell_data(self) -> jsonify:
        self.logger.info(f'Running shell_data...')
        if self.server.endpoints:
            self.station = True

        self.selected_row_data = request.get_json()
        checked_value = self.selected_row_data.get('checked', 'None')
        row_value = self.selected_row_data.get('row')

        if row_value == 'clear_shell':
            self.station = False
            return jsonify({'message': 'Shell cleared.'})

        if 'id' in self.selected_row_data and checked_value:
            if self.server.endpoints:
                time_now = datetime.now(timezone.utc)
                session['login_time'] = time_now
                for endpoint in self.server.endpoints:
                    try:
                        if endpoint.client_mac == self.selected_row_data['id']:
                            dir_path = os.path.join('static', 'images', endpoint.ident)
                            if not os.path.exists(dir_path):
                                os.makedirs(dir_path, exist_ok=True)

                            file_list = os.listdir(dir_path)
                            self.num_files = self.count_files()

                    except KeyError:
                        pass

                try:
                    self.logger.info(f'row: {self.selected_row_data}\n'
                                     f'station: {self.station}\n'
                                     f'num_files: {self.num_files}')
                except AttributeError:
                    pass

                return jsonify({'row': self.selected_row_data,
                                'station': self.station,
                                'num_files': self.num_files})

            self.commands.shell_target = []
            self.station = False
            self.logger.info(fr'No connected stations.')
            return jsonify({'message': 'No connected stations.'})

        else:
            return jsonify({'station': self.station})

    def get_ident(self) -> jsonify:
        self.logger.info(f'<Get Ident>')
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.commands.shell_target:
                endpoint_ident = endpoint.ident

                self.logger.info(fr'shell_target: {endpoint_ident}')
                return jsonify({'shell_target': endpoint_ident})

        return jsonify({'shell_target': 'None'})

    def index(self) -> render_template:
        if not session.get('logged_in'):
            self.logger.error(f'User {os.getenv("USER")} is not logged in.')
            return redirect('/login')

        if 'logged_in' in session and 'login_time' in session:
            self.logger.info(f'User {os.getenv("USER")} logged in successfully')
            login_time = session['login_time']
            time_now = datetime.now(timezone.utc)
            session_timeout = self.app.config['SESSION_TIMEOUT']
            if (time_now - login_time).total_seconds() < session_timeout:
                session['login_time'] = time_now
                elapsed_time = time_now - login_time
                hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                elapsed_time_str = f"{int(hours)} hours, {int(minutes)} minutes"
                self.logger.info(f'User {os.getenv("USER")} logged in for {elapsed_time_str}')
                matching_endpoint = None
                self.commands = Commands(self.main_path, self.log_path, matching_endpoint,
                                         self.server.remove_lost_connection)
                self.logger.debug(fr'shell_target: {matching_endpoint}')
                boot_time = self.last_boot()

                for endpoint in self.server.endpoints:
                    self.server.check_vital_signs(endpoint)

                connected_stations = len(self.server.endpoints)
                self.logger.debug(fr'connected stations: {len(self.server.endpoints)}')

                kwargs = {
                    "serving_on": f"{os.getenv('SERVER_URL')}:{os.getenv('WEB_PORT')}",
                    "server_ip": os.getenv('SERVER_IP'),
                    "server_port": os.getenv('SERVER_PORT'),
                    "boot_time": boot_time,
                    "connected_stations": connected_stations,
                    "endpoints": self.server.endpoints,
                    "history": self.server.connHistory,
                    "history_rows": len(self.server.connHistory),
                    "server_version": self.version,
                }

                return render_template('index.html', **kwargs)

        return render_template('login.html', failed_attempts=None)

    def run(self):
        self.sio.run(self.app, host=self.server_ip, port=self.port)


def check_platform(main_path):
    if platform.system() == 'Windows':
        main_path = main_path.replace('/', '\\')
        log_path = os.path.join(main_path, os.getenv('LOG_FILE'))
        return main_path, log_path

    elif platform.system() == 'Linux':
        log_path = os.path.join(main_path, os.getenv('LOG_FILE'))
        return main_path, log_path

    else:
        print("Unsupported operating system.")
        sys.exit(1)


def main(**kwargs):
    logger = init_logger(kwargs.get('log_path'), __name__)

    try:
        os.makedirs(str(kwargs.get('main_path')), exist_ok=True)

    except Exception as e:
        print(f"Failed to create directory '{kwargs.get('main_path')}': {e}")
        sys.exit(1)

    try:
        with open(kwargs.get('log_path'), 'w'):
            pass

    except IOError as e:
        print(f"Failed to open file '{kwargs.get('log_path')}': {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An error occurred while trying to open file '{kwargs.get('log_path')}': {e}")
        sys.exit(1)

    server = Server(kwargs.get('server_ip'), kwargs.get('server_port'), kwargs.get('log_path'))
    backend = Backend(logger, kwargs.get('main_path'), kwargs.get('log_path'),
                      server, kwargs.get('server_version'), kwargs.get('server_ip'), kwargs.get('web_port'))

    backend_thread = threading.Thread(target=backend.run)
    backend_thread.start()
    server.listener()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HandsOff-Server')
    parser.add_argument('-wp', '--web_port', type=int, help='Web port')
    parser.add_argument('-sp', '--server_port', type=int, help='Server port')
    parser.add_argument('-mp', '--main_path', type=str, help='Main path')
    parser.add_argument('-ip', '--server_ip', type=str, help='Server IP')
    args = parser.parse_args()

    load_dotenv()
    web_port = args.web_port if args.web_port else int(os.getenv('WEB_PORT'))
    server_port = args.server_port if args.server_port else int(os.getenv('SERVER_PORT'))
    main_path = args.main_path if args.main_path else str(os.getenv('MAIN_PATH'))
    main_path, log_path = check_platform(main_path)
    server_ip = args.server_ip if args.server_ip else str(os.getenv('SERVER_IP'))
    server_version = os.getenv('SERVER_VERSION')

    kwargs = {
        'web_port': web_port,
        'server_port': server_port,
        'main_path': main_path,
        'log_path': log_path,
        'server_ip': server_ip,
        'server_version': server_version,
    }

    main(**kwargs)
