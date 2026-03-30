import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def analyze_and_plot_cdf():
    file_path = 'data/chaos_experiment/latency_results_05_runA.csv'
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: 找不到数据文件 {file_path}")
        return

    # 1. 数据的导入与物理时间戳转换
    df = pd.read_csv(file_path)
    df['Timestamp_ISO'] = pd.to_datetime(df['Timestamp_ISO'])
    start_time = df['Timestamp_ISO'].min()
    df['timestamp'] = (df['Timestamp_ISO'] - start_time).dt.total_seconds()
    
    # 2. 数据切分 (Data Slicing)
    baseline = df[(df['timestamp'] >= 0) & (df['timestamp'] < 30)]['Latency_ms']
    fault = df[(df['timestamp'] >= 30) & (df['timestamp'] <= 90)]['Latency_ms']
    
    # 3. 计算关键指标 (Statistical Summary)
    def calc_stats(series):
        return {
            'Mean': series.mean(),
            'StdDev': series.std(),
            'P50': series.quantile(0.50),
            'P90': series.quantile(0.90),
            'P95': series.quantile(0.95),
            'P99': series.quantile(0.99),
            'Max': series.max()
        }

    stats_b = calc_stats(baseline)
    stats_f = calc_stats(fault)
    
    deg_ratio = stats_f['P99'] / stats_b['P99']

    # 4. 生成 Markdown 表格
    os.makedirs('data/metrics', exist_ok=True)
    md_table = f"""## Latency Quantitative Analysis (VM 05 Run A)

| Metric | Baseline (0-30s) | Fault Zone (30-90s) | Degrade. Ratio |
|--------|------------------|---------------------|----------------|
| Mean   | {stats_b['Mean']:.2f} ms | {stats_f['Mean']:.2f} ms | {stats_f['Mean']/stats_b['Mean']:.1f}x |
| StdDev | {stats_b['StdDev']:.2f} ms | {stats_f['StdDev']:.2f} ms | - |
| P50    | {stats_b['P50']:.2f} ms | {stats_f['P50']:.2f} ms | - |
| P90    | {stats_b['P90']:.2f} ms | {stats_f['P90']:.2f} ms | - |
| P95    | {stats_b['P95']:.2f} ms | {stats_f['P95']:.2f} ms | - |
| **P99**| **{stats_b['P99']:.2f} ms** | **{stats_f['P99']:.2f} ms** | **{deg_ratio:.1f}x** |
| Max    | {stats_b['Max']:.2f} ms | {stats_f['Max']:.2f} ms | - |

> Critical Insight: The Gray Failure starvation caused the P99 tail latency to degrade by a factor of **{deg_ratio:.1f}x**.
"""
    with open('data/metrics/latency_summary_05.md', 'w', encoding='utf-8') as f:
        f.write(md_table)
    print("✅ Successfully wrote Markdown table to data/metrics/latency_summary_05.md")

    # 5. 绘制 CDF 图像
    os.makedirs('data/figures', exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))

    def plot_cdf(data_series, color, label, p99_val, x_offset_ratio):
        sorted_data = np.sort(data_series.dropna())
        yvals = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        ax.plot(sorted_data, yvals, color=color, linewidth=2, label=label)
        
        # 标注 P99
        ax.scatter(p99_val, 0.99, color=color, s=50, zorder=5)
        
        # 为了保证 Log 刻度下标出的箭头好看，X轴上偏移使用比例
        text_x = p99_val * x_offset_ratio
        # 对于 Fault 这种长尾很大的，向左偏移 (ratio < 1)，Baseline 向左一点 (ratio < 1) 也行
        ax.annotate(f"{label} P99\n{p99_val:.0f} ms",
                    xy=(p99_val, 0.99), xytext=(text_x, 0.82),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
                    color=color, fontweight='bold', ha='center',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, alpha=0.9))

    # X 轴偏移率：Baseline 让字靠左，Fault 也靠左防止越界
    plot_cdf(baseline, 'tab:blue', 'Baseline (0-30s)', stats_b['P99'], 0.4)
    plot_cdf(fault, 'tab:red', 'Fault Zone (30-90s)', stats_f['P99'], 0.4)

    ax.set_xscale('log')
    # 动态设定 X 轴极限
    min_x = max(1, baseline.min() * 0.5)
    max_x = fault.max() * 2.0
    ax.set_xlim(left=min_x, right=max_x)
    
    ax.set_title("Figure 2: Cumulative Distribution Function (CDF) of Inference Latency", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Latency (ms) [Log Scale]', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cumulative Probability (CDF)', fontsize=12, fontweight='bold')
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.grid(True, which="both", ls=":", alpha=0.6)
    
    # 添加辅助线在 0.99 处
    ax.axhline(y=0.99, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    ax.legend(loc='lower right', fontsize=12, facecolor='white', framealpha=1.0)

    save_path = 'data/figures/latency_cdf_05.png'
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Successfully generated CDF plot at {save_path}")
    print(f"\n📊 [Script Output] The Degradation Ratio (Fault P99 / Baseline P99) is: {deg_ratio:.2f}x")

if __name__ == "__main__":
    analyze_and_plot_cdf()
