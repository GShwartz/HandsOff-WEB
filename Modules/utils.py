from Modules.logger import init_logger
import platform
import sys
import os


class Handlers:
    def __init__(self,  log_path, app_path, endpoint):
        self.log_path = log_path
        self.app_path = app_path
        self.endpoint = endpoint
        self.logger = init_logger(self.log_path, __name__)

    def handle_local_dir(self):
        self.ident_path = os.path.join(self.app_path, self.endpoint.ident)
        self.local_dir = os.path.join('static', 'images', self.endpoint.ident)
        if not os.path.isdir(self.ident_path):
            try:
                os.makedirs(str(self.ident_path), exist_ok=True)

            except Exception as e:
                print(f"Failed to create directory '{self.local_dir}': {e}")
                sys.exit(1)

        if not os.path.isdir(self.local_dir):
            try:
                os.makedirs(str(self.local_dir), exist_ok=True)

            except Exception as e:
                print(f"Failed to create directory '{self.local_dir}': {e}")
                sys.exit(1)

        return self.local_dir

    def clear_local(self):
        path = os.path.join('static', 'images', self.endpoint.ident)
        if os.path.isdir(path):
            files = os.listdir(path)
            for file_name in files:
                file_path = os.path.join(path, file_name)

                # Use platform-specific file removal
                self.remove_file(file_path)
            return True

        else:
            return False

    def remove_file(self, file_path):
        if platform.system() == 'Windows':
            try:
                os.remove(file_path)

            except OSError as e:
                print(f"Error deleting file: {e}")
                return False

        elif platform.system() == 'Linux' or platform.system() == 'Darwin':
            try:
                os.unlink(file_path)

            except OSError as e:
                print(f"Error deleting file: {e}")
                return False
        else:
            print("Unsupported platform")
            return False
