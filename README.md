# A macOS remote power menu for your Linux rig

Convenient menu utility to wake/suspend/poweroff a remote rig and seeing if it is awake from macOS

### Features

- macOS menu that:
  - Shows awake status ![rig-up.png](SwiftBar/rig-up.png) for a rig via Tailscale
  - Triggers:
    - Wake-on-LAN via a server 
    - Suspend/Poweroff via a dedicated SSH key limited to these functions 

## Prerequisites 

- Devices:
  - macOS local device 
  - Remote rig with a Wake-on-LAN capable ethernet port 
  - Server (i.e. dev board), on the same network as your remote rig, that you will leave powered on 
- Remote rig and server on the same ethernet local network
- [Tailscale](https://tailscale.com/) configured on all three devices 

## Overview

1. Set up the WoL server on a dev board (like a Raspberry Pi) or other server you leave on, on the same network as your target rig.
2. Configure your target machine for Wake-on-LAN and suspend/poweroff via a dedicated SSH key.
3. Install the SwiftBar plugin on macOS for menu bar control. 

## macOS SwiftBar Plugin

### Prerequisites

1. Install [SwiftBar](https://swiftbar.app/).
2. Install [Tailscale](https://tailscale.com/) on both macOS and your rig.
3. Ensure both devices are configured to connect to your Tailscale network. 

### Installation

1. Copy `SwiftBar/plugins/rig.10s.sh` to your SwiftBar plugins directory (i.e. `~/.swiftbar/plugins`).
2. Enable script permissions: `chmod +x rig.10s.sh`
3. Edit the script and replace `your-wol-server:8000` with your server's address. 
4. Create an SSH key for swiftbar to request suspend/poweroff:

   `ssh-keygen -f /Users/username/.swiftbar/ssh/id_swiftbar -C "swiftbar-key" -N ""`

6. Refresh SwiftBar or restart it.

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

### Wake-on-LAN Linux Configuration

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

### Remote Suspend and Poweroff Linux Configuration 

1. Enable passwordless access to suspend and poweroff:

Add lines at end of your `sudoers` file via `sudo visudo` (replace `username` with your username):

    username ALL=(ALL) NOPASSWD: /usr/bin/systemctl suspend
    username ALL=(ALL) NOPASSWD: /usr/bin/systemctl poweroff

2. Allow SSH using the swiftbar-key to perform suspend, poweroff (and nothing else). 

Add lines at the beginning of `~/.ssh/authorized_keys`

    command="/usr/bin/sudo /usr/bin/systemctl suspend",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty <content of id_swiftbar.pub>
    command="/usr/bin/sudo /usr/bin/systemctl poweroff",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty <content of id_swiftbar.pub>

Associating the key only with these entries means:
- The key can only run these commands.
- They key does not support SSH forwarding or pty allocation.

These functions should work after a reboot. 

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
