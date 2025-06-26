FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    inkscape \
    xvfb \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean

# Set display for xvfb
ENV DISPLAY=:99

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 10000

# Run using xvfb
CMD ["xvfb-run", "python3", "app.py"]
