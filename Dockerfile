FROM python:3.11

WORKDIR /app

COPY . /app

ARG DEFAULT_PORT=8000
ENV PORT=${PORT:-$DEFAULT_PORT}

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

EXPOSE $PORT 55400

# Run app.py when the container launches
ENTRYPOINT ["python", "mainWeb.py", "${PORT}"]