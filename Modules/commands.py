from flask import request, jsonify
import socket
import time

from Modules.logger import init_logger
from Modules.screenshot import Screenshot
from Modules.sysinfo import Sysinfo
from Modules.tasks import Tasks


class Commands:
    def __init__(self, logger, main_path, log_path, server, shell_target):
        self.logger = logger
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.shell_target = shell_target

    def call_screenshot(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            sc = Screenshot(self.main_path, self.log_path, matching_endpoint, self.server, self.shell_target)
            sc.run()

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
                    self.logger.debug(f'Updating statusbar message...')
                    self.logger.debug(f'Display popup confirmation for install anydesk...')
                    install_ad = input("Install Anydesk?")
                    install_ad = install_ad == 'yes'

                    self.logger.debug(f'Install anydesk: {install_ad}.')
                    if install_ad:
                        self.logger.debug(f'Updating statusbar message...')
                        self.logger.debug(f'Sending install command to {matching_endpoint.conn}')
                        matching_endpoint.conn.send('y'.encode())
                        while "OK" not in msg:
                            self.logger.debug(f'Waiting for response from {matching_endpoint.ip}...')
                            msg = matching_endpoint.conn.recv(1024).decode()
                            self.logger.debug(f'{matching_endpoint.ip}: {msg}...')

                        self.logger.debug(f'End of OK in msg loop.')
                        self.logger.info(f'anydesk_command completed.')

                    else:
                        self.logger.debug(f'Sending cancel command to {matching_endpoint.conn}...')
                        matching_endpoint.conn.send('n'.encode())
                        return

                else:
                    self.logger.info("anydesk running...")
                    self.logger.info(f'anydesk_command completed.')
                    return True

            except (WindowsError, ConnectionError, socket.error, RuntimeError) as e:
                self.logger.error(f'Connection Error: {e}.')
                self.logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                self.server.remove_lost_connection(matching_endpoint)
                return False

    def call_sysinfo(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            sysinfo = Sysinfo(self.main_path, self.log_path, matching_endpoint, self.server, self.shell_target)
            sysinfo.run()

        else:
            self.logger.info("No target")
            return False

    def call_tasks(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            self.tasks = Tasks(self.main_path, self.log_path, matching_endpoint)
            self.tasks.run()

    def tasks_post_run(self):
        task_name = request.json.get('taskName')
        if task_name:
            self.tasks.kill_task(task_name)
            return jsonify({'message': f'Killed task {task_name}'}), 200

        else:
            return jsonify({'error': 'No task name provided'}), 400

    def call_restart(self):
        matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            self.logger.info(f'Running restart_command...')
            self.logger.debug(f'Displaying confirmation...')

            try:
                self.logger.debug(f'Sending restart command to {matching_endpoint.ip}...')
                matching_endpoint.conn.send('restart'.encode())
                self.logger.debug(f'Sleeping for 1.2s...')
                time.sleep(1.2)
                self.server.remove_lost_connection(matching_endpoint)
                self.logger.info(f'restart_command completed.')
                return True

            except (RuntimeError, WindowsError, socket.error) as e:
                self.logger.error(f'Connection Error: {e}.')
                self.logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                self.server.remove_lost_connection(matching_endpoint)
                self.logger.info(f'restart_command failed.')
                return False

        else:
            return False

    def call_update_selected_endpoint(self) -> bool:
        self.logger.info(f'Running update_selected_endpoint...')
        self.matching_endpoint = self.find_matching_endpoint()
        if matching_endpoint:
            try:
                self.logger.debug(f'Sending update command to {matching_endpoint.ip} | {matching_endpoint.ident}...')
                matching_endpoint.conn.send('update'.encode())
                self.server.remove_lost_connection(matching_endpoint)
                if isinstance(self.shell_target, list):
                    self.shell_target = []
                self.logger.info(f'update_selected_endpoint completed.')
                return True

            except (RuntimeError, WindowsError, socket.error) as e:
                self.logger.error(f'Connection Error: {e}.')
                self.logger.debug(f'Calling server.remove_lost_connection({matching_endpoint})...')
                self.server.remove_lost_connection(matching_endpoint)
                return False

    def find_matching_endpoint(self):
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.shell_target:
                return endpoint
        return None