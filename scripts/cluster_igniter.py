import paramiko
import sys
import json
import concurrent.futures

NODES = [f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in range(4, 21)]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def deploy_node(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=10)
        
        # 1. Clean up existing containers
        client.exec_command(f"echo '{PASSWORD}' | sudo -S docker rm -f triton_cpu")
        
        # 2. Start CPU-based Triton
        deploy_cmd = f"echo '{PASSWORD}' | sudo -S docker run -d -p 8000:8000 --name triton_cpu -v /home/jisheng3/triton_model_repo:/models nvcr.io/nvidia/tritonserver:24.05-py3 tritonserver --model-repository=/models --allow-gpu=false"
        client.exec_command(deploy_cmd)
        
        # 3. Quick Health Check (Wait 5s then check)
        import time
        time.sleep(5)
        stdin, stdout, stderr = client.exec_command("curl -s -o /dev/null -w '%{http_code}' localhost:8000/v2/health/ready")
        status_code = stdout.read().decode().strip()
        client.close()
        return node, status_code
    except Exception as e:
        return node, f"Error: {str(e)}"

def main():
    print(f"Starting Campaign Cluster Deployment (VM 04-20)...")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=17) as executor:
        future_to_node = {executor.submit(deploy_node, node): node for node in NODES}
        for future in concurrent.futures.as_completed(future_to_node):
            node, status = future.result()
            results[node] = status
            print(f"{node}: {status}")

    with open('deploy_status.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
