# cs525_advanced_distributed_systems

# 🚀 CS525 Distributed Systems Cluster Configuration Guide

This document is intended to help team members quickly configure the experimental environment, achieving rapid access and automated management of the 20 VM nodes.

---

## 🛠️ What have I finished? (Infrastructure Status)

*   **Environment Initialization**: Confirmed and tested hardware specifications for all 20 machines in the cluster (Intel Xeon Silver 4216, 8GB RAM, 32GB Disk).
*   **Establish Trust Root**: I have distributed my local public key to **VM 01**, enabling a password-less secure connection between local and that node.
*   **Internal Network Connectivity**:
    *   **VM 01** acts as a "bastion host," possessing internal network access permissions to connect to **VM 02-20**.
    *   Through batch testing scripts, it has been confirmed that the SSH services for all 20 nodes in the cluster are in a responsive state.
*   **Development Toolchain**: Developed and tested the following Python automation tools:
    *   `connect.py`: Used for one-click interactive connection to specified VM nodes from local terminal, supporting one-click jump to Campus Cluster GPU nodes.
    *   `hardware_monitor.py`: Deep detection of hardware information across the cluster (CPU/Cache/RAM/GPU/Storage).
    *   `live_monitor.py`: Real-time resource monitoring dashboard for the entire cluster (real-time refresh of CPU usage, RAM progress bars, online status).

---

## 📂 Experiment Documentation

- **W2 Network Fault Injection (GrayPulse Evaluation)**: [W2 Network Test Protocol](archive/W2_network_test/README.md)

---

## 👥 What do teammates need to do? (Action Items)

To achieve "instant connection" to 20 machines like me, please follow these three steps:

### 1. Basic Environment Preparation

*   **VPN Connection**: Ensure **Cisco AnyConnect** is always in **"2 Tunnel All"** mode; otherwise, UIUC internal private IP ranges cannot be reached.
*   **Pull Repository**: Pull the latest `scripts/` folder from our GitHub repository.

### 2. Establish Password-less Login from Local to VM 01

This is the most critical step, required only once, to eliminate the requirement of entering passwords every time:

1.  **Generate Local Keys** (skip if already exists):
```powershell
ssh-keygen -t ed25519
```

2.  **Send your public key to VM 01**:
Please run the following command in **Windows PowerShell** (be sure to replace your public key path):
```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <your-netid>@sp26-cs525-0601.cs.illinois.edu "cat >> ~/.ssh/authorized_keys"
```

### 3. Use Automation Scripts for Connection and Monitoring

You **no longer need** to enter lengthy domain names; run our Python assistants directly on your local machine:

#### 🔗 Quick Connection
```powershell
python .\scripts\connect.py
```
*   **VM 1-20**: Enter the number to connect directly.
*   **GPU Node**: Enter `g` for a one-click jump to Campus Cluster login machine (requires `srun` to obtain GPU).

#### 📊 Real-time Monitoring
```powershell
python .\scripts\live_monitor.py
```
*   **Real-time Dashboard**: Refreshes cluster-wide CPU/RAM/GPU status every 5 seconds.
*   **Troubleshooting**: Automatically distinguishes between `OFFLINE` (network disconnected) and `SSH TIMEOUT` (system frozen).

#### 🔍 Hardware Audit
```powershell
python .\scripts\hardware_monitor.py
```
*   **Deep Detection**: Get detailed specifications like CPU cache, remaining disk space, etc., for all machines in the cluster with one click.

#### 🛑 Cluster Power Management
```powershell
python .\scripts\cluster_power.py
```
*   **All Shutdown**: Default mode, sends `sudo poweroff` command to all 20 VMs.
*   **Single Shutdown**: Run `python .\scripts\cluster_power.py 5` to shutdown VM 05 only.
*   **Note**: This is a "blind-send" command; it will attempt to send the SSH shutdown signal regardless of whether the machine responds to Ping.

Based on previous manual query results, I have compiled a detailed **VM Hardware Specifications Manual** for you. You can use it as part of project documentation or include it in your **Survey Report** as experimental environment description.

---

# 🖥️ Cluster Node Specifications (sp26-cs525-06xx)

This cluster consists of 20 identically configured virtual machines, running on UIUC Engr-IT's VMware virtualization platform.

## 1. Core Hardware Parameters (Hardware Specs)

| Dimension | Detailed Specifications |
| --- | --- |
| **CPU Model** | Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz |
| **Architecture** | x86_64 (Intel Cascade Lake Microarchitecture) |
| **Cores** | 2 vCPUs (1 Socket, 2 Cores per socket) |
| **Memory (RAM)** | Total **7.5 GiB** (approx. 6.5 GiB usable) |
| **Storage (Disk)** | **32 GB** (approx. 27 GB remaining on root `/`) |
| **Virtualization Technology** | VMware Full Virtualization |

---

## 2. Cache Hierarchy

Since our experiments involve large-scale data processing (e.g., Distributed Grep), a large L3 cache will provide significant performance advantages:

*   **L1 Cache**: 128 KiB (64K Data / 64K Instruction)
*   **L2 Cache**: 2 MiB (1 MiB per core)
*   **L3 Cache**: **22 MiB** (shared by all cores)

---

## 3. Graphics and Auxiliary Computing (GPU/Accelerator)

*   **GPU**: Only **VMware SVGA II Adapter** detected.
*   **Conclusion**: This cluster **does not have physical GPUs** (No NVIDIA/AMD Hardware); all computing tasks rely on CPU multi-core concurrency.

---

## 4. Software Environment

*   **Operating System**: Ubuntu 24.04.1 LTS (Linux Kernel 6.8.0)
*   **Development Language**: Go (Golang) installed
*   **Compiler**: GCC installed

---

## 5. Storage Quota Reminder

> **Note**: Although the system shows 27GB of free space, please regularly clean up log files generated by experiments. If a single machine occupies more than 30GB, it may trigger system suspension or lead to SSH connection timeouts.
