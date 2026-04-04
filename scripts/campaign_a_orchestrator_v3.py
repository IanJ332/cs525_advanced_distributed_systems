import paramiko
import sys
import time

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
    print("🚀 CAMPAIGN A v3: Research Agent 认证架构 (终极版)")
    
    print("[1/4] 重启网关为 Smart 模式...")
    # 强制清理确保端口释放
    remote_cmd(GW_NODE, "pkill -f gateway_dual_mode; pkill -f gateway_sentinel; nohup python3 gateway_dual_mode.py --mode smart --port 8080 > smart.log 2>&1 &")
    time.sleep(5)
    
    print("[2/4] 清理远端脏数据并推送 V3 引擎...")
    client_load = paramiko.SSHClient()
    client_load.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_load.connect(LOAD_NODE, username=USERNAME, password=PASSWORD)
    
    # 批量清理旧结果
    client_load.exec_command("rm -f ~/campaign_a_cv_c*.csv ~/smoke*.csv")
    
    sftp = client_load.open_sftp()
    sftp.put('scripts/campaign_a_engine_v3.py', '/home/jisheng3/campaign_a_engine_v3.py')
    
    print("[3/4] 执行远端冒烟测试 (Remote Smoke Gate)...")
    _, stdout, stderr = client_load.exec_command("python3 campaign_a_engine_v3.py --smoke-test")
    # 阻塞直到冒烟结果返回
    exit_status = stdout.channel.recv_exit_status()
    output_text = stdout.read().decode()
    print("=== 冒烟测试输出 ===")
    print(output_text)
    
    if exit_status != 0:
        print("🚨 远端冒烟测试失败！已拦截后续压测。请检查 Backend 或 Gateway 状态！")
        sys.exit(1)
        
    print("✅ 远端冒烟测试 200 OK！链路完全自洽，开始正式压测！")
    client_load.close()

    concurrencies = [16, 24, 32, 48, 64]
    for c in concurrencies:
        print(f"\n[SWEEP] 并发={c} | 持续时间 240s")
        out_file = f"campaign_a_cv_c{c}.csv"
        run_cmd = f"python3 campaign_a_engine_v3.py --concurrency {c} --duration 240 --output {out_file}"
        print(f"--> VM 02 发射指令: {run_cmd}")
        client, (_, stdout_load, _) = remote_cmd(LOAD_NODE, run_cmd, get_pty=True)
        
        print("--> (A) 稳态数据收集中 (90s)...")
        time.sleep(90)
        
        print("--> (B) 注入灰色故障 (VM 05 stress-ng, 90s)...")
        fail_client, _ = remote_cmd(WORKER_FALLIBLE, f"echo '{PASSWORD}' | sudo -S stress-ng --cpu 2 --vm 1 --vm-bytes 80% --timeout 90s")
        
        print("--> (C) 等待恢复期结束并采集剩余波段...")
        # 阻塞直到压测脚本自行退出
        stdout_load.channel.recv_exit_status()
        client.close()
        fail_client.close()
        print(f"✅ Sweep 并发 {c} 已收官。冷却 10 秒...")
        time.sleep(10)
        
    print("\n[COMPLETE] Campaign A V3 压测矩阵完美结束。")

if __name__ == "__main__":
    run_campaign_a()
