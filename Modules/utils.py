from Modules.logger import init_logger
import sys
import os


class Handlers:
    def __init__(self,  log_path, sub_path, endpoint):
        self.log_path = log_path
        self.sub_path = sub_path
        self.endpoint = endpoint
        self.logger = init_logger(self.log_path, __name__)

    def handle_local_dir(self):
        self.ident_path = os.path.join(self.sub_path, self.endpoint.ident)
        self.local_dir = os.path.join('static', 'images', self.endpoint.ident)
        try:
            os.makedirs(str(self.ident_path), exist_ok=True)
            os.makedirs(str(self.local_dir), exist_ok=True)

        except Exception as e:
            print(f"Failed to create directory '{self.local_dir}': {e}")
            sys.exit(1)

        return self.local_dir
