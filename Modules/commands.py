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

from flask import request, jsonify
from datetime import datetime
import socket
import time
import glob
import json
import os

from Modules.logger import init_logger
from Modules.screenshot import Screenshot
from Modules.sysinfo import Sysinfo
from Modules.tasks import Tasks


class Commands:
    def __init__(self, main_path, log_path, server):
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.shell_target = []
        self.logger = init_logger(self.log_path, __name__)

    def call_screenshot(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            self.logger.debug("Initializing Screenshot class...")
            sc = Screenshot(self.main_path, self.log_path, matching_endpoint, self.server, self.shell_target)
            if sc.run():
                return True

    def ex_ip(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            ip = matching_endpoint.external_ip
            return ip

    def get_nearby_wifi(self):
        matching_endpoint = self.find_matching_endpoint()

        if not matching_endpoint:
            return None

        try:
            # Send request to the matching endpoint
            matching_endpoint.conn.send('wifi'.encode())
            received_data = matching_endpoint.conn.recv(1024)
            decoded_data = received_data.decode()

            # Extract SSID list from received data
            ssid_list = [line.split(":")[1].strip() for line in decoded_data.split('\n') if line.startswith("SSID")]

            # Prepare file writing
            path = os.path.join('static', 'images', matching_endpoint.ident)
            os.makedirs(path, exist_ok=True)
            filename = f'network {matching_endpoint.ident}.txt'
            file_path = os.path.join(path, filename)

            # Write data to the newest or create a new file
            with open(file_path, 'a') as file:
                file.write('=' * 50 + f'\nNearby Wi-Fi networks | HOSTNAME: {matching_endpoint.ident} | '
                                      f'IP: {matching_endpoint.ip} | DATE: {self.get_date()}\n\n')
                file.write('\n'.join(ssid_list))
                file.write('\n' + '=' * 50 + '\n')

            # Count files and return data
            file_counter = self.count_files(matching_endpoint)
            return ssid_list, file_counter

        except socket.error as soc_error:
            self.logger.error(f"Socket error: {soc_error}")
            return None

    def call_discover(self):
        matching_endpoint = self.find_matching_endpoint()

        if matching_endpoint:
            self.logger.debug(f"Sending 'discover' to {matching_endpoint.ip}...")
            matching_endpoint.conn.send('discover'.encode())
            msg = matching_endpoint.conn.recv(2048)
            self.logger.debug(f"{matching_endpoint.ip}: {msg}")
            active_hosts = json.loads(msg)
        else:
            active_hosts = {}

        path = os.path.join('static', 'images', matching_endpoint.ident)
        os.makedirs(path, exist_ok=True)

        filename = f'network {matching_endpoint.ident}.txt'
        file_path = os.path.join(path, filename)

        with open(file_path, 'a') as network_file:
            network_file.write(
                f"Active Hosts | HOSTNAME: {matching_endpoint.ident} | "
                f"IP: {matching_endpoint.ip} | DATE: {self.get_date()}\n\n")

            for host, service in active_hosts.items():
                network_file.write(f"{host} | {service}\n")

            network_file.write("=" * 50 + "\n\n")

        return active_hosts

    def call_anydesk(self) -> bool:
        self.logger.info(f'Running anydesk_command...')
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            try:
                self.logger.debug(f'Sending anydesk command to {matching_endpoint.conn}...')
                matching_endpoint.conn.send('anydesk'.encode())

                self.logger.debug(f'Waiting for response from {matching_endpoint.ip}......')
                msg = matching_endpoint.conn.recv(1024).decode()
                self.logger.debug(f'Client response: {msg}.')

                if "OK" not in msg:
                    while "OK" not in msg:
                        self.logger.debug(f'Waiting for response from {matching_endpoint.ip}...')
                        msg = matching_endpoint.conn.recv(1024).decode()
                        self.logger.debug(f'{matching_endpoint.ip}: {msg}...')

                    self.logger.debug(f'End of OK in msg loop.')
                    self.logger.info(f'anydesk_command completed.')
                    return True

                else:
                    return True

            except (WindowsError, ConnectionError, socket.error, RuntimeError) as e:
                self.logger.error(f'Connection Error: {e}.')
                self.logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                self.server.remove_lost_connection(matching_endpoint)
                return False

        else:
            return False

    def call_teamviewer(self) -> bool:
        self.logger.info(f'Running anydesk_command...')
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            try:
                self.logger.debug(f'Sending teamviewer command to {matching_endpoint.conn}...')
                matching_endpoint.conn.send('teamviewer'.encode())

                self.logger.debug(f'Waiting for response from {matching_endpoint.ip}......')
                msg = matching_endpoint.conn.recv(1024).decode()
                self.logger.debug(f'Client response: {msg}.')

                if "OK" not in msg:
                    while "OK" not in msg:
                        self.logger.debug(f'Waiting for response from {matching_endpoint.ip}...')
                        msg = matching_endpoint.conn.recv(1024).decode()
                        self.logger.debug(f'{matching_endpoint.ip}: {msg}...')

                    self.logger.debug(f'End of OK in msg loop.')
                    self.logger.info(f'teamviewer completed.')
                    return True

                else:
                    return True

            except (WindowsError, ConnectionError, socket.error, RuntimeError) as e:
                self.logger.error(f'Connection Error: {e}.')
                self.logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                self.server.remove_lost_connection(matching_endpoint)
                return False

        else:
            return False

    def call_sysinfo(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            sysinfo = Sysinfo(self.main_path, self.log_path, matching_endpoint, self.server, self.shell_target)
            if sysinfo.run():
                latest_file = max(glob.glob(os.path.join(sysinfo.local_dir, 'systeminfo*.txt')), key=os.path.getmtime)
                return str(latest_file)

        else:
            self.logger.info("No target")
            return False

    def call_tasks(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            tasks = Tasks(self.main_path, self.log_path, matching_endpoint, self.server, self.shell_target)
            if tasks.run():
                latest_file = max(glob.glob(os.path.join(tasks.local_dir, 'tasks*.txt')), key=os.path.getmtime)
                return str(latest_file)

        else:
            self.logger.info("No target")
            return False

    def tasks_post_run(self):
        data = request.json.get('data')
        task_name = data['taskName']
        if task_name:
            if not str(task_name).endswith('.exe'):
                task_name = f"{task_name}.exe"

            matching_endpoint = self.find_matching_endpoint()
            if matching_endpoint:
                matching_endpoint.conn.send('kill'.encode())
                time.sleep(0.5)
                matching_endpoint.conn.send(str(task_name).encode())
                msg = matching_endpoint.conn.recv(1024).decode()
                self.logger.info(f'{msg}')
                return jsonify({'message': f'Killed task {task_name}'}), 200

        else:
            return jsonify({'message': f'Error killing {task_name}'}), 400

    def call_restart(self, target):
        target_data = json.loads(target)
        endpoint = next((endpoint for endpoint in self.server.endpoints if endpoint.client_mac == target_data['id']), None)
        try:
            endpoint.conn.send('restart'.encode())
            time.sleep(1.2)
            self.server.remove_lost_connection(endpoint)
            return True

        except (AttributeError, RuntimeError, WindowsError, socket.error) as e:
            self.logger.error(f'Connection Error: {e}.')
            self.logger.debug(f'Calling server.remove_lost_connection({endpoint})...')
            self.server.remove_lost_connection(endpoint)
            self.logger.info(f'restart_command failed.')
            return False

    def call_update_selected_endpoint(self, target) -> bool:
        self.logger.info(f'Running update_selected_endpoint...')
        target_data = json.loads(target)
        endpoint = next((endpoint for endpoint in self.server.endpoints if endpoint.client_mac == target_data['id']),
                        None)
        try:
            endpoint.conn.send('update'.encode())
            time.sleep(1.2)
            self.server.remove_lost_connection(endpoint)
            return True

        except (RuntimeError, WindowsError, socket.error) as e:
            self.logger.error(f'Connection Error: {e}.')
            self.logger.debug(f'Calling server.remove_lost_connection({endpoint})...')
            self.server.remove_lost_connection(endpoint)
            self.logger.error(f'Update failed.')
            return False

    def find_matching_endpoint(self):
        return next((endpoint for endpoint in self.server.endpoints if endpoint.conn == self.shell_target), None)

    def get_date(self) -> str:
        d = datetime.now().replace(microsecond=0)
        dt = str(d.strftime("%d-%b-%y %I.%M.%S %p"))
        return dt

    def count_files(self, endpoint):
        self.logger.info("Running count_files()...")
        dir_path = os.path.join('static', 'images', endpoint.ident)
        file_list = os.listdir(dir_path)
        return len(file_list)
