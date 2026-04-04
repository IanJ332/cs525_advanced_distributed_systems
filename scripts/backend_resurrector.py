import paramiko
import concurrent.futures

# 12 Target Backend Nodes
BACKENDS = [
    f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in [5, 6, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19]
]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def investigate_and_resurrect(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=15)
        
        # 1. Check Death Cause (Investigation)
        _, stdout_ps, _ = client.exec_command(f"echo '{PASSWORD}' | sudo -S docker ps -a | grep triton_cpu")
        ps_out = stdout_ps.read().decode().strip()
        
        _, stdout_log, _ = client.exec_command(f"echo '{PASSWORD}' | sudo -S docker logs --tail 10 triton_cpu")
        log_out = stdout_log.read().decode().strip()
        
        status = "ALIVE" if "Up" in ps_out else "DEAD"
        if not ps_out: status = "MISSING"
        
        # 2. Resurrection (Force Restart with CPU-only flag)
        resurrect_cmd = f"echo '{PASSWORD}' | sudo -S systemctl start docker && " \
                        f"echo '{PASSWORD}' | sudo -S docker rm -f triton_cpu || true && " \
                        f"echo '{PASSWORD}' | sudo -S docker run -d -p 8000:8000 --name triton_cpu " \
                        f"-v /home/jisheng3/triton_model_repo:/models nvcr.io/nvidia/tritonserver:24.05-py3 " \
                        f"tritonserver --model-repository=/models --allow-gpu=false --exit-on-error=false"
                        
        client.exec_command(resurrect_cmd)
        
        # 3. Quick Poll (Optional here, we rely on the orchestrator later)
        client.close()
        return node, status, log_out[:100]
    except Exception as e:
        return node, "UNREACHABLE", str(e)

def main():
    print("📡 EXECUTING BACKEND RESURRECTION PROTOCOL (12 NODES)...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_to_node = {executor.submit(investigate_and_resurrect, node): node for node in BACKENDS}
        for future in concurrent.futures.as_completed(future_to_node):
            node, status, snippet = future.result()
            print(f"{node}: Status before=[{status}] | Logs=[{snippet}]")
            results.append((node, status))

    print("\n✅ Resurrection commands dispatched to all nodes. Triton is initializing...")

if __name__ == "__main__":
    main()
