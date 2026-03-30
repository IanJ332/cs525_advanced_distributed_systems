#!/bin/bash

# $1 = Target VM (e.g., 05 or 06)
TARGET_VM=$1
DURATION=30

echo "=> [Fault Injector] Wiping clean any previous stress-ng/bash loops on VM $TARGET_VM..."
ssh -o StrictHostKeyChecking=no jisheng3@sp26-cs525-06${TARGET_VM}.cs.illinois.edu "pkill -f 'while : ; do : ; done' ; killall bash 2>/dev/null"

echo "=> [Fault Injector] Injecting Gray Failure on VM ${TARGET_VM} for $DURATION seconds..."
# Spawn infinite bash loops to lock up CPU cores 100%
ssh -o StrictHostKeyChecking=no jisheng3@sp26-cs525-06${TARGET_VM}.cs.illinois.edu "for i in {1..4}; do while : ; do : ; done & done; sleep $DURATION; kill \$(jobs -p) 2>/dev/null"
echo "=> [Fault Injector] Gray Failure Injection complete on VM ${TARGET_VM}."
