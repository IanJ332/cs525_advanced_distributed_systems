# cs525_advanced_distributed_systems

# 🚀 CS525 Distributed Systems 集群配置指南

本文档旨在帮助团队成员快速配置实验环境，实现对 20 台 VM 节点的快速访问与自动化管理。

---

## 🛠️ 我已经完成了什么？ (Infrastructure Status)

* **环境初始化**：确认并测试了全集群 20 台机器的硬件规格（Intel Xeon Silver 4216, 8GB RAM, 32GB Disk）。
* **建立信任根**：我已将我的本地公钥（Public Key）分发至 **VM 01**，实现了本地与该节点的免密安全连接。
* **内网打通**：
* **VM 01** 作为“堡垒机”，已经具备了连接 **VM 02-20** 的内网访问权限。
* 通过脚本批量测试，确认了全集群 20 台节点的 SSH 服务均处于响应状态。


* **开发工具链**：编写并测试了以下 Python 自动化工具：
* `ignition.py`：用于全集群状态实时巡检。
* `connect.py`：用于本地终端一键交互式连接指定节点。



---

## 👥 队友需要做什么？ (Action Items)

为了能像我一样“秒连” 20 台机器，请按照以下三个步骤操作：

### 1. 基础环境准备

* **VPN 连接**：确保 **Cisco AnyConnect** 始终处于 **"2 Tunnel All"** 模式，否则无法触达 UIUC 内部私有 IP 段。
* **拉取仓库**：从我们的 GitHub 仓库拉取最新的 `scripts/` 文件夹。

### 2. 建立本地到 VM 01 的免密登录

这是最关键的一步，只需执行一次，即可免去每次输入密码的烦恼：

1. **生成本地密钥**（如果已有可跳过）：
```powershell
ssh-keygen -t ed25519

```


2. **将你的公钥发送到 VM 01**：
请在 **Windows PowerShell** 中运行以下命令（注意替换你的公钥路径）：
```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh jisheng3@sp26-cs525-0601.cs.illinois.edu "cat >> ~/.ssh/authorized_keys"

```



### 3. 使用自动化脚本连接

以后**不需要**再输入冗长的域名，直接在你的本地运行我们的 Python 助手：

```powershell
python .\scripts\connect.py

```

* **操作方式**：运行后输入编号（**1-20**）即可瞬间直连对应服务器。
* **进阶用法**：成功登录 **VM 01** 后，由于内网已信任，你可以直接从 VM 01 访问其他节点（02-20），无需重复验证。

根据你之前手动查询的结果，我为你整理了一份详尽的 **VM 硬件规格说明书**。你可以直接将其作为项目文档的一部分，或者放在你的 **Survey Report** 中作为实验环境描述。

---

# 🖥️ Cluster Node Specifications (sp26-cs525-06xx)

本集群由 20 台配置完全一致的虚拟机组成，运行于 UIUC Engr-IT 的 VMware 虚拟化平台。

## 1. 核心硬件参数 (Hardware Specs)

| 维度 | 详细规格 (Detailed Specifications) |
| --- | --- |
| **CPU 型号** | Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz |
| **架构** | x86_64 (Intel Cascade Lake 微架构) |
| **核心数** | 2 vCPUs (1 Socket, 2 Cores per socket) |
| **内存 (RAM)** | 总计 **7.5 GiB** (可用约 6.5 GiB) |
| **存储 (Disk)** | **32 GB** (根目录 `/` 剩余约 27 GB) |
| **虚拟化技术** | VMware Full Virtualization |

---

## 2. 缓存体系 (Cache Hierarchy)

由于我们的实验涉及大规模数据处理（如 Distributed Grep），大容量的 L3 缓存将提供显著的性能优势：

* **L1 Cache**: 128 KiB (64K Data / 64K Instruction)
* **L2 Cache**: 2 MiB (每核 1 MiB)
* **L3 Cache**: **22 MiB** (所有核心共享)

---

## 3. 图形与辅助计算 (GPU/Accelerator)

* **GPU**: 仅检测到 **VMware SVGA II Adapter**。
* **结论**: 本集群 **不具备物理 GPU** (No NVIDIA/AMD Hardware)，所有计算任务均依赖 CPU 多核并发。

---

## 4. 软件环境 (Software Environment)

* **操作系统**: Ubuntu 24.04.1 LTS (Linux Kernel 6.8.0)
* **开发语言**: Go (Golang) 已安装
* **编译器**: GCC 已安装

---

## 5. 存储配额提醒 (Storage Warning)

> **注意**：虽然系统显示有 27GB 剩余空间，但请务必定期清理实验产生的日志文件。如果单台机器占用超过 30GB，可能会触发系统挂起或导致 SSH 连接超时。

