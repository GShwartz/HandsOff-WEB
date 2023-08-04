# HandsOff-Server
<img src="https://github.com/GShwartz/HandsOff-WEB/blob/main/src/02-connected.jpg?raw=true" alt="Connected" width="800" height="450">

* Compatible with windows OS and Debian (tested on Ubuntu 22.04 with docker-ce).

### Base Image
The base image used in this Dockerfile is `python:3.11`. This ensures that the container has Python 3.11 installed as the runtime environment.

### Environment Variables
The Dockerfile defines several environment variables that can be customized during container runtime:

- `MAIN_PATH`: Specifies the main path for the application. The default value is set to `/HandsOff`. You can override this value by setting the `MAIN_PATH` environment variable when running the container.

- `WEB_PORT`: Sets the web server port number. The default value is `8000`. You can change this value by setting the `WEB_PORT` environment variable during container runtime.

- `SERVER_IP`: Defines the IP address the server should bind to. The default value is `"0.0.0.0"`, which means the server will bind to all available network interfaces. You can modify this value by setting the 
`SERVER_IP` environment variable.

- `SERVER_PORT`: Specifies the server port number. The default value is `55400`. You can customize this value by setting the `SERVER_PORT` environment variable during container runtime.

### Exposing Ports
The Dockerfile exposes the ports specified by the `WEB_PORT` and `SERVER_PORT` environment variables. This allows inbound connections to the container on these ports.

### Clone App
```
git clone https://github.com/GShwartz/HandsOff-WEB.git
```

### Defining Environment
Create a new .env file inside the app's dir.
copy & paste the following:
```
SERVER_VERSION="1.0.0"
LOG_FILE="server_log.txt"
SERVER_IP="0.0.0.0"
SERVER_PORT=<port>
WEB_PORT=<port>
SERVER_URL=""
MAIN_PATH=""
SECRET_KEY=<"your secret key">
USER=<your username>
PASSWORD=<your password>
```
add & change the values to fit your needs.

### Building the Image
To build the Docker image using this Dockerfile, run the following command in the directory where

the Dockerfile and application code are located:
```
docker build -t your_image_name:tag .
```
Replace `your_image_name` with the desired name for your image and `tag` with a version or tag name.

### Running the Container
To run a container based on the built image, use the following command:
```
docker run -p host_port:container_port -e MAIN_PATH=/custom_path -e WEB_PORT=custom_web_port -e SERVER_IP=custom_server_ip -e SERVER_PORT=custom_server_port -v /host/path:/app/static your_image_name:tag
```
- Replace `host_port` with the desired port number on the host machine that will be mapped to the `WEB_PORT` and `SERVER_PORT` of the container.
- Specify any custom values for `MAIN_PATH`, `WEB_PORT`, `SERVER_IP`, and `SERVER_PORT` using the `-e` flag followed by the environment variable name and value.
- Replace `/host/path` with the path on the host machine that you want to map to the `/app/static` directory in the container.
- Finally, provide the name and tag of the Docker image you built with `your_image_name:tag`.

or if you chose the .env way
```
docker run -d -p <host_web_port:container_port> -p <host_server_port>:<container_server_port> --restart=always -v <local/path>:/static/images <image-name:tag>
```

After running the container, you can access the application by opening a web browser and visiting http://url:<host_web_port>. 
The application should be up and running, allowing you to interact with it. <br /> <br />

