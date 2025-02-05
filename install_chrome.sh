#!/bin/bash

# Install dependencies
apt-get update
apt-get install -y wget unzip

# Download & Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb || apt-get --fix-broken install -y
