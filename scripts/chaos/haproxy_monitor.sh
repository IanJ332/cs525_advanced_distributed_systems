#!/bin/bash
echo "Timestamp_s,HAProxy_Status" > haproxy_status.csv
START_TIME=$(date +%s)
while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    # Removed 'sudo' so it stops prompting for passwords in the background loop!
    STATUS=$(echo "show stat" | socat stdio /var/run/haproxy.sock | grep triton_backend | grep gpu1 | cut -d',' -f18)
    if [ -z "$STATUS" ]; then
        STATUS="UNKNOWN"
    fi
    echo "$ELAPSED,$STATUS" >> haproxy_status.csv
    sleep 1
done
