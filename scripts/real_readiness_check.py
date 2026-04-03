import paramiko
import sys
import json
import time

# 12 Targets known as active
BACKENDS = [
    f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in [5, 6, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19]
]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def check_backend(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=5)
        # Check if triton is responding on 8000
        cmd = "curl -s -o /dev/null -w '%{http_code}' localhost:8000/v2/health/ready"
        stdin, stdout, stderr = client.exec_command(cmd)
        code = stdout.read().decode().strip()
        client.close()
        return code == "200"
    except:
        return False

def main():
    print("STARTING REAL-WORLD CLUSTER READINESS CHECK...")
    active_backends = []
    for node in BACKENDS:
        if check_backend(node):
            print(f"✅ {node}: TRITON READY")
            active_backends.append(node)
        else:
            print(f"❌ {node}: NOT RESPONDING")
            
    print(f"\nFinal Active Backend Count: {len(active_backends)}/12")
    
    # Save the real active backend list for the gateway
    with open('active_backends.json', 'w') as f:
        json.dump(active_backends, f, indent=4)

if __name__ == "__main__":
    main()
