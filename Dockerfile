# Use Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

COPY requirements.txt requirements.txt
COPY app.py app.py

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for Flask
EXPOSE 51234

ENV ND_PORT=51234

# Run the application
CMD ["python", "app.py"]
