FROM python:3.11-alpine AS base

LABEL maintainer="Gil Shwartz <https://www.linkedin.com/in/gilshwartz/>"
LABEL version="1.0.0"

WORKDIR /app

# Copy the entire project
COPY . .

# Install dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt && \
    apk del gcc musl-dev libffi-dev openssl-dev

# Set environment variables
ARG DEFAULT_MAIN_PATH="/server"
ENV MAIN_PATH=${MAIN_PATH:-$DEFAULT_MAIN_PATH}
ARG DEFAULT_WEB_PORT=8000
ENV WEB_PORT=${WEB_PORT:-$DEFAULT_WEB_PORT}
ARG DEFAULT_SERVER_IP="0.0.0.0"
ENV SERVER_IP=${SERVER_IP:-$DEFAULT_SERVER_IP}
ARG DEFAULT_SERVER_PORT=55400
ENV SERVER_PORT=${SERVER_PORT:-$DEFAULT_SERVER_PORT}

VOLUME ["/app/static"]

# Expose ports
EXPOSE $WEB_PORT $SERVER_PORT

# Create an entrypoint script
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'exec python main.py -wp "$WEB_PORT" -sp "$SERVER_PORT" -mp "$MAIN_PATH" -ip "$SERVER_IP"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
