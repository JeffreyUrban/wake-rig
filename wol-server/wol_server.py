from dotenv import load_dotenv
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
from urllib.parse import parse_qs, urlparse

load_dotenv('/home/wol/.env')

class WOLHandler(BaseHTTPRequestHandler):
    def load_devices(self):
        try:
            with open('devices.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"devices": {}}

    def is_valid_mac(self, mac):
        """Validate MAC address format"""
        if not mac:
            return False
        parts = mac.split(':')
        if len(parts) != 6:
            return False
        try:
            # Check each part is a valid hex number between 00 and FF
            return all(0 <= int(part, 16) <= 255 for part in parts)
        except ValueError:
            return False

    def do_GET(self):
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        if parsed_path.path == '/wake':
            # Support both device name and direct MAC
            device_name = params.get('device', [None])[0]
            mac = params.get('mac', [None])[0]

            # If device name provided, look up its MAC
            if device_name:
                devices = self.load_devices()
                device = devices.get('devices', {}).get(device_name.lower())
                if device:
                    mac = device.get('mac')

            if not mac:
                self.send_error(400, "MAC address required")
                return

            if not self.is_valid_mac(mac):
                self.send_error(400, "Invalid MAC address format")
                return

            try:
                # Send WoL packet to local network broadcast
                subprocess.run(['wakeonlan', mac], check=True)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'success',
                    'message': f'WoL packet sent to {mac}',
                    'device': device_name if device_name else 'unknown'
                }
                self.wfile.write(json.dumps(response).encode())
            except subprocess.CalledProcessError as e:
                self.send_error(500, f"Failed to send WoL packet: {str(e)}")

        elif parsed_path.path == '/devices':
            # List all known devices
            devices = self.load_devices()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(devices).encode())

        else:
            self.send_error(404, "Not Found")

    def run(server_class=HTTPServer, handler_class=WOLHandler, port=8000):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print(f'Starting WoL server on port {port}...')
        httpd.serve_forever()

if __name__ == '__main__':
    run()
