FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8000

# Run app.py when the container launches
ENTRYPOINT ["python", "mainWeb.py"]