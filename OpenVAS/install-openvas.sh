#!/bin/bash

# OpenVAS/GVM Automated Installer for Ubuntu 22.04+
# Run with: sudo bash install-openvas.sh

echo "[+] Updating system packages..."
apt update && apt upgrade -y

echo "[+] Installing software-properties-common..."
apt install -y software-properties-common

echo "[+] Adding OpenVAS/GVM PPA repository..."
add-apt-repository -y ppa:mrazavi/gvm
apt update

echo "[+] Installing GVM and OpenVAS components..."
apt install -y gvm

echo "[+] Running GVM setup..."
gvm-setup

echo "[+] Starting GVM services..."
gvm-start

echo "[+] Checking GVM status..."
gvm-status

echo ""
echo "[✔] Installation Complete!"
echo "Open your browser and navigate to: https://localhost:9392"
echo "Or use your server IP: https://<your-server-ip>:9392"
echo "Use the credentials provided at the end of gvm-setup."