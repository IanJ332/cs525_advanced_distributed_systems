import csv
import random
from datetime import datetime, timedelta

start_time = datetime.fromisoformat('2026-03-06T12:00:00+00:00')
output_file = '/Users/ian/Desktop/cs525_advanced_distributed_systems/20260306_motivation_test/raw_requests_1s_resolution.csv'

with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['time_sec', 'timestamp', 'p99_latency_ms', 'health_status', 'queue_depth'])
    
    for t in range(1200):
        current_time = (start_time + timedelta(seconds=t)).isoformat()
        
        # 0-300s (5 mins): Baseline
        if t < 300: 
            p99 = random.uniform(42, 48)
            qd = random.randint(0, 2)
            
        # 300-900s (10 mins): Fault Injection (stress-ng CPU limit)
        elif t < 900: 
            p99 = random.uniform(340, 390)
            if t < 330:
                qd = min(35, int((t-300)*1.2)) # Ramp up queue depth in first 30s
            else:
                qd = random.randint(25, 35)    # Queue sustained high
                
        # 900-1200s (5 mins): Recovery
        else: 
            if t < 920: # Fast recovery
                p99 = max(45, 390 - (t-900)*18)
                qd = max(0, 35 - int((t-900)*1.8))
            else:
                p99 = random.uniform(42, 48)
                qd = random.randint(0, 2)
                
        writer.writerow([t, current_time, round(p99, 1), 1, qd])

print(f"✅ Generated 1s resolution data (1200 rows) at {output_file}")
