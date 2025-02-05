#!/bin/bash
set -ex

# Install Chromium (lighter than Google Chrome)
apt-get update
apt-get install -y chromium-browser

# Verify installation
chromium-browser --version
