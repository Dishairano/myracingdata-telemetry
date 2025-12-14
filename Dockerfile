# Dockerfile for building Windows .exe on Linux
# Uses Wine + Python + PyInstaller

FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Wine and dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
    wine \
    wine64 \
    wine32 \
    wget \
    unzip \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set Wine prefix
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win64

# Initialize Wine
RUN wine wineboot --init && sleep 10

# Download and install Python 3.11 in Wine
WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe && \
    wine python-3.11.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 && \
    sleep 20

# Install PyInstaller and dependencies
RUN wine python -m pip install --upgrade pip && \
    wine python -m pip install pyinstaller

# Set working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
RUN wine python -m pip install -r requirements.txt

COPY . .

# Build command
CMD ["wine", "pyinstaller", "myracingdata.spec", "--clean"]
