import paramiko
import sys
import concurrent.futures

NODES = [f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in range(1, 21)]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def repair_and_ignite(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=10)
        
        # 1. Force kill existing
        client.exec_command(f"echo '{PASSWORD}' | sudo -S docker rm -f triton_cpu")
        
        # 2. Check real model path
        stdin, stdout, stderr = client.exec_command("find /home/jisheng3 -name 'config.pbtxt' | head -n 1")
        path = stdout.read().decode().strip()
        if not path:
            client.close()
            return node, "ERROR: Model Repository not found."
            
        # Get the repo root (dir above model dir)
        # e.g., /home/jisheng3/triton_model_repo/resnet/config.pbtxt -> /home/jisheng3/triton_model_repo
        repo_path = "/".join(path.split("/")[:-2])
        
        # 3. Targeted Ignition (Explicitly disabling GPUs to prevent hang)
        ignite_cmd = f"echo '{PASSWORD}' | sudo -S docker run -d --name triton_cpu -v {repo_path}:/models -p 8000:8000 nvcr.io/nvidia/tritonserver:24.05-py3 tritonserver --model-repository=/models --allow-gpu=false --exit-on-error=false"
        client.exec_command(ignite_cmd)
        
        client.close()
        return node, f"IGNITED [Path: {repo_path}]"
    except Exception as e:
        return node, f"FAILED: {str(e)}"

def main():
    print("SURGICAL CLUSTER REPAIR COMMENCING...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_node = {executor.submit(repair_and_ignite, node): node for node in NODES}
        for future in concurrent.futures.as_completed(future_to_node):
            node, result = future.result()
            print(f"{node}: {result}")

if __name__ == "__main__":
    main()
