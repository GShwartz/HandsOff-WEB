import getpass
from datetime import datetime
import socketio
import socket
import psutil
from threading import Thread
import time

sio = socketio.Client()


def last_boot():
    last_reboot = psutil.boot_time()
    bt = datetime.fromtimestamp(last_reboot).strftime('%d/%b/%y %H:%M:%S %p')
    return bt


@sio.on('connect')
def on_connect():
    print('Connected to server')
    client_hostname = socket.gethostname()
    ip_address = socket.gethostbyname(client_hostname)
    logged_user = getpass.getuser()
    boot_time = last_boot()

    # Send client information to the server
    sio.emit('client_info', {'ip_address': ip_address,
                             'hostname': client_hostname,
                             'logged_user': logged_user,
                             'boot_time': boot_time,
                             'client_version': version
                             })


def keep_alive():
    while True:
        sio.send('heartbeat')
        time.sleep(10)


# Wait for events
def main():
    # Connect to the server
    sio.connect('http://127.0.0.1:5000')

    while True:
        heartbeat = Thread(target=keep_alive, name="Keep Alive", daemon=True).start()
        sio.wait()


if __name__ == "__main__":
    version = "1.00"
    main()
