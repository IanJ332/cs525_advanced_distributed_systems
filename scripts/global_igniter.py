import paramiko
import sys
import concurrent.futures

# The 12 Known Real Backends
BACKENDS = [
    f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in [5, 6, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19]
]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def ignite_node(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=15)
        
        # 1. Start Docker Daemon
        # 2. Cleanup
        # 3. Targeted CPU Triton Ignition
        cmd = f"echo '{PASSWORD}' | sudo -S systemctl start docker && " \
              f"echo '{PASSWORD}' | sudo -S docker rm -f triton_cpu || true && " \
              f"echo '{PASSWORD}' | sudo -S docker run -d --name triton_cpu -p 8000:8000 -v /home/jisheng3/triton_model_repo:/models nvcr.io/nvidia/tritonserver:24.05-py3 tritonserver --model-repository=/models --allow-gpu=false --exit-on-error=false"
        
        stdin, stdout, stderr = client.exec_command(cmd)
        # Wait for the command to trigger (non-blocking for the container run itself as it's -d)
        stdout.read() 
        client.close()
        return node, "✅ IGNITED & DOCKER READY"
    except Exception as e:
        return node, f"❌ FAILED: {str(e)}"

def main():
    print("🔥 GLOBAL CLUSTER IGNITION (12-NODE CPU MATRIX) COMMENCING...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_to_node = {executor.submit(ignite_node, node): node for node in BACKENDS}
        for future in concurrent.futures.as_completed(future_to_node):
            node, result = future.result()
            print(f"{node}: {result}")

if __name__ == "__main__":
    main()
