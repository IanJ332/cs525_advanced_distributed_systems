import paramiko
import sys

NODE = "sp26-cs525-0601.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def check_triton():
    print(f"Connecting to {NODE} to check Triton status...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(NODE, username=USERNAME, password=PASSWORD, timeout=20)
        
        # 1. Check for running container
        stdin, stdout, stderr = client.exec_command("docker ps --filter name=triton_cpu")
        out = stdout.read().decode().strip()
        print(f"Docker ps result:\n{out}")
        
        # 2. Check logs if container exists
        if "triton_cpu" in out:
            print("Fetching container logs...")
            stdin, stdout, stderr = client.exec_command("docker logs --tail 20 triton_cpu")
            print(f"Logs:\n{stdout.read().decode()}")
            
        # 3. Direct port check
        stdin, stdout, stderr = client.exec_command("curl -v localhost:8000/v2/health/ready")
        print(f"Curl result:\n{stderr.read().decode()}{stdout.read().decode()}")
        
        client.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    check_triton()
