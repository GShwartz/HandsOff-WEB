import logging
import logging.handlers
import platform
import queue
import os


def init_logger(log_path, name):
    print(log_path)
    log_queue = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        try:
            if platform.system() == 'Windows':
                # Windows-specific log file path
                log_path = log_path.replace('/', '\\')
            info = logging.FileHandler(log_path)

        except FileNotFoundError:
            with open(log_path, 'w') as file:
                pass

        except FileExistsError:
            pass

        info.setLevel(logging.DEBUG)
        info.setFormatter(formatter)
        logger.addHandler(info)

    return logger
