# GrayPulse - Weekly Plan (Week 2)

## 核心任务: 灰阶故障检测算法 (Detection Module)
本周目标是彻底解决我们在 W1 动机实验中发现的观测分裂现象，不采用静态粗暴阈值 (ST) 或底层非关联指标 (GUA)，改从上层端到端服务延迟与队列特性入手，实现无监督高维感知异常检测器。

### 当前主要里程碑 (Milestones & Epics)
*   **[DONE] 算法回测 (Algorithm Backtesting)**: 
    *   完成了 `zscore_backtest.py` 的编写，使用 $L_i$ (端到端延迟) 和 $Q_i$ (队列深度) 计算滑动窗口中位数，提取全局历史数据的 MAD (Median Absolute Deviation) 绝对中位差作为稳定除数。
    *   在 W1 原生数据集上成功跑通，防除了 epsilon 计算被 0 除的情况，并在连续检测到 3 次 $zL_i \geq 3$ 且 $zQ_i \geq 2$ 时精确触发了 `Suspicious` 全局告警。
*   **[PLANNED] 集群联合打通 (Cluster Integration)**:
    *   将离线的 `zscore_backtest.py` 改写为针对 HAProxy 的 Socket Log Streaming 的外挂流式分析模块。
    *   真正对接 `socat` 下发 `state drain` 动态切割后端异常流量。

### W2 下发交付物 (Expected Artifacts)
1.  基于 Robust Z-score 的 `graypulse_daemon.py`。
2.  完成真机 W2 集群环境注入实验的数据源导出对齐。
