Configuration
-------------
Model: ResNet-50
Framework: round_robin
Dataset: CIFAR-10 resized to 224x224
Runtime: Triton CPU-only distributed serving
Cluster: 20 VMs total, 12 active backends
Active backends: sp26-cs525-0605, sp26-cs525-0606, sp26-cs525-0607, sp26-cs525-0608, sp26-cs525-0609, sp26-cs525-0612, sp26-cs525-0613, sp26-cs525-0614, sp26-cs525-0615, sp26-cs525-0617, sp26-cs525-0618, sp26-cs525-0619

Serving assumptions
-------------------
input tensor name: data
precision: FP32
shape: [1, 3, 224, 224]
batch size: 1
dynamic batching: disabled

Campaign
--------
Concurrency levels: 16, 24, 32, 48, 64
Duration: 240 seconds
Phases:
- 0-90 steady
- 90-180 fault
- 180-240 recovery

Fault model
-----------
Round robin distributes requests nearly uniformly and does not adapt away from the
degraded backend sp26-cs525-0605 during the fault window, so the impact is stronger
than an adaptive policy would show.
