from subprocess import Popen, PIPE
import win32com.client as win32
from datetime import datetime
from threading import Thread
import PySimpleGUI as sg
import subprocess
import threading
import PIL.Image
import socketio
import pystray
import socket
import psutil
import ctypes
import pickle
import time
import wget
import uuid
import sys
import os

# Local Modules
# from Modules.sysinfo import SystemInformation
# from Modules.maintenance import Maintenance
# from Modules.screenshot import Screenshot
# from Modules.logger import init_logger
# from Modules.tasks import Tasks


sio = socketio.Client()


class Welcome:
    def __init__(self, client):
        self.client = client
        self.ps_path = rf'{app_path}\maintenance.ps1'

    def send_mac_address(self) -> str:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                        for ele in range(0, 8 * 6, 8)][::-1])
        try:
            self.client.soc.send(mac.encode())
            self.client.soc.settimeout(intro_socket_timeout)
            message = self.client.soc.recv(buffer_size).decode()
            self.client.soc.settimeout(default_socket_timeout)

        except (WindowsError, socket.error, socket.timeout) as e:
            return False

    def send_host_name(self) -> str:
        try:
            self.client.soc.send(self.client.hostname.encode())
            self.client.soc.settimeout(intro_socket_timeout)
            message = self.client.soc.recv(buffer_size).decode()
            self.client.soc.settimeout(default_socket_timeout)

        except (WindowsError, socket.error):
            return False

    def send_current_user(self) -> str:
        try:
            self.client.soc.send(self.client.current_user.encode())
            self.client.soc.settimeout(intro_socket_timeout)
            message = self.client.soc.recv(buffer_size).decode()
            self.client.soc.settimeout(default_socket_timeout)

        except (WindowsError, socket.error) as e:
            return False

    def send_client_version(self):
        try:
            self.client.soc.send(client_version.encode())
            self.client.soc.settimeout(intro_socket_timeout)
            message = self.client.soc.recv(buffer_size).decode()
            self.client.soc.settimeout(default_socket_timeout)

        except (socket.error, WindowsError, socket.timeout) as e:
            return False

    def send_boot_time(self):
        try:
            bt = self.get_boot_time()
            self.client.soc.send(str(bt).encode())
            message = self.client.soc.recv(buffer_size).decode()

        except (socket.error, WindowsError, socket.timeout) as e:
            return False

    def get_boot_time(self):
        last_reboot = psutil.boot_time()
        return datetime.fromtimestamp(last_reboot).strftime('%d/%b/%y %H:%M:%S')

    def confirm(self):
        try:
            self.client.soc.settimeout(intro_socket_timeout)
            message = self.client.soc.recv(buffer_size).decode()
            self.client.soc.settimeout(default_socket_timeout)

        except (WindowsError, socket.error, socket.timeout) as e:
            return False

    def anydeskThread(self) -> None:
        return subprocess.call([r"C:\Program Files (x86)\AnyDesk\anydesk.exe"])

    def anydesk(self):
        # Threaded Process
        def run_ad():
            return subprocess.run(anydesk_path)

        try:
            if os.path.exists(r"C:\Program Files (x86)\AnyDesk\anydesk.exe"):
                anydeskThread = threading.Thread(target=self.anydeskThread, name="Run Anydesk")
                anydeskThread.daemon = True
                logger.debug(f"Calling anydeskThread()...")
                anydeskThread.start()
                self.client.soc.send("OK".encode())

            else:
                error = "Anydesk not installed."
                self.client.soc.send(error.encode())

                try:
                    install = self.client.soc.recv(buffer_size).decode()
                    if str(install).lower() == "y":
                        url = "https://download.anydesk.com/AnyDesk.exe"
                        destination = rf'c:\users\{os.getlogin()}\Downloads\anydesk.exe'

                        if not os.path.exists(destination):
                            self.client.soc.send("Downloading anydesk...".encode())
                            wget.download(url, destination)

                        self.client.soc.send("Running anydesk...".encode())
                        programThread = Thread(target=run_ad, name='programThread')
                        programThread.daemon = True
                        programThread.start()

                        self.client.soc.send("Anydesk Running.".encode())
                        self.client.soc.send("OK".encode())

                    else:
                        return False

                except (WindowsError, socket.error, socket.timeout) as e:
                    return False

        except FileNotFoundError as e:
            return False

    def main_menu(self):
        self.client.soc.settimeout(menu_socket_timeout)
        while True:
            try:
                command = self.client.soc.recv(buffer_size).decode()

            except (ConnectionResetError, ConnectionError,
                    ConnectionAbortedError, WindowsError, socket.error) as e:
                break

            try:
                if len(str(command)) == 0:
                    return False

                # Vital Signs
                elif str(command.lower())[:5] == "alive":
                    try:
                        self.client.soc.send('yes'.encode())

                    except (WindowsError, socket.error) as e:
                        break

                # Capture Screenshot
                elif str(command.lower())[:6] == "screen":
                    screenshot = Screenshot(self.client, log_path, app_path)
                    screenshot.run()

                # Get System Information & Users
                elif str(command.lower())[:2] == "si":
                    system = SystemInformation(self.client, log_path, app_path)
                    system.run()

                # Get Last Restart Time
                elif str(command.lower())[:2] == "lr":
                    last_reboot = psutil.boot_time()
                    try:
                        self.client.soc.send(f"{self.client.hostname} | {self.client.localIP}: "
                                             f"{self.get_boot_time()}".encode())

                    except ConnectionResetError as e:
                        break

                # Run Anydesk
                elif str(command.lower())[:7] == "anydesk":
                    self.anydesk()
                    continue

                # Task List
                elif str(command.lower())[:5] == "tasks":
                    task = Tasks(self.client, log_path, app_path)
                    task.run()

                # Restart Machine
                elif str(command.lower())[:7] == "restart":
                    os.system('shutdown /r /t 1')

                # Run Updater
                elif str(command.lower())[:6] == "update":
                    try:
                        subprocess.run(f'{updater_file}')
                        sys.exit(0)

                    except (WindowsError, socket.error) as e:
                        return False

                # Maintenance
                elif str(command.lower()) == "maintenance":
                    waiting_msg = "waiting"
                    try:
                        self.client.soc.send(waiting_msg.encode())

                    except (WindowsError, socket.error) as e:
                        return False

                    maintenance = Maintenance(self.ps_path, self.client, log_path)
                    maintenance.maintenance()
                    self.client.connection()
                    self.main_menu()

                # Close Connection
                elif str(command.lower())[:4] == "exit":
                    self.client.soc.settimeout(1)
                    # sys.exit(0)     # CI CD
                    break  # CICD

            except (Exception, socket.error, socket.timeout) as err:
                break


