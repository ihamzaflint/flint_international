#!/bin/bash

echo "=============================="
echo "Installing FortiClient (7.4)"
echo "=============================="

# 1. Add Fortinet GPG Key
echo "[1/3] Adding Fortinet GPG key..."
wget -O - https://repo.fortinet.com/repo/forticlient/7.4/ubuntu22/DEB-GPG-KEY \
  | gpg --dearmor | sudo tee /usr/share/keyrings/repo.fortinet.com.gpg > /dev/null

# 2. Add Fortinet repository
echo "[2/3] Adding Fortinet repository..."
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/repo.fortinet.com.gpg] https://repo.fortinet.com/repo/forticlient/7.4/ubuntu22/ stable non-free" \
  | sudo tee /etc/apt/sources.list.d/forticlient.list

# 3. Install FortiClient
echo "[3/3] Updating APT and installing FortiClient..."
sudo apt update
sudo apt install -y forticlient

echo "✅ FortiClient installation complete."

