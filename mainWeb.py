from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

from dotenv import load_dotenv, dotenv_values

from datetime import datetime
import psutil
import socket
import getpass
import os

# Local Modules
from Modules.maintenance import Maintenance
from Modules.screenshot import Screenshot
from Modules.logger import init_logger
from Modules.commands import Commands
from Modules.sysinfo import Sysinfo
from Modules.server import Server
from Modules.about import About
from Modules.tasks import Tasks

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*",
                    transports=['websocket', 'polling'])


class Endpoints:
    def __init__(self, room, client_ip, hostname, logged_user, boot_time, version):
        self.id = room
        self.boot_time = boot_time
        self.ip_address = client_ip
        self.hostname = hostname
        self.logged_user = logged_user
        self.client_version = version

    def __repr__(self):
        return f"Endpoint({self.id}, {self.ip_address}, {self.hostname}, " \
               f"{self.logged_user}, {self.boot_time}, {self.client_version})"


@app.route('/')
def index():
    serving_on = os.getenv('URL')
    hostname = socket.gethostname()
    server_ip = str(socket.gethostbyname(hostname))
    server_port = os.getenv('PORT')
    boot_time = last_boot()
    connected_stations = len(server.endpoints)

    return render_template('index.html',
                           serving_on=serving_on,
                           server_ip=server_ip,
                           server_port=server_port,
                           boot_time=boot_time,
                           connected_stations=connected_stations,
                           endpoints=endpoints)


@socketio.on('client_info')
def handle_client_info(client_info):
    client_id = request.sid

    fresh_endpoint = Endpoints(client_id,
                               client_info["ip_address"],
                               client_info["hostname"],
                               client_info["logged_user"],
                               client_info["boot_time"],
                               client_info['client_version'])

    history[get_date()] = fresh_endpoint
    if fresh_endpoint not in endpoints:
        endpoints.append(fresh_endpoint)

    for count, endpoint in enumerate(endpoints):
        if count == 0:
            count += 1

        print(f"#{count} | ID: {endpoint.id} | IP: {endpoint.ip_address} | "
              f"Hostname: {endpoint.hostname} | "
              f"Logged User: {endpoint.logged_user} | "
              f"Boot Time: {endpoint.boot_time} | "
              f"Client_Version: {endpoint.client_version}")

    for t, endpoint in history.items():
        print(f"History\n{t} | IP: {endpoint.ip_address} | "
              f"Hostname: {endpoint.hostname} | "
              f"Logged User: {endpoint.logged_user} | "
              f"Boot Time: {endpoint.boot_time} | "
              f"Client_Version: {endpoint.client_version}")


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('message')
def handle_message(message):
    print('Received message: ' + message)


def last_boot():
    last_reboot = psutil.boot_time()
    bt = datetime.fromtimestamp(last_reboot).strftime('%d/%b/%y %H:%M:%S %p')
    return bt


def get_date() -> str:
    d = datetime.now().replace(microsecond=0)
    dt = str(d.strftime("%d/%b/%y %H:%M:%S"))
    return dt


if __name__ == '__main__':
    endpoints = []
    history = {}
    socketio.run(app, allow_unsafe_werkzeug=True)