class Client:
    def __init__(self, server, soc):
        self.server_host = server[0]
        self.server_port = server[1]
        self.current_user = os.getlogin()
        self.hostname = socket.gethostname()
        self.localIP = str(socket.gethostbyname(self.hostname))
        self.soc = soc

        if not os.path.exists(f'{app_path}'):
            os.makedirs(app_path)

    def connection(self) -> None:
        try:
            self.soc.connect((self.server_host, self.server_port))

        except (TimeoutError, WindowsError, ConnectionAbortedError, ConnectionResetError, socket.timeout) as e:
            return False

    def welcome(self):
        endpoint_welcome = Welcome(self)
        endpoint_welcome.send_mac_address()
        endpoint_welcome.send_host_name()
        endpoint_welcome.send_current_user()
        endpoint_welcome.send_client_version()
        endpoint_welcome.send_boot_time()
        endpoint_welcome.confirm()
        endpoint_welcome.main_menu()
        return True


def on_clicked(icon, item):
    if str(item) == "About":
        layout = [[sg.Text("By Gil Shwartz\n@2022")], [sg.Button("OK")]]
        window = sg.Window("About", layout)
        window.set_icon('client.ico')

        while True:
            event, values = window.read()
            # End program if user closes window or
            # presses the OK button
            if event == "OK" or event == sg.WIN_CLOSED:
                break

        window.close()


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


def web_connect():
    sio.connect(f'http://127.0.0.1:8000')
    sio.wait()


def main():
    # Configure system tray icon
    # icon_image = PIL.Image.open(rf"{app_path}\client.png")
    # icon = pystray.Icon("HandsOff", icon_image, menu=pystray.Menu(
    #     pystray.MenuItem("About", on_clicked)
    # ))

    # Show system tray icon
    # logger.info("Displaying HandsOff icon...")
    # iconThread = Thread(target=icon.run, name="Icon Thread")
    # iconThread.daemon = True
    # iconThread.start()
    #
    server = ('192.168.1.10', 55400)

    # Start Client
    while True:
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            client = Client(server, soc)

            soc.settimeout(default_socket_timeout)
            soc.connect(server)
            client.welcome()
            Thread(target=web_connect, daemon=True).start()

        except (WindowsError, socket.error) as e:
            soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            soc.close()
            time.sleep(1)


if __name__ == "__main__":
    client_version = "1.0.0"
    app_path = r'c:\HandsOff'
    updater_file = rf'{app_path}\updater.exe'
    log_path = fr'{app_path}\client_log.txt'
    powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    anydesk_path = rf'c:\users\{os.getlogin()}\Downloads\anydesk.exe'

    default_socket_timeout = None
    menu_socket_timeout = None
    intro_socket_timeout = 10
    buffer_size = 1024

    if not os.path.exists(app_path):
        os.makedirs(app_path)

    main()
