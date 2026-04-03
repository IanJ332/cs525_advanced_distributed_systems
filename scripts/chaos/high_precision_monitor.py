import socket
import time
import csv
import sys
from datetime import datetime, timezone

def fetch_haproxy_stat(target_node):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect("/var/run/haproxy.sock")
        sock.sendall(b"show stat\n")
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except Exception:
        return "ERROR", "0"
    finally:
        sock.close()
        
    lines = data.decode('utf-8').split('\n')
    for line in lines:
        if "triton_backend" in line and target_node in line:
            parts = line.split(',')
            if len(parts) > 18:
                # parts[2] = qcur (current queue), parts[17] = status
                qcur = parts[2]
                status = parts[17]
                return status, qcur
    return "UNKNOWN", "0"

def main():
    if len(sys.argv) < 4:
        print("Usage: python high_precision_monitor.py [duration] [target_node_name] [output_file.csv]")
        sys.exit(1)
        
    duration = int(sys.argv[1])
    target_node = sys.argv[2] # e.g. 'gpu1' or 'gpu2'
    output_file = sys.argv[3]
    
    start_time = time.time()
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp_ISO', 'Node', 'Status', 'Queue_Depth'])
        
        while time.time() - start_time < duration:
            # 100ms precision loop
            loop_start = time.time()
            iso_time = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
            status, qcur = fetch_haproxy_stat(target_node)
            
            writer.writerow([iso_time, target_node, status, qcur])
            f.flush()
            
            # sleep to maintain 100ms interval (0.1s)
            elapsed = time.time() - loop_start
            if elapsed < 0.1:
                time.sleep(0.1 - elapsed)

if __name__ == "__main__":
    main()