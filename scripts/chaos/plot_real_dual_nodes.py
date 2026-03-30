import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def plot_real_dual_nodes():
    # 确保存档目录存在
    os.makedirs('data/figures', exist_ok=True)
    
    # 真实数据的相对路径
    file_05_lat = 'data/chaos_experiment/latency_results_05_runA.csv'
    file_05_stat = 'data/chaos_experiment/haproxy_status_05_runA.csv'
    file_06_lat = 'data/chaos_experiment/latency_results_06_runB.csv'
    file_06_stat = 'data/chaos_experiment/haproxy_status_06_runB.csv'
    
    try:
        df_05_lat = pd.read_csv(file_05_lat)
        df_05_stat = pd.read_csv(file_05_stat)
        df_06_lat = pd.read_csv(file_06_lat)
        df_06_stat = pd.read_csv(file_06_stat)
    except FileNotFoundError as e:
        print(f"Error: 找不到真实数据文件。请确保 CSV 路径正确。{e}")
        return

    # 数据预处理：统一时间轴、计算 P99 延迟、转换 UP/DOWN 状态
    def preprocess(df_lat, df_stat):
        df_lat['Timestamp_ISO'] = pd.to_datetime(df_lat['Timestamp_ISO'])
        df_stat['Timestamp_ISO'] = pd.to_datetime(df_stat['Timestamp_ISO'])
        
        start_time = min(df_lat['Timestamp_ISO'].min(), df_stat['Timestamp_ISO'].min())
        
        df_lat['timestamp'] = (df_lat['Timestamp_ISO'] - start_time).dt.total_seconds()
        df_stat['timestamp'] = (df_stat['Timestamp_ISO'] - start_time).dt.total_seconds()
        
        # 滑动窗口计算真实的 P99 延迟 (用真实的 Latency_ms 计算)
        df_lat['p99_latency'] = df_lat['Latency_ms'].rolling(window=10, min_periods=1).quantile(0.99)
        df_lat['p99_latency'] = df_lat['p99_latency'].fillna(df_lat['Latency_ms'])
        
        # 转换文字状态为数字状态，并专门处理空白报错列
        df_stat['status'] = df_stat['Status'].apply(lambda x: 1 if "UP" in str(x) else 0)
        
        return df_lat, df_stat

    df_05_lat, df_05_stat = preprocess(df_05_lat, df_05_stat)
    df_06_lat, df_06_stat = preprocess(df_06_lat, df_06_stat)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
    
    def plot_node(ax, df_lat, df_stat, title):
        color_lat = 'tab:red'
        color_stat = 'tab:blue'
        
        # 绘制真实的延迟曲线 (左轴)
        ax.plot(df_lat['timestamp'], df_lat['p99_latency'], color=color_lat, alpha=0.8, linewidth=1.5, label='Real P99 Latency')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('P99 Latency (ms)', color=color_lat, fontweight='bold')
        ax.tick_params(axis='y', labelcolor=color_lat)
        ax.set_ylim(bottom=0, top=df_lat['p99_latency'].max() * 1.3) # 增加顶部空间
        
        # 绘制 HAProxy 状态曲线 (右轴) - 改用阶梯曲线 (Step) 更符合状态监控的实际
        ax_stat = ax.twinx()
        ax_stat.step(df_stat['timestamp'], df_stat['status'], color=color_stat, linestyle='--', linewidth=2, label='HAProxy Status', where='post')
        ax_stat.set_ylabel('Status (1=UP, 0=DOWN)', color=color_stat, fontweight='bold')
        ax_stat.tick_params(axis='y', labelcolor=color_stat)
        ax_stat.set_ylim(-0.2, 1.5) # 提高上限，将 Status 1.0 的线向上推，避开文字
        ax_stat.set_yticks([0, 1])
        
        # 标注故障注入区 (实际时间为 30s 到 60s)
        ax.axvspan(30, 60, color='gray', alpha=0.2, label='Gray Failure Zone (stress-ng)')
        # 将文字垂直位置下调到 65% 处，避开上方的线条
        ax.text(45, ax.get_ylim()[1] * 0.65, 'Differential\nObservability', ha='center', color='dimgray', fontweight='bold', fontsize=12)
        
        ax.set_title(title, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # 合并图例
        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax_stat.get_legend_handles_labels()
        ax.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    # 绘制双节点
    plot_node(ax1, df_05_lat, df_05_stat, 'VM 05 (gpu1) - Gray Failure Injected')
    plot_node(ax2, df_06_lat, df_06_stat, 'VM 06 (gpu2) - Symmetrical Run')

    plt.suptitle('Figure 1: Real Telemetry of Differential Observability (100ms Resolution)', fontsize=16, fontweight='bold', y=1.05)
    plt.tight_layout()
    
    save_path = 'data/figures/gray_failure_analysis_dual_nodes.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Successfully generated data-driven plot at: {save_path}")

if __name__ == "__main__":
    plot_real_dual_nodes()
