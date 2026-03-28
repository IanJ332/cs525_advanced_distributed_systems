import socket
import time
import csv
import io
import subprocess
import numpy as np
from collections import deque, defaultdict

# --- 配置参数 ---
HAPROXY_SOCK = "/var/run/haproxy.sock"
BACKEND_NAME = "triton_backend"        # <-- 确保与 haproxy.cfg 一致
WINDOW_SIZE = 5                        
THRESHOLD_ZL = 3.0                     
THRESHOLD_ZQ = 2.0                     
CONSECUTIVE_TICKS = 3                  
EPSILON = 1e-5                         

# 状态存储
history_L = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))
history_Q = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))
alert_counters = defaultdict(int)

def fetch_haproxy_stats():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(HAPROXY_SOCK)
        client.sendall(b"show stat\n")
        response = b""
        while True:
            data = client.recv(4096)
            if not data: break
            response += data
            
        decoded_response = response.decode('utf-8').lstrip('# ')
        reader = csv.DictReader(io.StringIO(decoded_response))
        stats = {}
        found_px = set()
        for row in reader:
            found_px.add(row['pxname'])
            # 调试：打印看到的每一行，看看名字到底是什么
            if row['pxname'] == BACKEND_NAME and row['svname'] in ['gpu1', 'gpu2'] and row['status'] == 'UP':
                rtime = float(row['rtime']) if row['rtime'] else 0.0
                qcur = float(row['qcur']) if row['qcur'] else 0.0
                stats[row['svname']] = {'L': rtime, 'Q': qcur}
                
        if not stats:
            print(f"[DEBUG] 未发现可用节点。Backend '{BACKEND_NAME}' 是否正确? 当前看到的 Backend 列表: {list(found_px)}")
        return stats
    except Exception as e:
        print(f"[ERROR] 无法连接到 Socket: {e}")
        return {}
    finally:
        client.close()

def isolate_node(node_name):
    """使用 socat 向 HAProxy 下发隔离(摘流)命令"""
    print(f"[ALERT] 触发隔离规则！正在将节点 {node_name} 设为 DRAIN 状态...")
    cmd = f'echo "set server {BACKEND_NAME}/{node_name} state drain" | socat stdio {HAPROXY_SOCK}'
    subprocess.run(cmd, shell=True)

def run_daemon():
    print(f"GrayPulse Daemon 启动 (监控后端: {BACKEND_NAME})...")
    while True:
        stats = fetch_haproxy_stats()
        if not stats:
            time.sleep(1)
            continue
            
        print(f"[INFO] 当前在线节点: {list(stats.keys())}")
        current_L_medians = {}
        current_Q_medians = {}
        
        # 1. 更新滑动窗口 & 计算局部中位数 (L_i, Q_i)
        for node, data in stats.items():
            history_L[node].append(data['L'])
            history_Q[node].append(data['Q'])
            
            if len(history_L[node]) == WINDOW_SIZE:
                current_L_medians[node] = np.median(history_L[node])
                current_Q_medians[node] = np.median(history_Q[node])

        # 如果数据还没填满 5 秒，跳过本次判定
        if len(current_L_medians) < 2:
            time.sleep(1)
            continue

        # 2. 计算全局中位数 (M_L, M_Q) 和 MAD
        L_values = list(current_L_medians.values())
        Q_values = list(current_Q_medians.values())
        
        M_L = np.median(L_values)
        M_Q = np.median(Q_values)
        
        MAD_L = np.median(np.abs(L_values - M_L))
        MAD_Q = np.median(np.abs(Q_values - M_Q))
        
        # 3. 计算 Z-score 并判定
        for node in current_L_medians.keys():
            zL = (current_L_medians[node] - M_L) / (1.4826 * MAD_L + EPSILON)
            zQ = (current_Q_medians[node] - M_Q) / (1.4826 * MAD_Q + EPSILON)
            
            if zL >= THRESHOLD_ZL and zQ >= THRESHOLD_ZQ:
                alert_counters[node] += 1
                print(f"[WARN] {node} 出现异常 (Tick {alert_counters[node]}/{CONSECUTIVE_TICKS}): zL={zL:.2f}, zQ={zQ:.2f}")
                
                if alert_counters[node] >= CONSECUTIVE_TICKS:
                    isolate_node(node)
                    # 隔离后清零计数器，防止重复触发
                    alert_counters[node] = -999 
            else:
                alert_counters[node] = 0 # 恢复正常则清零计数

        time.sleep(1) # 严格按照 1 秒间隔拉取

if __name__ == "__main__":
    run_daemon()
