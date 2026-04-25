import subprocess
with open('final_results.txt', 'w') as f:
    subprocess.run(['python', './scripts/verify_cluster.py'], stdout=f, stderr=f)
