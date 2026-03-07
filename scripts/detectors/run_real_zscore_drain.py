import subprocess
import time
import os
import signal
import sys
import threading

def run_traffic():
    # We use our hedging bench single mode simply to put load on HAProxy
    print("[Traffic Gen] 🚀 Starting Background Load (Queue Depth filler)...")
    try:
        subprocess.run(["/Users/ian/Desktop/cs525_advanced_distributed_systems/.venv/bin/python3", "scripts/detectors/hedging_bench.py"], stdout=subprocess.DEVNULL)
    except:
        pass

def trigger_fault():
    print(f"\n[{time.strftime('%X')}] 💉 [FAULT INJECTION] Executing Python CPU Hog on 0605 (Simulating Heavy ResNet50 Contention)...")
    py_hog = "import multiprocessing; [multiprocessing.Process(target=lambda: sum(range(1000000)) while True).start() for _ in range(32)]"
    # Using python3 -c with timeout 30
    cmd = f'ssh -i /Users/ian/.ssh/id_ed25519 -o StrictHostKeyChecking=no jisheng3@sp26-cs525-0605.cs.illinois.edu "timeout 30 python3 -c \\"import multiprocessing; f=lambda: sum(1 for _ in iter(int, 1)); [multiprocessing.Process(target=f).start() for _ in range(32)]\\""'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[{time.strftime('%X')}] 🛑 [FAULT OVER] CPU Hog finished")

def main():
    print("======================================================================")
    print(" GrayPulse W2 Real-Time Integration & Drain Validation ")
    print("======================================================================")
    
    # 1. Start Z-Score detector trace
    print("[1] Launching Z-score Detector Fast-Path...")
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    detector_proc = subprocess.Popen(["/Users/ian/Desktop/cs525_advanced_distributed_systems/.venv/bin/python3", "scripts/detectors/graypulse_zscore_detector.py"], env=env)
    
    # Wait for Detector to establish baseline
    time.sleep(3)
    
    # 2. Start Traffic generator to build concurrent HTTP queue map
    print("\n[2] Warming up baseline traffic...")
    t_traffic = threading.Thread(target=run_traffic)
    t_traffic.daemon = True
    t_traffic.start()
    
    # Let baseline settle for 5 seconds
    time.sleep(5)
    
    # 3. Inject Fault (Gray Failure)
    print("\n[3] Injecting Gray Failure...")
    fault_start = time.time()
    t_fault = threading.Thread(target=trigger_fault)
    t_fault.daemon = True
    t_fault.start()
    
    try:
        # We let the detector do its thing and wait for it to print the Drain execution
        print("\n⏳ Waiting for GrayPulse to detect and mitigate...")
        time.sleep(20) # 20s is plenty since detector sliding window is 5s
        
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🧹 Shutting down experiment...")
        detector_proc.terminate()
        detector_proc.wait()
        
if __name__ == "__main__":
    main()
