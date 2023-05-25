FROM python:3.11 AS base

LABEL maintainer="Gil Shwartz <https://www.linkedin.com/in/gilshwartz/>"
LABEL version="1.0.0"

WORKDIR /app

COPY . /app

ARG DEFAULT_MAIN_PATH="HandsOff"
ENV MAIN_PATH=${MAIN_PATH:-$DEFAULT_MAIN_PATH}

ARG DEFAULT_WEB_PORT=8000
ENV WEB_PORT=${WEB_PORT:-$DEFAULT_WEB_PORT}

ARG DEFAULT_SERVER_IP="0.0.0.0"
ENV SERVER_IP=${SERVER_IP:-$DEFAULT_SERVER_IP}

ARG DEFAULT_SERVER_PORT=55400
ENV SERVER_PORT=${SERVER_PORT:-$DEFAULT_SERVER_PORT}

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

VOLUME ["/app/static"]

EXPOSE $WEB_PORT $SERVER_PORT


# Build stage for Linux
FROM base AS linux

CMD python main.py -wp $WEB_PORT -sp $SERVER_PORT -mp $MAIN_PATH -ip $SERVER_IP


# Build stage for Windows
FROM base AS windows

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

CMD python main.py -wp $env:WEB_PORT -sp $env:SERVER_PORT -mp $env:MAIN_PATH -ip $env:SERVER_IP


# Determine the build stage based on the OS
FROM linux AS final
RUN echo "Linux"
COPY --from=linux /app /app

FROM windows AS final
RUN echo "Windows"
COPY --from=windows /app /app
