import paramiko
import concurrent.futures

# Target all 20 nodes for absolute cleanup
NODES = [f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in range(1, 21)]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def deep_clean_node(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=10)
        
        # 1. Kill all running Python/Gateway/Bombard processes
        # 2. Stop and Remove all Triton/Triton-like Docker containers
        # 3. Purge temp CSV logs and old experimental scripts
        # 4. Stop Docker (Optional but safer for resource saving)
        clean_cmd = f"pkill -9 -f python3; " \
                    f"echo '{PASSWORD}' | sudo -S docker rm -f triton_cpu || true; " \
                    f"rm -f ~/campaign_a_cv_c*.csv ~/summary_results.csv ~/payload_vry_results.csv ~/smart.log ~/strawman.log ~/gateway_sentinel.py ~/campaign_a_engine.py ~/bombard_engine.py; " \
                    f"rm -rf ~/data/results/*; " \
                    f"echo '{PASSWORD}' | sudo -S systemctl stop docker || true"
        
        stdin, stdout, stderr = client.exec_command(clean_cmd)
        stdout.read() # Wait for completion
        client.close()
        return node, "🧹 DEEP CLEANED (Processes/Containers/Logs Refunged)"
    except Exception as e:
        return node, f"⚠️ SKIP/FAILED: {str(e)}"

def main():
    print("🧹 GLOBAL NODE SANITIZATION (20-NODE ARSENAL CLEANUP) COMMENCING...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_node = {executor.submit(deep_clean_node, node): node for node in NODES}
        for future in concurrent.futures.as_completed(future_to_node):
            node, result = future.result()
            print(f"{node}: {result}")
    print("\n[COMPLETE] All cluster nodes are now in a clean, dormant state.")

if __name__ == "__main__":
    main()
