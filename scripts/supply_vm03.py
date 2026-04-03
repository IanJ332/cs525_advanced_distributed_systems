import paramiko
import sys

LOAD_CV = "sp26-cs525-0602.cs.illinois.edu"
LOAD_NLP = "sp26-cs525-0603.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def supply_nlp():
    # Use the local copies instead of cross-node to be safer
    client_nlp = paramiko.SSHClient()
    client_nlp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Upload to VM 03
        client_nlp.connect(LOAD_NLP, username=USERNAME, password=PASSWORD, timeout=10)
        sftp_nlp = client_nlp.open_sftp()
        # Use our local copies in scripts/
        sftp_nlp.put('scripts/bombard_engine.py', 'bombard_engine.py')
        sftp_nlp.put('scripts/gateway_dual_mode.py', 'gateway_dual_mode.py')
        
        # Install dependencies on VM 03
        stdin, stdout, stderr = client_nlp.exec_command("python3 -m pip install --user aiohttp numpy")
        stdout.read() # Wait for completion
        
        client_nlp.close()
        return True
    except Exception as e:
        print(f"Supply VM 03 Failed: {e}")
        return False

if __name__ == "__main__":
    supply_nlp()
