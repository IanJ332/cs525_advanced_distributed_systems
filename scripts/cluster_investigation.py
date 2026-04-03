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

def run_investigation(node):
    print(f"Investigating {node}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=20)
    except Exception as e:
        return {"error": str(e)}

    results = {}
    
    # 1. Profiling VM 05 (only if it's VM 05)
    if "0605" in node:
        profiling_cmd = f"echo '{PASSWORD}' | sudo -S du -xh --max-depth=3 /var 2>/dev/null | sort -hr | head -n 15"
        results['var_profile'] = run_command(client, profiling_cmd)
    
    # 2. Global Model Hunt (on both)
    hunt_cmd = f"echo '{PASSWORD}' | sudo -S find / -type f \( -name 'config.pbtxt' -o -name '*.onnx' \) 2>/dev/null | grep -v '/proc' | grep -v '/sys' | head -n 20"
    results['model_hunt'] = run_command(client, hunt_cmd)
    
    client.close()
    return results

def main():
    final_output = {}
    for n in NODES:
        final_output[n] = run_investigation(n)
        
    with open('investigation_results.json', 'w') as f:
        json.dump(final_output, f, indent=4)
    print("Investigation complete. Results saved to investigation_results.json")

if __name__ == "__main__":
    main()
