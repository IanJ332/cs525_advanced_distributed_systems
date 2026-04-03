import paramiko
import sys
import json
import concurrent.futures

NODES = {
    "VM 01 (Gateway)": "sp26-cs525-0601.cs.illinois.edu",
    "VM 02 (Load CV)": "sp26-cs525-0602.cs.illinois.edu",
    "VM 03 (Load NLP)": "sp26-cs525-0603.cs.illinois.edu"
}

BACKENDS = [
    f"sp26-cs525-06{i:02d}.cs.illinois.edu" for i in [5, 6, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19]
]

USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def check_load_node(node_name, host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=USERNAME, password=PASSWORD, timeout=10)
        # Check files
        files_check = "ls bombard_engine.py high_precision_monitor.py"
        stdin, stdout, stderr = client.exec_command(files_check)
        files_list = stdout.read().decode().strip()
        
        # Check libraries
        stdin, stdout, stderr = client.exec_command("python3 -c 'import aiohttp; import numpy; print(\"READY\")'")
        lib_status = stdout.read().decode().strip()
        
        client.close()
        return node_name, {"files": files_list if files_list else "MISSING", "libs": lib_status}
    except Exception as e:
        return node_name, {"error": str(e)}

def check_gateway(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=USERNAME, password=PASSWORD, timeout=10)
        # Check gateway dual mode script
        stdin, stdout, stderr = client.exec_command("ls gateway_dual_mode.py")
        out = stdout.read().decode().strip()
        client.close()
        return "Gateway", {"script": out if out else "MISSING"}
    except Exception as e:
        return "Gateway", {"error": str(e)}

def check_backend_readiness(node):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node, username=USERNAME, password=PASSWORD, timeout=5)
        # 1. System Ready Check
        stdin, stdout, stderr = client.exec_command("curl -s -o /dev/null -w '%{http_code}' localhost:8000/v2/health/ready")
        sys_code = stdout.read().decode().strip()
        # 2. ResNet50 Model Ready Check
        stdin, stdout, stderr = client.exec_command("curl -s -o /dev/null -w '%{http_code}' localhost:8000/v2/models/resnet50/ready")
        model_code = stdout.read().decode().strip()
        client.close()
        return node, {"sys": sys_code, "model": model_code}
    except Exception as e:
        return node, {"error": str(e)}

def main():
    print("🚀 CONDUCTING PRE-FLIGHT SANITY CHECK...")
    
    # 1. Check Load Nodes
    load_results = {}
    for name, host in [("VM 02", NODES["VM 02 (Load CV)"]), ("VM 03", NODES["VM 03 (Load NLP)"])]:
        _, res = check_load_node(name, host)
        load_results[name] = res
        
    # 2. Check Gateway
    _, gw_res = check_gateway(NODES["VM 01 (Gateway)"])
    
    # 3. Check 12 Backends
    backend_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_to_node = {executor.submit(check_backend_readiness, node): node for node in BACKENDS}
        for future in concurrent.futures.as_completed(future_to_node):
            node, res = future.result()
            backend_results[node] = res

    report = {
        "load_nodes": load_results,
        "gateway": gw_res,
        "backends": backend_results
    }
    with open('preflight_report.json', 'w') as f:
        json.dump(report, f, indent=4)
    print("\nPre-flight check complete. Report generated.")

if __name__ == "__main__":
    main()
