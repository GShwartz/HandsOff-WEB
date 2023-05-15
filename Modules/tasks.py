import socket
import shutil
import sys
import os

from Modules.logger import init_logger


class Tasks:
    def __init__(self, path, log_path, endpoint, server, shell_target):
        self.endpoint = endpoint
        self.path = path
        self.log_path = log_path
        self.server = server
        self.shell_target = shell_target
        self.tasks_file_path = os.path.join(self.path, self.endpoint.ident)
        self.logger = init_logger(self.log_path, __name__)

    def create_local_dir(self):
        local_dir = os.path.join('static', 'images', self.endpoint.ident)
        if not os.path.exists(local_dir):
            try:
                os.makedirs(str(local_dir), exist_ok=True)

            except Exception as e:
                print(f"Failed to create directory '{local_dir}': {e}")

        return local_dir

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def display_text(self):
        self.logger.info(f"Running display_text...")
        os.startfile(self.full_file_path)

    def kill_task(self, taskname):
        self.logger.debug(f"Running kill_task...")
        try:
            self.logger.debug(f"Sending kill command to {self.endpoint.ip}...")
            self.endpoint.conn.send('kill'.encode())

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

        try:
            self.logger.debug(f"Sending {str(taskname)} to {self.endpoint.ip}...")
            self.endpoint.conn.send(str(taskname).encode())

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

        try:
            self.logger.debug(f"Waiting for confirmation from {self.endpoint.ip}...")
            msg = self.endpoint.conn.recv(1024).decode()
            self.logger.debug(f"{self.endpoint.ip}: {msg}")
            self.logger.debug(f"Displaying {msg} in popup window...")
            print(f"{self.endpoint.ip} | {self.endpoint.ident}: ", f"{msg}")
            return True

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def get_file_name(self):
        self.logger.info(f"Running get_file_name...")
        self.logger.debug(f"Waiting for filename from {self.endpoint.ip}...")
        self.endpoint.conn.settimeout(10)
        self.filenameRecv = self.endpoint.conn.recv(1024).decode()
        self.full_file_path = os.path.join(self.tasks_file_path, self.filenameRecv)
        self.endpoint.conn.settimeout(None)
        self.logger.debug(f"Filename: {self.filenameRecv}")

    def get_file_size(self):
        self.logger.info(f"Running get_file_size...")
        self.logger.debug(f"Waiting for file size from {self.endpoint.ip}...")
        self.endpoint.conn.settimeout(10)
        self.size = self.endpoint.conn.recv(4)
        self.endpoint.conn.settimeout(None)
        self.size = self.bytes_to_number(self.size)
        self.logger.debug(f"Size: {self.size}")

    def get_file_content(self):
        self.logger.info(f"Running get_file_content...")

        current_size = 0
        buffer = b""

        self.logger.debug(f"Writing content to {self.full_file_path}...")
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
        self.logger.info(f"Running confirm...")
        self.logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
        self.endpoint.conn.send(f"Received file: {self.filenameRecv}\n".encode())
        self.endpoint.conn.settimeout(10)
        msg = self.endpoint.conn.recv(1024).decode()
        self.endpoint.conn.settimeout(None)
        self.logger.debug(f"{self.endpoint.ip}: {msg}")

    def run(self):
        self.logger.info(f"Running run...")
        self.filepath = os.path.join(self.path, self.endpoint.ident)
        try:
            os.makedirs(str(self.filepath), exist_ok=True)

        except Exception as e:
            print(f"Failed to create directory '{self.filepath}': {e}")
            sys.exit(1)

        try:
            self.logger.debug(f"Sending tasks command to {self.endpoint.ip}...")
            self.endpoint.conn.send('tasks'.encode())

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling server.remove_lost_connection({self.endpoint})")
            self.server.remove_lost_connection(self.endpoint)
            return False

        self.logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        self.logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        self.logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        self.logger.debug(f"Calling confirm...")
        self.confirm()

        src = os.path.join(self.filepath, self.filenameRecv)
        for endpoint in self.server.endpoints:
            if endpoint.conn == self.shell_target:
                endpoint_ident = endpoint.ident
                local_dir = self.create_local_dir()
                shutil.copy(src, local_dir)

        self.logger.debug(f"Calling display_text...")
        self.display_text()
        self.logger.info(f"run completed.")
