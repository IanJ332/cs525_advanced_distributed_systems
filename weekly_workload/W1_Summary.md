# GrayPulse - Weekly Progress Report (Week 1)

## 1. 已完成事项 (Milestones Achieved)
本周成功完成了 GrayPulse 项目的分布式基础设施搭建与核心动机实验验证。

*   **环境固化 (Environment Hardening)**:
    *   完成了 20 台虚拟机（sp26-cs525-0601 至 0620）的自动化角色分配（Ingress x2, Control x2, GPU Inference x2, Replay/Fault x14）。
    *   全量记录容器镜像 **Image Digest**（如 HAProxy 和 Triton），消除 Tag 漂移风险。
    *   通过 `freeze_sysctl.sh` 实现了全节点 Linux 内核参数的一致性固化。
*   **模型部署 (Model Preparation)**:
    *   成功在 A10 GPU 节点上部署了 Triton Inference Server。
    *   完成了 ResNet50 (Vision) 与 BERT (Text) 模型的导出、加载与基础压力测试 (Perf Analyzer)。
*   **动机实验 (Core Motivation Test)**:
    *   在分布式集群中成功复现并记录了 **“观测分裂 (Differential Observability)”** 这一铁证。
    *   **关键发现**: 注入 30%-50% CPU 故障后，P99 延迟及 Queue Depth 飙升约 8-15 倍，但 HAProxy 心跳检测（Liveliness Check）返回 200 OK，证明了常规健康检查对“灰阶故障”的感知盲点。

## 2. 关键产物索引 (Key Artifacts Index)
*   **全局版本定义**: [VERSIONS.md](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/VERSIONS.md)
*   **Ansible 清单**: [infrastructure/inventory.yml](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/infrastructure/inventory.yml)
*   **1s 高解析度数据集**: [20260306_motivation_test/raw_requests_1s_resolution.csv](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/20260306_motivation_test/raw_requests_1s_resolution.csv)
*   **冲突证据报告**: [20260306_motivation_test/evidence_summary.log](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/20260306_motivation_test/evidence_summary.log)
*   **证据归档**: [archive/20260306_motivation_test/](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/archive/20260306_motivation_test/)

## 3. 识别不足与风险 (Gaps & Risks)
*   **实验局限性**: 目前的动机实验仅验证了 **CPU 本地计算退化** 导致的故障。尚未覆盖如网络随机抖动（Jitter）、磁盘 I/O 争抢等其他可能引发灰阶故障的物理层/共享路径瓶颈。
*   **模型多样性**: 压测主要针对计算机视觉与 NLP 推理，尚未测试大语言模型 (LLM) 在极端显存占用下的表现。
