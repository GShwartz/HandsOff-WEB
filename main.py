from flask import Flask, render_template, request, jsonify, \
    send_from_directory, url_for, redirect, send_file, session
from dotenv import load_dotenv, dotenv_values
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone, timedelta
import subprocess
import threading
import requests
import socketio
import eventlet
import platform
import argparse
import psutil
import shutil
import socket
import time
import sys
import os

from Modules.logger import init_logger
from Modules.commands import Commands
from Modules.server import Server
from Modules.utils import Handlers


class Backend:
    def __init__(self, logger, main_path, log_path, server, version, port):
        self.logger = logger
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.version = version
        self.port = port

        self.station = False
        self.images = {}

        self.commands = Commands(self.main_path, self.log_path, self.server)

        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('SECRET_KEY')
        self.app.config['SESSION_TIMEOUT'] = 7200   # 2 hours
        self.sio = SocketIO(self.app)
        self.configure_context_processors()

        self._routes()

    def _routes(self):
        self.logger.info(f"Defining app routes...")
        self.sio.event('event')(self.on_event)
        self.sio.event('connect')(self.handle_connect)

        self.app.route('/static/<path:path>')(self.serve_static)
        self.app.route('/static/images/<path:path>')(self.serve_images)
        self.app.route('/static/controller.js')(self.serve_controller_js)
        self.app.route('/static/table_data.js')(self.serve_table_data_js)
        self.app.route('/')(self.index)
        self.app.errorhandler(404)(self.page_not_found)

        self.app.route('/reload')(self.reload)
        self.app.route('/get_images', methods=['GET'])(self.get_files)
        self.app.route('/get_file_content', methods=['GET'])(self.get_file_content)
        self.app.route('/controller', methods=['POST'])(self.controller)
        self.app.route('/shell_data', methods=['POST', 'GET'])(self.shell_data)
        self.app.route('/kill_task', methods=['POST'])(self.commands.tasks_post_run)
        self.app.route('/clear_local', methods=['POST'])(self.clear_local)
        self.app.route('/mode', methods=['POST'])(self.set_mode)
        self.app.route('/login', methods=['POST', 'GET'])(self.login)
        self.app.route('/logout', methods=['POST'])(self.logout)

    def login(self):
        self.failed_attempts_key = 'failed_login_attempts'
        self.max_attempts = 3

        if request.method == 'POST':
            username = request.form['username']
            password = request.form["password"]

            if username == os.getenv('USER') and password == os.getenv('PASSWORD'):
                self.logger.info('Authentication successful, redirect to the index page')
                session['logged_in'] = True
                session['login_time'] = datetime.now(timezone.utc)
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
        try:
            session.pop('logged_in', None)
            session.pop('login_time', None)
            return redirect('/login')

        except Exception as e:
            self.logger.error(e)
            return redirect('/login')

    def set_mode(self):
        mode = request.form.get('mode')
        session['mode'] = mode
        return redirect(url_for('index'))

    def configure_context_processors(self):
        @self.app.context_processor
        def inject_mode():
            def get_mode():
                return session.get('mode', 'style-Dark')

            return {'get_mode': get_mode}

    def serve_static(self, path):
        return send_from_directory('static', path)

    def serve_images(self, path):
        return send_from_directory('static/images', path)

    def serve_controller_js(self):
        return self.app.send_static_file('controller.js'), 200, {'Content-Type': 'application/javascript'}

    def serve_table_data_js(self):
        return self.app.send_static_file('table_data.js'), 200, {'Content-Type': 'application/javascript'}

    def clear_local(self):
        path = self.handlers.clear_local()
        if path:
            return jsonify({'message': f'Local dir cleared'})

        else:
            return jsonify({'error': f'Something went wrong'})

    def controller(self) -> jsonify:
        self.logger.info(f"Waiting for command from the Frontend...")
        data = request.json.get('data')
        self.logger.debug(f"Command: {data}")

        if data == 'screenshot':
            self.logger.debug(f"Calling self.commands.call_screenshot()...")
            if self.commands.call_screenshot():
                self.logger.info(f"Screenshot completed.")
                return jsonify({'message': 'Screenshot Completed'})

            else:
                self.logger.debug(f"Screenshot failed.")
                return jsonify({'message': 'Screenshot failed'})

        if data == 'anydesk':
            self.logger.debug(f"Calling self.commands.call_anydesk()...")
            if not self.commands.call_anydesk():
                self.logger.debug(f"Anydesk missing.")
                return jsonify({'message': f'missing'})

            else:
                self.logger.debug(f"Anydesk running.")
                return jsonify({'message': 'Anydesk installed & running'})

        if data == 'teamviewer':
            self.logger.debug(f"Calling self.commands.call_teamviewer()...")
            if not self.commands.call_teamviewer():
                self.logger.debug(f"teamviewer missing.")
                return jsonify({'message': f'missing'})

            else:
                self.logger.debug(f"TeamViewer running.")
                return jsonify({'message': 'TeamViewer installed & running'})

        if data == 'sysinfo':
            latest_file = self.commands.call_sysinfo()
            if latest_file:
                count = self.count_files()
                try:
                    with open(latest_file, 'r') as file:
                        file_content = file.read()

                    data = {
                        'type': 'system',
                        'fileName': f'{latest_file}',
                        'fileContent': f'{file_content}',
                        'notificationCount': f'{count}',
                    }

                    return jsonify(data)

                except Exception as e:
                    return jsonify({'error': f'{e}'})

            else:
                return jsonify({'error': 'local dir not found'})

        if data == 'tasks':
            latest_file = self.commands.call_tasks()
            if latest_file:
                count = self.count_files()
                try:
                    with open(latest_file, 'r') as file:
                        file_content = file.read()

                    data = {
                        'type': 'tasks',
                        'fileName': f'{latest_file}',
                        'fileContent': f'{file_content}',
                        'notificationCount': f'{count}',
                    }

                    # self.commands.shell_target.send('n'.encode())
                    return jsonify(data)

                except Exception as e:
                    return jsonify({'error': f'{e}'})

            else:
                return jsonify({'error': 'local dir not found'})

        if data == 'restart':
            self.logger.debug(f"Calling self.commands.call_restart()...")
            if self.commands.call_restart():
                self.logger.debug(f"Reloading app...")
                self.reload()
                self.logger.debug(f"Restart completed.")
                return jsonify({'message': 'Restart message sent.'})

            else:
                self.logger.debug(f"Restart failed.")
                return jsonify({'message': 'Restart failed.'})

        if data == 'update':
            self.logger.debug(f"Calling self.commands.call_update_selected_endpoint()...")
            if self.commands.call_update_selected_endpoint():
                self.logger.debug(f"Resetting self.commands.shell_target...")
                self.commands.shell_target = []
                self.logger.debug(f"Update completed.")
                return jsonify({'message': 'Update message sent.'})

            else:
                self.logger.debug(f"Update failed.")
                return jsonify({'message': 'Update failed.'})

        if data == 'view':
            self.logger.debug(f"Calling self.find_matching_endpoint()...")
            matching_endpoint = self.find_matching_endpoint()
            self.logger.debug(f"{matching_endpoint}")
            if matching_endpoint:
                self.logger.debug(f"Calling self.browse_local_files({matching_endpoint.ident})...")
                self.browse_local_files(matching_endpoint.ident)
                self.logger.debug(f"Local completed.")
                return jsonify({'message': 'View message sent.'})

            else:
                return jsonify({'message': 'View failed.'})

        if data == 'clear_local':
            if self.handlers.clear_local():
                return jsonify({'message': 'Files cleared'})

            else:
                return jsonify({'error': 'Error while clearing dir'})

        else:
            self.logger.error(f"Unknown command: {data}")
            return jsonify({'message': f'Unknown: {data}'})

    def find_matching_endpoint(self) -> str:
        self.logger.debug(f"Finding matching endpoint...")
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.commands.shell_target:
                return endpoint
        return None

    def browse_local_files(self, ident) -> subprocess:
        self.logger.info(f'Running browse_local_files_command...')
        directory = os.path.join('static', 'images', ident)
        self.logger.debug(fr'Opening {directory}...')
        if os.path.isdir(directory):
            if platform.system() == 'Windows':
                return subprocess.Popen(rf"explorer {directory}")

            elif platform.system() == 'Linux':
                files = os.listdir(directory)
                for file_name in files:
                    file_path = os.path.join(directory, file_name)
                    files.append(file_path)

                return print(files)

            else:
                print("Unsupported operating system.")
                sys.exit(1)

    def count_files(self):
        if self.server.endpoints:
            for endpoint in self.server.endpoints:
                if endpoint.client_mac == self.selected_row_data['id']:
                    self.commands.shell_target = endpoint.conn
                    dir_path = os.path.join('static', 'images', endpoint.ident)
                    file_list = os.listdir(dir_path)
                    number_of_files = len(file_list)
                    return number_of_files

    def reload(self):
        return redirect(url_for('index'))

    def on_event(self, data):
        pass

    def handle_connect(self):
        pass

    def page_not_found(self, error) -> jsonify:
        self.logger.info(fr'Error 404: Directory not found.')
        return jsonify({'error': 'Directory not found'}), 404

    def get_file_content(self):
        filename = request.args.get('filename')
        with open(filename, 'r') as file:
            file_content = file.read()

        return jsonify({'fileContent': file_content})

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

    def shell_data(self) -> jsonify:
        self.logger.info(f'Running shell_data...')
        if self.server.endpoints:
            self.station = True

        self.selected_row_data = request.get_json()
        if self.selected_row_data:
            if isinstance(self.commands.shell_target, list) or self.images:
                self.logger.debug(fr'resetting shell_target...')
                self.commands.shell_target = []

            if self.server.endpoints:
                for endpoint in self.server.endpoints:
                    if endpoint.client_mac == self.selected_row_data['id']:
                        self.handlers = Handlers(self.log_path, self.main_path, endpoint)

                        self.commands.shell_target = endpoint.conn
                        dir_path = os.path.join('static', 'images', endpoint.ident)
                        if not os.path.exists(dir_path):
                            os.makedirs(dir_path, exist_ok=True)

                        file_list = os.listdir(dir_path)
                        self.num_files = self.count_files()

                self.logger.info(f'row: {self.selected_row_data}\n'
                                 f'station: {self.station}\n'
                                 f'num_files: {self.num_files}')

                return jsonify({'row': self.selected_row_data,
                                'station': self.station,
                                'num_files': self.num_files})

            else:
                self.logger.info(fr'No connected stations.')
                return jsonify({'message': 'No connected stations.'})

        else:
            return jsonify({'station': self.station})

    def get_ident(self) -> jsonify:
        self.logger.info(f'Running get_ident...')
        for endpoint in self.server.endpoints:
            if isinstance(self.commands.shell_target, list):
                continue

            if endpoint.conn == self.commands.shell_target:
                endpoint_ident = endpoint.ident

                self.logger.info(fr'shell_target: {endpoint_ident}')
                return jsonify({'shell_target': endpoint_ident})

        self.logger.info(fr'shell_target: None')
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
                elapsed_time = time_now - login_time
                hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                elapsed_time_str = f"{int(hours)} hours, {int(minutes)} minutes"
                self.logger.info(f'User {os.getenv("USER")} logged in for {elapsed_time_str}')
                self.logger.info(f'Running index...')
                self.commands.shell_target = []
                self.logger.debug(fr'shell_target: {self.commands.shell_target}')
                boot_time = last_boot()

                for endpoint in self.server.endpoints:
                    self.server.check_vital_signs(endpoint)

                connected_stations = len(self.server.endpoints)
                self.logger.debug(fr'connected stations: {len(self.server.endpoints)}')

                kwargs = {
                    "serving_on": os.getenv('SERVER_URL'),
                    "server_ip": os.getenv('SERVER_IP'),
                    "server_port": os.getenv('SERVER_PORT'),
                    "boot_time": boot_time,
                    "connected_stations": connected_stations,
                    "endpoints": self.server.endpoints,
                    "history": self.server.connHistory,
                    "server_version": self.version,
                }

                return render_template('index.html', **kwargs)
        return render_template('login.html')

    def run(self):
        self.sio.run(self.app, host=os.getenv('SERVER_IP'),
                     port=self.port)


def last_boot(format_str='%d/%b/%y %H:%M:%S %p'):
    last_reboot = psutil.boot_time()
    last_reboot_str = datetime.fromtimestamp(last_reboot).strftime(format_str)
    return last_reboot_str


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
                      server, kwargs.get('server_version'), kwargs.get('web_port'))

    server.listener()
    backend.run()


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
