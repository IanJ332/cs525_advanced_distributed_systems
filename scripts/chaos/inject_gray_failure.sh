#!/bin/bash
echo "=> Injecting Gray Failure on VM 05 (gpu1) for 30 seconds..."
# Spawn 4 infinite bash loops to lock up 4 CPU cores 100%. No stress-ng installation needed!
ssh -o StrictHostKeyChecking=no jisheng3@sp26-cs525-0605.cs.illinois.edu "for i in {1..4}; do while : ; do : ; done & done; sleep 30; kill \$(jobs -p) 2>/dev/null"
echo "=> Gray Failure Injection complete. Recovery started."
