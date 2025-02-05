#!/bin/bash
echo "Installing Chrome..."
wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > google-chrome.deb
sudo apt install -y ./google-chrome.deb
rm google-chrome.deb
echo "Chrome Installed!"
