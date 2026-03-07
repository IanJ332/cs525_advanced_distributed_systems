import csv
import numpy as np

def calculate_mad(arr):
    """
    Calculate Median and Median Absolute Deviation (MAD)
    """
    if len(arr) == 0:
        return 0.0, 0.0
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    return med, mad

def backtest():
    # Backtest using real raw traces from W1 containing 1s resolution
    csv_file = "/Users/ian/Desktop/cs525_advanced_distributed_systems/archive/20260306_motivation_test/raw_requests_1s_resolution.csv"
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return

    history_l = [] # Global P99 history
    history_q = [] # Global queue depth history
    
    window_l = []  # 5-second sliding window P99
    window_q = []  # 5-second sliding window queue depth
    
    consecutive_suspicious = 0
    epsilon = 1e-4 # epsilon term to prevent division by zero
    
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
        
        # Maintain 5-second sliding window
        if len(window_l) > 5:
            window_l.pop(0)
            window_q.pop(0)
            
        # Perform per-second evaluation when sliding window is full
        if len(window_l) == 5:
            # 1. Intra-window median evaluation
            Li = np.median(window_l)
            Qi = np.median(window_q)
            
            # 2. Global median and MAD (calculated based on historical data)
            med_L, mad_L = calculate_mad(history_l)
            med_Q, mad_Q = calculate_mad(history_q)
            
            # 3. Calculate Robust Z-score with epsilon stabilization
            zL_i = (Li - med_L) / (mad_L + epsilon)
            zQ_i = (Qi - med_Q) / (mad_Q + epsilon)
            
            # 4. Trigger logic
            if zL_i >= 3 and zQ_i >= 2:
                consecutive_suspicious += 1
            else:
                # Interrupted, reset
                consecutive_suspicious = 0
                
            if consecutive_suspicious >= 3:
                print(f"[{row['timestamp']}] 🚨 SUSPICIOUS NODE DETECTED! Local T={t}s | zL: {zL_i:.2f}, zQ: {zQ_i:.2f}")
                suspicious_events += 1
                # Reset counter for subsequent triggers
                consecutive_suspicious = 0
                
    print(f"\nBacktest Completed. Total Detection Triggers: {suspicious_events}")

if __name__ == "__main__":
    backtest()
