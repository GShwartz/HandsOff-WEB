import getpass
import os.path
from datetime import datetime
import socketio
import socket
import psutil
from threading import Thread
import time
import win32con
import win32gui
import win32ui
import requests

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


@sio.on('message')
def handle_message(message):
    print('Received message: ' + message)


def get_screenshot():
    client_hostname = socket.gethostname()
    ip_address = socket.gethostbyname(client_hostname)

    file_path = r'c:/HandsOff'
    file_name = f'screenshot {ip_address} {get_date()}.jpg'
    filename = os.path.join(file_path, file_name)

    desktop = win32gui.GetDesktopWindow()

    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77

    width = ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    height = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    left = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    top = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)

    desktop_dc = win32gui.GetWindowDC(desktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)

    mem_dc = img_dc.CreateCompatibleDC()
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

    screenshot.SaveBitmapFile(mem_dc, filename)
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())

    with open(filename, 'rb') as f:
        file_data = f.read()

    headers = {
        'Content-Type': 'multipart/form-data',
    }

    data = {
        'file': (filename, file_data, 'image/jpeg'),
        'file_name': file_name,
        'file_size': len(file_data),
        'file_type': 'image/jpeg'
    }

    response = requests.post('http://localhost:5000/receive-file', headers=headers, data=data)
    print(response.text)


def get_date() -> str:
    d = datetime.now().replace(microsecond=0)
    dt = str(d.strftime("%d.%b.%y %H.%M.%S"))
    return dt


def keep_alive():
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
