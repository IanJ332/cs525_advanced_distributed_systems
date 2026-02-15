import os
import subprocess

# Basic configuration
USER = ""
BASE_URL = "sp26-cs525-06"
DOMAIN = ".cs.illinois.edu"

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
            
            # 使用 os.system 或 subprocess 调起系统原生的 ssh
            # 这样所有的密码输入提示都会正常显示
            os.system(f"ssh {target}")
        else:
            print("❌ Invalid range. Please enter a number between 1 and 20.")
            
    except ValueError:
        print("❌ Please enter a valid number.")

if __name__ == "__main__":
    get_vm_connection()