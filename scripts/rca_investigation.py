import paramiko
import sys

GW_NODE = "sp26-cs525-0601.cs.illinois.edu"
WORKER_NODE = "sp26-cs525-0605.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def fetch_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 1. Check Gateway Logs (VM 01)
    try:
        print("🔍 FETCHING GATEWAY ERROR LOGS (VM 01)...")
        client.connect(GW_NODE, username=USERNAME, password=PASSWORD, timeout=10)
        stdin, stdout, stderr = client.exec_command("tail -n 20 smart.log")
        print(f"--- smart.log (Last 20 Bytes) ---\n{stdout.read().decode()}")
        print(f"--- stderr ---\n{stderr.read().decode()}")
        client.close()
    except Exception as e:
        print(f"Failed to fetch GW logs: {e}")

    # 2. Check Backend Logs (VM 05)
    try:
        print("\n🔍 FETCHING TRITON BACKEND LOGS (VM 05)...")
        client.connect(WORKER_NODE, username=USERNAME, password=PASSWORD, timeout=10)
        # Check if container is even alive
        client.exec_command(f"echo '{PASSWORD}' | sudo -S docker ps --filter name=triton_cpu")
        stdin, stdout, stderr = client.exec_command(f"echo '{PASSWORD}' | sudo -S docker logs --tail 30 triton_cpu")
        print(f"--- Triton Logs ---\n{stdout.read().decode()}")
        client.close()
    except Exception as e:
        print(f"Failed to fetch Triton logs: {e}")

if __name__ == "__main__":
    fetch_logs()
