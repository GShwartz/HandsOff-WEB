FROM python:3.11-slim AS base

LABEL maintainer="Gil Shwartz <https://www.linkedin.com/in/gilshwartz/>"
LABEL version="1.0.0"

WORKDIR /app

COPY . /app

ARG DEFAULT_MAIN_PATH="/HandsOff"
ENV MAIN_PATH=${MAIN_PATH:-$DEFAULT_MAIN_PATH}

ARG DEFAULT_WEB_PORT=8000
ENV WEB_PORT=${WEB_PORT:-$DEFAULT_WEB_PORT}

ARG DEFAULT_SERVER_IP="0.0.0.0"
ENV SERVER_IP=${SERVER_IP:-$DEFAULT_SERVER_IP}

ARG DEFAULT_SERVER_PORT=55400
ENV SERVER_PORT=${SERVER_PORT:-$DEFAULT_SERVER_PORT}

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

VOLUME ["/static"]

EXPOSE $WEB_PORT $SERVER_PORT

# Create an entrypoint script
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'if [ "$(uname -s)" = "Linux" ]; then' >> /entrypoint.sh && \
    echo '    exec python main.py -wp "$WEB_PORT" -sp "$SERVER_PORT" -mp "$MAIN_PATH" -ip "$SERVER_IP"' >> /entrypoint.sh && \
    echo 'else' >> /entrypoint.sh && \
    echo '    exec python main.py -wp "$WEB_PORT" -sp "$SERVER_PORT" -mp "$MAIN_PATH" -ip "$SERVER_IP"' >> /entrypoint.sh && \
    echo 'fi' >> /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]