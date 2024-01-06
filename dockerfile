# Use an official Python runtime as a parent image
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN cp /app/.conf/config4docker.yaml /app/.conf/config.yaml
RUN touch /app/.conf/webhooks.txt /app/.conf/host_key

EXPOSE 8022

# Run expose_sftp.py when the container launches
CMD ["python", "expose_sftp.py"]
