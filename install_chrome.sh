#!/bin/bash
set -ex

# Install dependencies
apt-get update
apt-get install -y wget unzip

# Download and install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Verify installation
google-chrome --version
