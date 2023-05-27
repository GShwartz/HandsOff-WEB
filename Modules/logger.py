import logging
import logging.handlers
import platform
import queue
import os


def init_logger(log_path, name):
    log_queue = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # Set the log level for the logger
        logger.propagate = False
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        try:
            if platform.system() == 'Windows':
                # Convert forward slashes to backslashes for Windows file path
                log_path = log_path.replace('/', '\\')
                info = logging.FileHandler(log_path)
            else:
                info = logging.FileHandler(log_path)

        except FileNotFoundError:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w') as file:
                pass

        except FileExistsError:
            pass

        info.setFormatter(formatter)  # Set the formatter for the file handler
        logger.addHandler(info)

    return logger
