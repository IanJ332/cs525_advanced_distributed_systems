#!/bin/bash

# Clean up
rm -f latency_results.csv haproxy_status.csv experiment_results.tar.gz

echo "----------------------------------------"
echo "Granting socket permissions so background monitor doesn't need sudo..."
sudo chmod 777 /var/run/haproxy.sock

echo "[0s] Starting HAProxy Monitor in background..."
./haproxy_monitor.sh &
MONITOR_PID=$!

echo "[0s] Starting Traffic Logger (Baseline)..."
python3 traffic_logger.py &
LOGGER_PID=$!

echo "[0s] Waiting 15 seconds to establish baseline..."
sleep 15

echo "----------------------------------------"
echo "[15s] TRIGGERING GRAY FAILURE!"
./inject_gray_failure.sh &
INJECT_PID=$!

echo "[15s] Experiment running. Waiting 45s for 60s window to complete..."
sleep 45

echo "----------------------------------------"
echo "[60s] Experiment interval complete. Cleaning up processes..."
kill $MONITOR_PID 2>/dev/null
# Traffic logger auto-exits at 60s, but we wait just in case
wait $LOGGER_PID 2>/dev/null

echo "[60s] Packaging results..."
tar -czvf experiment_results.tar.gz latency_results.csv haproxy_status.csv

echo "========================================"
echo " Experiment Complete!"
echo " Results saved to: experiment_results.tar.gz"
echo "========================================"
