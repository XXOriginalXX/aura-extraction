# Start with a basic Python image
FROM python:3.9-slim

# Install necessary dependencies and Chromium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    unzip \
    libx11-dev \
    libx11-xcb1 \
    libgl1-mesa-glx \
    libxrandr2 \
    libxss1 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libasound2 \
    chromium

# Set environment variable to tell selenium where the chrome binary is
ENV CHROME_BIN=/usr/bin/chromium

# Install Python packages (from requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app's code
COPY . /app

# Set the app directory as the working directory
WORKDIR /app

# Run the app with Python
CMD ["python", "datafetch.py"]
