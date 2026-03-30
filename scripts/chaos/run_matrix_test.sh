#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./run_matrix_test.sh [vm_id] [run_label]"
    echo "Example: ./run_matrix_test.sh 05 runA"
    exit 1
fi

VM_ID=$1
RUN_LABEL=$2
TOTAL_DURATION=90 # 30s baseline + 30s fault + 30s recovery

if [ "$VM_ID" == "05" ]; then
    TARGET_NODE="gpu1"
elif [ "$VM_ID" == "06" ]; then
    TARGET_NODE="gpu2"
else
    echo "Invalid VM_ID. Must be 05 or 06."
    exit 1
fi

LATENCY_CSV="latency_results_${VM_ID}_${RUN_LABEL}.csv"
STATUS_CSV="haproxy_status_${VM_ID}_${RUN_LABEL}.csv"
TAR_FILE="matrix_test_${VM_ID}_${RUN_LABEL}.tar.gz"

rm -f $LATENCY_CSV $STATUS_CSV $TAR_FILE

echo "----------------------------------------"
echo "[0s] Starting 100ms High-Precision HAProxy Monitor ($TARGET_NODE) in background..."
sudo chmod 777 /var/run/haproxy.sock
python3 high_precision_monitor.py $TOTAL_DURATION $TARGET_NODE $STATUS_CSV &
MONITOR_PID=$!

echo "[0s] Starting Traffic Logger v2 (Baseline)..."
python3 traffic_logger_v2.py $TOTAL_DURATION $LATENCY_CSV &
LOGGER_PID=$!

echo "[0s] Waiting 30 seconds to establish pure baseline..."
sleep 30

echo "----------------------------------------"
echo "[30s] TRIGGERING GRAY FAILURE ON VM $VM_ID!"
./inject_gray_failure_v2.sh $VM_ID &
INJECT_PID=$!

echo "[30s] Fault active for 30s. Waiting..."
sleep 30

echo "----------------------------------------"
echo "[60s] Fault duration ended natively. Observing 30s recovery..."
sleep 30

echo "----------------------------------------"
echo "[90s] Experiment interval complete. Synchronizing..."
wait $LOGGER_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

echo "[90s] Packaging results into ${TAR_FILE}..."
tar -czvf $TAR_FILE $LATENCY_CSV $STATUS_CSV

echo "========================================"
echo " Matrix Test [$RUN_LABEL] on VM $VM_ID Complete!"
echo " Results saved to: $TAR_FILE"
echo "========================================"
