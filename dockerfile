# Use an official Python runtime as a parent image
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN cp /app/config4docker.yaml /app/config.yaml
RUN touch /app/webhooks.txt /app/host_key

EXPOSE 8022

# Run expose_sftp.py when the container launches
CMD ["python", "expose_sftp.py"]
