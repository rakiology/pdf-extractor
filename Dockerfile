# 1. Start from a Python slim image
FROM python:3.11-slim

# 2. Install Inkscape (and its X virtual framebuffer), plus libs OpenCV needs
RUN apt-get update && apt-get install -y \
    inkscape \
    xvfb \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
  && apt-get clean

# 3. Tell xvfb where to point
ENV DISPLAY=:99

# 4. Copy your code into the container
WORKDIR /app
COPY . /app

# 5. Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# 6. Expose a port (this is just documentation—Render still injects $PORT)
EXPOSE 10000

# 7. Launch the app under Gunicorn, binding to Render’s $PORT
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "1"]
