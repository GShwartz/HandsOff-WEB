FROM python:3.11

LABEL maintainer="Gil Shwartz"
LABEL version="1.0.0"
LABEL description="HandsOff the mouse and keyboard sir/lady!"

WORKDIR /app

COPY . /app

ARG DEFAULT_MAIN_PATH="c:\HandsOff"
ENV MAIN_PATH=${MAIN_PATH:-$DEFAULT_MAIN_PATH}

ARG DEFAULT_WEB_PORT=8000
ENV WEB_PORT=${WEB_PORT:-$DEFAULT_WEB_PORT}

ARG DEFAULT_SERVER_IP="0.0.0.0"
ENV SERVER_IP=${SERVER_IP:-DEFAULT_SERVER_IP}

ARG DEFAULT_SERVER_PORT=55400
ENV SERVER_PORT=${SERVER_PORT:-DEFAULT_SERVER_PORT}

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

ARG INSTALL_PYINSTALLER=false
RUN if [ "$INSTALL_PYINSTALLER" = "true" ]; then pip install pyinstaller; fi

RUN mv main.py handsoff.py

RUN if [ "$INSTALL_PYINSTALLER" = "true" ]; then pyinstaller -F --icon=src/handsoff.ico handsoff.py; fi

EXPOSE $WEB_PORT $SERVER_PORT

# Run mainWeb.py or handsoff.exe depending on the value of INSTALL_PYINSTALLER
ENTRYPOINT if [ "$INSTALL_PYINSTALLER" = "true" ]; then ./dist/handsoff.exe "${MAIN_PATH}" "${WEB_PORT}" "${SERVER_IP}" "${SERVER_PORT}"; else python main.py "${MAIN_PATH}" "${WEB_PORT}" "${SERVER_IP}" "${SERVER_PORT}"; fi
