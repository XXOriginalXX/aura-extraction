#!/bin/bash
apt-get update && apt-get install -y chromium
export PATH=$PATH:/usr/bin/chromium
python3 datafetch.py
