# Use an official Python runtime as a parent image
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir docker-systemctl-replacement

RUN systemctl.py status

RUN apt-get update && apt-get install -y git gnupg curl

COPY . .

RUN cp /app/config4docker.yaml /app/config.yaml

RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor
RUN echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
RUN apt-get update && apt-get install -y mongodb-org

# Expose the required port (if your Python script uses a specific port)
EXPOSE 8022

RUN chmod +x start.sh

# Run expose_sftp.py when the container launches
CMD ["python", "expose_sftp.py"]
