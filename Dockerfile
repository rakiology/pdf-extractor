FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    inkscape \
    xvfb \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean

# Set display for Inkscape
ENV DISPLAY=:99

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Render will scan
EXPOSE 10000

# Run Flask with xvfb
CMD ["xvfb-run", "python", "app.py"]
