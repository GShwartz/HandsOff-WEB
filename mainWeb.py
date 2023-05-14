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
import os

from Modules.screenshot import Screenshot
from Modules.logger import init_logger
from Modules.sysinfo import Sysinfo
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


class Commands:
    def call_screenshot(self):
        matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
        if matching_endpoint:
            sc = Screenshot(hands_off_path, log_path, matching_endpoint, server, shell_target)
            sc.run()

    def call_anydesk(self) -> bool:
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

    def call_sysinfo(self):
        matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
        if matching_endpoint:
            sysinfo = Sysinfo(hands_off_path, log_path, matching_endpoint, server, shell_target)
            sysinfo.run()

        else:
            logger.info("No target")
            return False

    def call_tasks(self):
        matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
        if matching_endpoint:
            self.tasks = Tasks(hands_off_path, log_path, matching_endpoint)
            self.tasks.run()

    def tasks_post_run(self):
        task_name = request.json.get('taskName')
        if task_name:
            self.tasks.kill_task(task_name)
            return jsonify({'message': f'Killed task {task_name}'}), 200

        else:
            return jsonify({'error': 'No task name provided'}), 400

    def call_restart(self):
        matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
        if matching_endpoint:
            logger.info(f'Running restart_command...')
            logger.debug(f'Displaying confirmation...')

            try:
                logger.debug(f'Sending restart command to {matching_endpoint.ip}...')
                matching_endpoint.conn.send('restart'.encode())
                logger.debug(f'Sleeping for 1.2s...')
                time.sleep(1.2)
                server.remove_lost_connection(matching_endpoint)
                print(f"Restart command sent to {matching_endpoint.ip} | {matching_endpoint.ident}")
                logger.info(f'restart_command completed.')
                return True

            except (RuntimeError, WindowsError, socket.error) as e:
                logger.error(f'Connection Error: {e}.')
                logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                server.remove_lost_connection(matching_endpoint)
                logger.info(f'restart_command failed.')
                return False

        else:
            return False

    def call_update_selected_endpoint(self) -> bool:
        global shell_target
        logger.info(f'Running update_selected_endpoint...')
        matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
        if matching_endpoint:
            try:
                logger.debug(f'Sending update command to {matching_endpoint.ip} | {matching_endpoint.ident}...')
                matching_endpoint.conn.send('update'.encode())
                server.remove_lost_connection(matching_endpoint)
                if isinstance(shell_target, list):
                    shell_target = []
                logger.info(f'update_selected_endpoint completed.')
                return True

            except (RuntimeError, WindowsError, socket.error) as e:
                logger.error(f'Connection Error: {e}.')
                logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                server.remove_lost_connection(matching_endpoint)
                return False


class Backend:
    def __init__(self):
        self.app = Flask(__name__)
        self.sio = SocketIO(self.app)
        self.commands = Commands()
        self.images = {}
        self.app.route('/static/<path:path>')(self.serve_static)
        self.app.route('/static/images/<path:path>')(self.serve_images)
        self.app.route('/static/controller.js')(self.serve_controller_js)
        self.app.errorhandler(404)(self.page_not_found)

        self.app.route('/reload')(self.reload)
        self.sio.event('event')(self.on_event)
        self.sio.event('connect')(self.handle_connect)

        self.app.route('/')(self.index)
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
            # return jsonify({'message': 'Kill Task message sent.'})

        if data == 'restart':
            if self.commands.call_restart():
                self.reload()
            return jsonify({'message': 'Restart message sent.'})

        if data == 'local':
            global shell_target
            matching_endpoint = find_matching_endpoint(server.endpoints, shell_target)
            if matching_endpoint:
                browse_local_files(matching_endpoint.ident)
            return jsonify({'message': 'Local message sent.'})

        if data == 'update':
            if self.commands.call_update_selected_endpoint():
                shell_target = []
            return jsonify({'message': 'Update message sent.'})

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
        global shell_target
        selected_row_data = request.get_json()
        if isinstance(shell_target, list) or Backend().images:
            shell_target = []

        for endpoint in server.endpoints:
            if endpoint.ip == selected_row_data['ip_address']:
                shell_target = endpoint.conn
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
        for endpoint in server.endpoints:
            if endpoint.conn == shell_target:
                endpoint_ident = endpoint.ident
                return jsonify({'shell_target': endpoint_ident})

        return jsonify({'shell_target': 'None for now'})

    def index(self):
        global shell_target
        shell_target = []
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
            "endpoints": server.endpoints,
            "history": server.connHistory,
            "server_version": version
        }

        return render_template('index.html', **kwargs)

    def run(self):
        self.sio.run(self.app, host='0.0.0.0', port=8000)


def create_local_dir(endpoint_ident):
    local_dir = os.path.join('static', 'images', endpoint_ident)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    return local_dir


def find_matching_endpoint(endpoint_list, shell_target):
    for endpoint in endpoint_list:
        if endpoint.conn == shell_target:
            return endpoint
    return None


def browse_local_files(ident) -> subprocess:
    logger.info(f'Running browse_local_files_command...')
    directory = os.path.join(hands_off_path, ident)
    logger.debug(fr'Opening {directory}...')
    return subprocess.Popen(rf"explorer {directory}")


def last_boot():
    last_reboot = psutil.boot_time()
    bt = datetime.fromtimestamp(last_reboot).strftime('%d/%b/%y %H:%M:%S %p')
    return bt


def get_date() -> str:
    d = datetime.now().replace(microsecond=0)
    dt = str(d.strftime("%d/%b/%y %H:%M:%S"))
    return dt


def main():
    backend = Backend()
    server.listener()
    backend.run()


if __name__ == '__main__':
    load_dotenv()
    version = "1.00"
    hands_off_path = r'c:\HandsOff'
    if not os.path.exists(str(hands_off_path)):
        os.makedirs(hands_off_path)

    log_path = os.path.join(hands_off_path, 'server_log.txt')
    with open(log_path, 'w'):
        pass

    server_ip = '0.0.0.0'
    server_port = 55400
    server = Server(server_ip, server_port, log_path)
    logger = init_logger(log_path, __name__)

    shell_target = []

    main()
