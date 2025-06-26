# Base image
FROM python:3.11-slim

# Install system dependencies for Inkscape, Xvfb, OpenCV
RUN apt-get update && apt-get install -y \
    inkscape \
    xvfb \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean

# Set virtual display for Inkscape
ENV DISPLAY=:99

# Set the working directory
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (informational only)
EXPOSE 10000

# Start the Flask app using Gunicorn, binding to Render's $PORT
# Shell form ensures $PORT is expanded correctly
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1
