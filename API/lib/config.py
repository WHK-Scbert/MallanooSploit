import os

DEFAULT_IP = "127.0.0.1"
IP_FILE = "./target_ip.txt"

if not os.path.exists(IP_FILE):
    with open(IP_FILE, "w") as f:
        f.write(DEFAULT_IP)

with open(IP_FILE, "r") as f:
    ip = f.read().strip()
