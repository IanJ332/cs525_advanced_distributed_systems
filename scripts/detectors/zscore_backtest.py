import csv
import numpy as np

def calculate_mad(arr):
    """
    计算中位数及其绝对中位差 (Median Absolute Deviation)
    """
    if len(arr) == 0:
        return 0.0, 0.0
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    return med, mad

def backtest():
    # 使用 W1 中采集的已包含 1s 解析度的真实原始迹线进行回测
    csv_file = "/Users/ian/Desktop/cs525_advanced_distributed_systems/archive/20260306_motivation_test/raw_requests_1s_resolution.csv"
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return

    history_l = [] # 全局 P99 历史
    history_q = [] # 全局队列深度历史
    
    window_l = []  # 5秒滑动窗口 P99
    window_q = []  # 5秒滑动窗口 队列深度
    
    consecutive_suspicious = 0
    epsilon = 1e-4 # epsilon 项防止分母为零
    
    print(f"Loaded {len(data)} records. Starting Robust Z-score backtest...")
    
    suspicious_events = 0

    for row in data:
        t = int(row['time_sec'])
        p99 = float(row['p99_latency_ms'])
        qd = float(row['queue_depth'])
        
        history_l.append(p99)
        history_q.append(qd)
        
        window_l.append(p99)
        window_q.append(qd)
        
        # 维持 5 秒滑动窗口
        if len(window_l) > 5:
            window_l.pop(0)
            window_q.pop(0)
            
        # 当滑动窗口填满 5 秒时进行按秒评估
        if len(window_l) == 5:
            # 1. 窗口内中位数评估
            Li = np.median(window_l)
            Qi = np.median(window_q)
            
            # 2. 全局中位数与绝对中位差 MAD (基于历史累积数据计算)
            med_L, mad_L = calculate_mad(history_l)
            med_Q, mad_Q = calculate_mad(history_q)
            
            # 3. 计算含 epsilon 平滑项的 Robust Z-score 分数
            zL_i = (Li - med_L) / (mad_L + epsilon)
            zQ_i = (Qi - med_Q) / (mad_Q + epsilon)
            
            # 4. 触发判定判定逻辑 [Trigger Logic]
            if zL_i >= 3 and zQ_i >= 2:
                consecutive_suspicious += 1
            else:
                # 打断重置
                consecutive_suspicious = 0
                
            if consecutive_suspicious >= 3:
                print(f"[{row['timestamp']}] 🚨 SUSPICIOUS NODE DETECTED! Local T={t}s | zL: {zL_i:.2f}, zQ: {zQ_i:.2f}")
                suspicious_events += 1
                # 重置计数器以便后续观察是否持续触发
                consecutive_suspicious = 0
                
    print(f"\nBacktest Completed. Total Detection Triggers: {suspicious_events}")

if __name__ == "__main__":
    backtest()
