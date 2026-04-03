import paramiko
import sys

NODES = ["sp26-cs525-0601.cs.illinois.edu", "sp26-cs525-0602.cs.illinois.edu"]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def supply_node(node):
    print(f"Final Supply for {node}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=20)
        # 1. Download get-pip.py safely
        client.exec_command("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py")
        
        # 2. Install pip per-user and libraries
        cmd = f"python3 get-pip.py --user && python3 -m pip install --user aiohttp numpy psutil"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.read() # Wait for completion
        client.close()
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    for n in NODES:
        supply_node(n)
