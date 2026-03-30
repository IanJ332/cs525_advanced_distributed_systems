import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def process_and_plot():
    # Setup subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('High-Precision Gray Failure Analysis (100ms Sampling)', fontsize=16, fontweight='bold')
    
    # Locate data files relative to script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data/chaos_experiment')
    fig_dir = os.path.join(base_dir, '../../data/figures')
    os.makedirs(fig_dir, exist_ok=True)
    
    metrics_summary = []

    for i, (vm_id, run_lbl) in enumerate([("05", "runA"), ("06", "runB")]):
        ax1 = axes[i]
        
        lat_path = os.path.join(data_dir, f'latency_results_{vm_id}_{run_lbl}.csv')
        stat_path = os.path.join(data_dir, f'haproxy_status_{vm_id}_{run_lbl}.csv')
        
        if not os.path.exists(lat_path) or not os.path.exists(stat_path):
            print(f"Skipping {vm_id} because files are missing in {data_dir}.")
            continue
            
        lat_df = pd.read_csv(lat_path)
        lat_df['Timestamp_ISO'] = pd.to_datetime(lat_df['Timestamp_ISO'])
        start_time = lat_df['Timestamp_ISO'].iloc[0]
        lat_df['Time_s'] = (lat_df['Timestamp_ISO'] - start_time).dt.total_seconds()
        
        stat_df = pd.read_csv(stat_path)
        stat_df['Timestamp_ISO'] = pd.to_datetime(stat_df['Timestamp_ISO'])
        stat_df['Time_s'] = (stat_df['Timestamp_ISO'] - start_time).dt.total_seconds()
        
        # Clean status column and convert to 1 (UP) or 0 (DOWN)
        stat_df['UP'] = stat_df['Status'].apply(lambda x: 1 if "UP" in str(x) else 0)
        
        # Calculate Rolling Average Latency for smooth representation
        lat_df['Smooth_Latency'] = lat_df['Latency_ms'].rolling(window=10, min_periods=1).mean()
        
        # PLOT: Ax1 (Latency)
        ax1.scatter(lat_df['Time_s'], lat_df['Latency_ms'], color='tab:cyan', alpha=0.2, s=5, label='Raw Requests')
        ax1.plot(lat_df['Time_s'], lat_df['Smooth_Latency'], color='tab:blue', linewidth=2, label='Avg Latency (Smoothed)')
        
        ax1.set_xlabel('Experiment Time (Seconds)', fontsize=12)
        ax1.set_ylabel('Inference Latency (ms)', color='tab:blue', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        
        # Set latency limits dynamically with some headroom
        ymax_lat = lat_df['Smooth_Latency'].max() * 1.5
        ax1.set_ylim(0, max(ymax_lat, 100))
        
        # PLOT: Ax2 (Status)
        ax2 = ax1.twinx()
        ax2.step(stat_df['Time_s'], stat_df['UP'], color='tab:red', linestyle='--', linewidth=2, label='HAProxy Probe State', where='post')
        ax2.set_ylabel('Health Status (1=UP, 0=DOWN)', color='tab:red', fontsize=12, fontweight='bold')
        ax2.set_ylim(-0.2, 1.2)
        ax2.set_yticks([0, 1])
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        # Gray Failure Zone Injection Rectangle (30s -> 60s)
        ax1.axvspan(30, 60, color='gray', alpha=0.3, label='stress-ng CPU/L3 Fault')
        
        # Add Text Annotation
        ax1.annotate('Differential Observability Zone\n(HAProxy Blind Spot)', 
                     xy=(45, lat_df['Smooth_Latency'].max() * 0.9), 
                     xytext=(45, ax1.get_ylim()[1] * 0.8),
                     ha='center', va='bottom', fontsize=10, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1, alpha=0.8),
                     arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color='black', lw=2))
        
        ax1.set_title(f'Run {run_lbl[-1]}: VM {vm_id} Target', fontsize=14)
        
        # Merge legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        # To avoid duplicate 'stress-ng' labels across subplots we can skip them or let it be
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10, facecolor='white', framealpha=0.9)
        
        ax1.grid(True, linestyle=':', alpha=0.6)
        
        # Summarize stats for README
        mean_base = lat_df[lat_df['Time_s'] < 30]['Latency_ms'].mean()
        p99_fault = lat_df[(lat_df['Time_s'] >= 30) & (lat_df['Time_s'] <= 60)]['Latency_ms'].quantile(0.99)
        mean_recov = lat_df[lat_df['Time_s'] > 60]['Latency_ms'].mean()
        metrics_summary.append((vm_id, mean_base, p99_fault, mean_recov))

    plt.tight_layout(rect=[0, 0, 1, 0.95]) # Make room for suptitle
    
    out_path = os.path.join(fig_dir, 'gray_failure_analysis_dual_nodes.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved successfully to {out_path}")
    
    print("\n--- Summary for README ---")
    for vm, base, p99, recov in metrics_summary:
        print(f"VM {vm}: Base={base:.1f}ms | Fault P99={p99:.1f}ms | Recovery={recov:.1f}ms")

if __name__ == '__main__':
    process_and_plot()
