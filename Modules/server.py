from Modules.logger import init_logger
from datetime import datetime
from threading import Thread
import socket
import json
import time
import os


class Endpoints:
    def __init__(self, conn, client_mac, ip, ident, user, client_version, os_release, boot_time, connection_time):
        self.boot_time = boot_time
        self.conn = conn
        self.client_mac = client_mac
        self.ip = ip
        self.ident = ident
        self.user = user
        self.client_version = client_version
        self.os_release = os_release
        self.connection_time = connection_time

    def __repr__(self):
        return f"Endpoint({self.conn}, {self.client_mac}, " \
               f"{self.ip}, {self.ident}, {self.user}, " \
               f"{self.client_version}, {self.os_release}, {self.boot_time}, {self.connection_time})"


class Server:
    def __init__(self, ip, port, log_path):
        self.log_path = log_path
        self.port = port
        self.serverIP = ip
        self.hostname = socket.gethostname()
        self.connHistory = {}
        self.endpoints = []

        self.logger = init_logger(self.log_path, __name__)

    # Server listener
    def listener(self) -> None:
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.logger.debug(f'Binding {self.serverIP}, {self.port}...')
        self.server.bind((self.serverIP, int(self.port)))
        self.server.listen()

        self.logger.info(f'Running run...')
        self.logger.debug(f'Starting connection thread...')
        self.connectThread = Thread(target=self.connect,
                                    daemon=True,
                                    name=f"Connect Thread")
        self.connectThread.start()

    # Listen for connections and sort new connections to designated lists/dicts
    def connect(self) -> None:
        self.logger.info(f'Running connect...')
        while True:
            dt = self.get_date()
            self.logger.debug(f'Accepting connection...')
            self.conn, (self.ip, self.port) = self.server.accept()
            self.logger.debug(f'Connection from {self.ip} accepted.')
            self.logger.info(f'Running welcome_message...')
            self.welcome = "Connection Established!"
            self.logger.debug(f'Sending welcome message...')
            self.conn.send(f"@Server: {self.welcome}".encode())
            self.logger.debug(f'"{self.welcome}" sent to {self.conn}.')

            self.logger.debug(f'Waiting for handshake data...')
            received_data = self.conn.recv(1024).decode()
            handshake = json.loads(received_data)

            self.logger.debug(f'handshake: {handshake}')
            self.client_mac = handshake['mac_address']
            self.logger.debug(f'MAC: {self.client_mac}.')
            self.ident = handshake['hostname']
            self.logger.debug(f'Station name: {self.hostname}.')
            self.user = handshake['current_user']
            self.logger.debug(f'Logged user: {self.ident}.')
            self.client_version = handshake['client_version']
            self.logger.debug(f'Client version: {self.client_version}.')
            self.os_release = handshake['os_platform']
            self.logger.debug(f'OS Platform: {self.os_release}.')
            self.bt = handshake['boot_time']
            self.logger.debug(f"Client Boot time: {handshake['boot_time']}.")

            # Apply Data to dataclass Endpoints
            self.logger.debug(f'Defining fresh endpoint data...')
            self.fresh_endpoint = Endpoints(self.conn, self.client_mac, self.ip,
                                            self.ident, self.user, self.client_version, self.os_release,
                                            self.bt, self.get_date())
            self.logger.debug(f'Fresh Endpoint: {self.fresh_endpoint}')

            if self.fresh_endpoint not in self.endpoints:
                self.logger.debug(f'{self.fresh_endpoint} not in endpoints list. adding...')
                self.endpoints.append(self.fresh_endpoint)

            self.logger.debug(f'Updating connection history dict...')
            self.connHistory.update({self.fresh_endpoint: dt})

            self.logger.info(f'connect completed.')
            self.logger.info(f'Running CICD Thread...')
            Thread(target=cicd, args=(self.conn,), daemon=True, name="CICD Thread").start()

    # Get human readable datetime
    def get_date(self) -> str:
        d = datetime.now().replace(microsecond=0)
        dt = str(d.strftime("%d/%b/%y %H:%M:%S"))
        return dt

    # Check vital signs
    def check_vital_signs(self, endpoint):
        self.callback = 'yes'
        self.logger.debug(f'Checking {endpoint.ip}...')

        try:
            endpoint.conn.send('alive'.encode())
            ans = endpoint.conn.recv(1024).decode()

        except (Exception, socket.error, UnicodeDecodeError) as e:
            self.logger.debug(f'removing {endpoint}...')
            self.remove_lost_connection(endpoint)
            return

        if str(ans) == str(self.callback):
            try:
                self.logger.debug(f'Station IP: {endpoint.ip} | Station Name: {endpoint.ident} - ALIVE!')
            except (IndexError, RuntimeError):
                return

        else:
            try:
                self.logger.debug(f'removing {endpoint}...')
                self.remove_lost_connection(endpoint)

            except (IndexError, RuntimeError):
                return

    # Run vital signs
    def vital_signs(self) -> bool:
        self.logger.info(f'Running vital_signs...')
        if not self.endpoints:
            self.logger.debug(f'Updating statusbar message: No connected stations.')
            self.app.update_statusbar_messages_thread(msg='No connected stations.')
            return False

        self.callback = 'yes'
        self.logger.debug(f'Updating statusbar message: running vitals check....')
        threads = []
        for endpoint in self.endpoints:
            thread = Thread(target=self.check_vital_signs, args=(endpoint,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        self.logger.debug(f'Updating statusbar message: Vitals check completed.')
        self.logger.info(f'=== End of vital_signs() ===')
        return True

    # Remove Lost connections
    def remove_lost_connection(self, endpoint) -> bool:
        self.logger.info(f'Running remove_lost_connection({endpoint})...')
        try:
            self.logger.debug(f'Removing {endpoint.ip} | {endpoint.ident}...')
            endpoint.conn.close()
            self.endpoints.remove(endpoint)

            # Update statusbar message
            self.logger.info(f'=== End of remove_lost_connection({endpoint}) ===')
            return True

        except (ValueError, RuntimeError) as e:
            self.logger.error(f'Error: {e}.')


def cicd(soc):
    while True:
        exit_command = input('>')
        if exit_command == 'exit':
            soc.send('exit'.encode())
            break

        else:
            continue
