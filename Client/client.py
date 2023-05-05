import getpass
from datetime import datetime
import socketio
import socket
import psutil

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
                             'boot_time': boot_time
                             })


# Connect to the server
sio.connect('http://127.0.0.1:5000')

# Wait for events
sio.wait()
