import urllib.request
import ssl
import json

# --- Create SSL context that ignores self-signed certificate warnings ---
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# The IP address of the server machine
SERVER_IP = '192.168.1.112'

# --- GET Request ---
print(f"Sending secure GET request to {SERVER_IP}...")
with urllib.request.urlopen(f'https://{SERVER_IP}:1212', context=ssl_context) as response:
    print(response.read().decode())

# --- POST Request ---
print("\nSending secure POST request...")

# JSON data to send
data = {'message': 'Secure hello from another system!', 'encrypted': True}
json_data = json.dumps(data).encode('utf-8')

req = urllib.request.Request(
    url=f'https://{SERVER_IP}:1212',
    data=json_data,
    method='POST',
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req, context=ssl_context) as response:
    print(response.read().decode())