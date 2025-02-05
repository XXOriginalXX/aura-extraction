#!/bin/bash
set -ex

# Install Chromium (lighter than Google Chrome)
apt-get update
apt-get install -y chromium

# Verify installation
chromium --version
