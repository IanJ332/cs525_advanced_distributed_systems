import os
import sys

# Try to load configuration from config.py
try:
    if os.path.dirname(__file__) not in sys.path:
        sys.path.append(os.path.dirname(__file__))
    import config
    USER = getattr(config, 'USER', 'netid')
    BASE_URL = getattr(config, 'BASE_URL', 'sp26-cs525-06')
    DOMAIN = getattr(config, 'DOMAIN', '.cs.illinois.edu')
    SSH_KEY_PATH = getattr(config, 'SSH_KEY_PATH', None)
except ImportError:
    print("⚠️  Warning: config.py not found. Using default/placeholder values.")
    print("💡 Hint: Copy scripts/config.py.example to scripts/config.py and fill in your info.")
    USER = "netid"
    BASE_URL = "sp26-cs525-06"
    DOMAIN = ".cs.illinois.edu"
    SSH_KEY_PATH = None


def get_vm_connection():
    print("--- UIUC CS525 Cluster Connector ---")
    try:
        # Obtain the user's input
        choice = input("Which VM do you want to connect to? (1-20, or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            return

        # (e.g., 1 -> 01)
        vm_id = int(choice)
        if 1 <= vm_id <= 20:
            target = f"{USER}@{BASE_URL}{vm_id:02d}{DOMAIN}"
            print(f"🚀 Connecting to Node {vm_id:02d} ({target})...")
            
            ssh_cmd = "ssh"
            if SSH_KEY_PATH:
                ssh_cmd += f' -i "{SSH_KEY_PATH}"'
            
            os.system(f"{ssh_cmd} {target}")

        else:
            print("❌ Invalid range. Please enter a number between 1 and 20.")
            
    except ValueError:
        print("❌ Please enter a valid number.")

if __name__ == "__main__":
    get_vm_connection()