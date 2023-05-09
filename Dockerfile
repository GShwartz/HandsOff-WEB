# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY Modules/logger.py /app/Modules/logger.py
COPY Modules/server.py /app/Modules/server.py
COPY static /app/static
COPY templates /app/templates


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
ENTRYPOINT ["python", "mainWeb.py"]