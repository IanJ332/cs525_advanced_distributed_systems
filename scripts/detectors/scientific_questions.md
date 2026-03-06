# Scientific Questions (GrayPulse)

本项目的实验设计与数据采样旨在回答并验证以下核心研究问题（Research Questions, RQs）：

## RQ1: 检测信号 (Detection Signals)
**疑问**: 相比于底层硬件监控程序和网关错误率，端到端的延迟和排队行为是否能更早、更精准地捕获“灰阶故障（Gray Failures）”？
*   **假设 (H1)**: 基于应用层的细粒度信号（Queue Depth 与 P99 Latency）能够在不触发心跳报警的前提下，更早且准确地标记出由于资源争抢引发的局部响应退化（Gray Failure），而底层硬件指标（如 GPU 使用率或错误率日志）在此类故障中存在严重的延迟和盲区现象。

## RQ2: 根因区分 (Root Cause Differentiation)
**疑问**: 灰阶检测算法能否在全局高负载（流量高峰）和局部节点降级（真实故障）中做出准确区分？
*   **假设 (H2)**: 引入滑动窗口中位数与提取 MAD（绝对中位差）的 Robust Z-score 算法能够在全局流量压力正常波动时自我消音，而只会剥离并捕捉单节点行为特异产生的局部分布极值。

## RQ3: 修复开销 (Mitigation Overhead)
**疑问**: 基于路由隔离的（Z-score 剔除）策略是否能取得比微服务架构中常用的“对冲请求 (Request Hedging)”更低的额外开销？
*   **假设 (H3)**: 当某节点发生灰阶降速时，采用软剔除（Soft-drain）能够立刻恢复整个集群的 P99 延迟且几乎不产生额外开销；相反，Hedging 会带来严重的二次 CPU 和内网带宽 (Network Traffic) 开销，甚至诱发由于资源耗尽引发的级联雪崩。
