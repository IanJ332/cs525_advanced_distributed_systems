import paramiko
import sys
import time
import os

GW_NODE = "sp26-cs525-0601.cs.illinois.edu"
LOAD_NODE = "sp26-cs525-0602.cs.illinois.edu"
WORKER_FALLIBLE = "sp26-cs525-0605.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def remote_cmd(host, cmd, get_pty=False):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    return client, client.exec_command(cmd, get_pty=get_pty)

def run_campaign_a():
    print("🚀 CAMPAIGN A v2: 严格对齐的高并发与故障注入")
    
    print("[1/5] 正在重启 VM 01 上的智能网关...")
    remote_cmd(GW_NODE, "pkill -f gateway_dual_mode; nohup python3 gateway_dual_mode.py --mode smart --port 8080 > smart.log 2>&1 &")
    time.sleep(5)
    
    print("[2/5] 正在将修复后的 v2 压测引擎同步至 VM 02...")
    client_load = paramiko.SSHClient()
    client_load.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_load.connect(LOAD_NODE, username=USERNAME, password=PASSWORD)
    sftp = client_load.open_sftp()
    # 强制覆盖为我们刚写的 v2 版本
    sftp.put('scripts/campaign_a_engine_v2.py', '/home/jisheng3/campaign_a_engine_v2.py')
    
    print("[3/5] 清除 VM 02 上的历史脏数据...")
    client_load.exec_command("rm -f ~/campaign_a_cv_c*.csv ~/smoke_test*.csv")
    
    print("[4/5] 执行远端冒烟测试 (Remote Smoke Test)...")
    # 让 VM 02 运行你之前成功的单发脚本
    _, stdout, stderr = client_load.exec_command("python3 bombard_engine_v2.py")
    smoke_output = stdout.read().decode()
    print("=== 远端冒烟测试输出 ===")
    print(smoke_output)
    
    if "200 OK" not in smoke_output:
        print("🚨 警报：远端冒烟测试失败！已拦截后续无效高并发。请检查日志。")
        sys.exit(1)
        
    print("✅ 远端冒烟测试通过！系统链路完全闭环，开始阶梯轰炸！")
    client_load.close()

    concurrencies = [16, 24, 32, 48, 64]
    
    for c in concurrencies:
        print(f"\n[SWEEP] 并发={c} | 持续时间 240s")
        out_file = f"campaign_a_cv_c{c}.csv"
        
        # 使用修复后的 v2 脚本
        run_cmd = f"python3 campaign_a_engine_v2.py --concurrency {c} --duration 240 --output {out_file}"
        print(f"--> VM 02 执行命令: {run_cmd}")
        client, (_, stdout_load, _) = remote_cmd(LOAD_NODE, run_cmd, get_pty=True)
        
        print("--> 稳态数据收集中 (90s)...")
        time.sleep(90)
        
        print("--> 对 VM 05 注入灰色故障 (90s)...")
        fail_client, _ = remote_cmd(WORKER_FALLIBLE, f"echo '{PASSWORD}' | sudo -S stress-ng --cpu 2 --vm 1 --vm-bytes 80% --timeout 90s")
        
        print("--> 等待恢复期结束及引擎退出...")
        # 正确等待远端命令执行结束，而不是野蛮抛出
        stdout_load.channel.recv_exit_status()
        client.close()
        fail_client.close()
        
        print(f"✅ Sweep C{c} 已完成并落盘。")
        time.sleep(10) # 冷却 10 秒
        
    print("\n[COMPLETE] Campaign A 物理极限探查结束。")

if __name__ == "__main__":
    run_campaign_a()
