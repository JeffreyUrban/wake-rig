# wake-rig

Convenient menu utility for waking a remote rig and seeing if it is awake from macOS consisting of:
- Wake-on-LAN server: HTTP server for sending WoL packets to target devices 
- macOS SwiftBar plugin: Menu that shows awake status for a rig via Tailscale and triggers wake 

## Prerequisites 

- Devices:
  - macOS local device 
  - Remote rig with a Wake-on-LAN capable ethernet port 
  - Server (i.e. dev board), on the same network as your remote rig, that you will leave powered on 
- Remote rig and server on the same ethernet local network
- [Tailscale](https://tailscale.com/) configured on all three devices 

## Overview

1. Set up the WoL server on a dev board (like a Raspberry Pi) or other server you leave on, on the same network as your target rig.
2. Configure your target machine for Wake-on-LAN.
3. Install the SwiftBar plugin on macOS for menu bar control. 

## Wake-on-LAN Server Setup

### Requirements

Choose a device with ethernet connectivity that stays powered on (e.g., dev board like a Raspberry Pi, or existing server) on the same local network as your target rig. I'm running Ubuntu; adjust as necessary for other operating systems.

### Installation

```bash
# Install system packages
sudo apt update
sudo apt install -y wakeonlan python3 python3-pip

# Install Python dependencies
pip3 install python-dotenv

# Create dedicated wol user for the service
sudo useradd -r -m -s /bin/bash wol

# Copy server files to the wol user's home directory
sudo cp -r wol-server/* /home/wol/
sudo chown -R wol:wol /home/wol/
```

### Configuration

1. **Configure devices** - Edit `/home/wol/devices.json`:
   ```json
   {
       "devices": {
           "rig": {
               "name": "rig",
               "mac": "aa:bb:cc:dd:ee:ff",
               "description": "Deep learning rig"
           }
       }
   }
   ```
   Replace 'rig' with the name of your rig, and the MAC address with your rig's ethernet interface MAC.

   ```bash
   # Edit the configuration file as root or wol user
   sudo nano /home/wol/devices.json
   # or
   sudo -u wol nano /home/wol/devices.json
   ```

### Running the Wake-on-LAN Server

```bash
# Manual start (for testing)
cd /home/wol
python3 wol_server.py

# Set up as systemd service (recommended)
sudo cp /home/wol/wol-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wol-server
sudo systemctl start wol-server

# Check service status
sudo systemctl status wol-server
```

### API Endpoints

- `GET /wake?device=rig` - Wake device by name
- `GET /wake?mac=aa:bb:cc:dd:ee:ff` - Wake device by MAC address
- `GET /devices` - List all configured devices

## Rig Setup

### Hardware Requirements

- Ensure the ethernet interface supports Wake-on-LAN when powered off
  - Some machines have multiple ethernet ports - typically only one supports WoL

### BIOS Configuration

1. Enable "Wake on LAN" or "Power On by PCI-E" in BIOS/UEFI
2. Ensure "ErP Ready" is disabled (if present)

### Linux Configuration

Here, running Ubuntu. Adjust as necessary for other operating systems. 

```bash
# Enable Wake-on-LAN for ethernet interface
sudo ethtool -s eth0 wol g

# Check current status
ethtool eth0 | grep Wake

# Make persistent across reboots
echo 'ethtool -s eth0 wol g' | sudo tee -a /etc/rc.local
```

For more detailed Linux setup, see: https://www.cyberciti.biz/tips/linux-send-wake-on-lan-wol-magic-packets.html

### Optional: Hibernate Setup

```bash
# Install power management tools
sudo apt install powermanagement-interface

# Hibernate remotely via SSH
sudo pmi action hibernate
```

## macOS SwiftBar Plugin

### Prerequisites

1. Install [SwiftBar](https://swiftbar.app/).
2. Install [Tailscale](https://tailscale.com/) on both macOS and your rig.
3. Ensure both devices are configured to connect to your Tailscale network. 

### Installation

1. Copy `SwiftBar/plugins/rig.10s.sh` to your SwiftBar plugins directory (i.e. `~/.swiftbar/plugins`).
2. Enable script permissions: `chmod +x rig.10s.sh`
3. Edit the script and replace `your-wol-server:8000` with your server's address. 
5. Refresh SwiftBar or restart it.

### Features

- **Rig Awake Status**: Shows green/gray icon based on Tailscale connectivity
- **Wake Rig**: Click menu item to send wake command to your WoL server

## Troubleshooting

### WoL Server Issues

Troubleshooting locally on the WOL server:
- Check if `wakeonlan` command works: `wakeonlan aa:bb:cc:dd:ee:ff`
- Verify the WOL server is listening: `netstat -ln | grep 8000`
- Check logs: `journalctl -u wol-server -f`

### Target Machine Issues

- Verify WoL is enabled: `ethtool eth0 | grep Wake`
- Test from another machine: `wakeonlan aa:bb:cc:dd:ee:ff`
- Check BIOS/UEFI settings

### SwiftBar Plugin Issues

- Verify Tailscale status: `/Applications/Tailscale.app/Contents/MacOS/Tailscale status`
- Test wake command manually: `curl http://your-server:8000/wake?device=rig`
