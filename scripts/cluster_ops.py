import paramiko
import sys
import json

NODES = ["sp26-cs525-0605.cs.illinois.edu", "sp26-cs525-0606.cs.illinois.edu"]
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def run_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8', errors='replace').strip()
    return output

def run_ops_on_node(node):
    print(f"Connecting to {node}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=20)
    except Exception as e:
        return {"error": str(e)}

    results = {}
    
    # 1. Before df
    results['df_before'] = run_command(client, "df -h /var")
    
    # 2. Clean commands
    # We use a single shell string to ensure sequential execution and proper environment
    clean_script = f"""
    apptainer cache clean --all --force || singularity cache clean -a -f
    echo '{PASSWORD}' | sudo -S find /var/tmp -type f -mtime +0 -delete
    echo '{PASSWORD}' | sudo -S apt-get clean || echo '{PASSWORD}' | sudo -S dnf clean all
    """
    run_command(client, f"bash -c \"{clean_script}\"")
        
    # 3. After df
    results['df_after'] = run_command(client, "df -h /var")
    
    # 4. Recon
    recon_cmd = f"echo '{PASSWORD}' | sudo -S find /srv -name 'config.pbtxt' -o -name 'cs525*' -o -name 'resnet*' 2>/dev/null | head -n 10"
    results['recon'] = run_command(client, recon_cmd)
    
    client.close()
    return results

def main():
    final_output = {}
    for n in NODES:
        final_output[n] = run_ops_on_node(n)
        
    with open('cluster_results.json', 'w') as f:
        json.dump(final_output, f, indent=4)
    print("Execution complete. Results saved to cluster_results.json")

if __name__ == "__main__":
    main()
