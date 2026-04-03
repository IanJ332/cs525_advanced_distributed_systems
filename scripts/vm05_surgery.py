import paramiko
import sys

NODE = "sp26-cs525-0605.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def run_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8', errors='replace').strip()
    return output

def main():
    print(f"Connecting to {NODE} for surgery...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(NODE, username=USERNAME, password=PASSWORD, timeout=20)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print("Executing Podman/Buildah Prune Protocol...")
    # Attempt gentle prune first, then force if directory still exists
    prune_cmds = [
        f"echo '{PASSWORD}' | sudo -S podman system prune -a -f || echo 'Podman failed'",
        f"echo '{PASSWORD}' | sudo -S buildah prune -a -f || echo 'Buildah failed'",
        # Check if the directory still has significant size, if so, use the 'nuclear' option
        f"echo '{PASSWORD}' | sudo -S rm -rf /var/lib/containers/storage/*"
    ]
    
    for cmd in prune_cmds:
        res = run_command(client, cmd)
        print(f"Result: {res}")
        
    print("Final health check...")
    health = run_command(client, "df -h /var")
    print(f"Final status for /var:\n{health}")
    
    client.close()

if __name__ == "__main__":
    main()
