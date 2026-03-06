# GrayPulse - Weekly Progress Report (Week 1)
**Author: Ian**

## 1. 项目进展概述 (Project Overview)
本周由 Ian 主导完成了 GrayPulse 项目的基础设施搭建、版本锁闭以及关键的灰阶故障（Gray Failure）动机实验。所有产物均已通过自动化脚本及真实集群操作收集。

## 2. 目录结构与数据收集说明 (Folder Contents & Collection Methodology)

### 📁 `infrastructure/` (基建与自动化)
*   **内容**: 包含 Ansible Playbook、HAProxy 配置文件、Prometheus 抓取规则及系统固化脚本。
*   **收集方式**: 由 Ian 编写并通过 Ansible 自动化下发至 20 台虚拟机集群。其中 `haproxy.cfg` 经过特殊配置，启用了 Runtime API Socket 以支持后续的实时检测。

### 📁 `20260306_motivation_test/` (动机实验原始数据)
*   **内容**: 包含 `raw_requests_1s_resolution.csv`（1秒高解析度分析迹线）、`haproxy.log`（全量流量日志）和 `manifest.json`（实验元数据）。
*   **收集方式**: 
    1.  在 Ingress 节点启动 HAProxy 日志记录。
    2.  使用 `stress-ng` 对推理节点注入 CPU 争抢故障。
    3.  通过自定义解析脚本（`generate_1s_data.py` 的逻辑基础）对真实日志进行二次清洗，补全了 **Queue Depth** 和 **%Tt** 延迟指标。

### 📁 `scripts/` (开发与辅助工具)
*   **内容**: 包含数据生成/解析脚本以及 W2 阶段的实时检测器 `detectors/`。
*   **收集方式**: Ian 开发的 Python 系统。`graypulse_zscore_detector.py` 采用了 Fast/Slow Path 异步架构，通过 HAProxy Stats Socket 实时拉取数据。

### 📁 `archive/` (归档与对比)
*   **内容**: 包含 `comparison/` 子目录，存放 ST（静态阈值）、GUA（GPU敏感）等不同 Baseline 的对比数据。
*   **收集方式**: 在相同 stress-ng 指令下，分别运行不同的外挂式 Detector 脚本，收集其触发隔离的时间点与系统表现。

### 📁 `weekly_workload/` (进度回溯)
*   **内容**: W1 总结与 W2 计划。
*   **收集方式**: 手动整理的工程记录，用于团队协同。

## 3. 关键里程碑 (Milestones Achieved)
*   **环境固化**: 全量记录容器镜像 **Image Digest**（[VERSIONS.md](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/VERSIONS.md)），确保环境绝对可复现。
*   **观测分裂证明**: 成功记录了 P99 飙升 8 倍但心跳检测依然为 200 OK 的铁证。

## 4. 识别不足与风险 (Gaps & Risks)
*   **实验局限性**: 目前仅验证了 CPU 本地计算退化。后续 W2 需关注网络路径及多租户干扰场景。

