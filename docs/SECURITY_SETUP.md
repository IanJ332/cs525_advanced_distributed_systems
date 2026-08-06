# Security Setup & Secret Management Guide

**Project**: GrayPulse Distributed Inference Observatory  
**Scope**: Credentials, SSH Keys, Environment Variables, and Secret Hygiene

---

## 1. Environment Variable Architecture

This repository strictly enforces **zero hardcoded credentials**. All cluster authentication tokens, passwords, and user identifiers must be supplied via local environment variables.

### Required Environment Variables

| Variable Name | Description | Example / Allowed Values | Required? |
| :--- | :--- | :--- | :--- |
| `CLUSTER_PASSWORD` | SSH password for cluster virtual machine nodes | *Provided securely by admin* | **YES** |
| `CLUSTER_USER` | SSH username / NetID for cluster nodes | `jisheng3` | Optional (default: `jisheng3`) |
| `CLUSTER_BASE_URL` | Subdomain prefix for cluster nodes | `sp26-cs525-06` | Optional |
| `CLUSTER_DOMAIN` | Cluster FQDN suffix | `.cs.illinois.edu` | Optional |
| `SSH_KEY_PATH` | Path to local SSH ed25519 or RSA private key | `~/.ssh/id_ed25519` | Optional |

---

## 2. Local Setup Instructions

### Step 1: Copy Environment Template
Copy `.env.example` to `.env` in the repository root:
```bash
cp .env.example .env
```

### Step 2: Configure Environment Secrets
Edit `.env` locally (this file is excluded by `.gitignore` and **must never be committed**):
```bash
CLUSTER_USER=your_netid
CLUSTER_PASSWORD=your_actual_cluster_password
```

### Step 3: Export Variables in Shell
```bash
# On Linux/macOS
export CLUSTER_PASSWORD="your_actual_cluster_password"

# On Windows PowerShell
$env:CLUSTER_PASSWORD="your_actual_cluster_password"
```

---

## 3. SSH Key Configuration

Do not hardcode absolute user paths (such as `/Users/username/.ssh/id_ed25519` or `C:/path/to/key`). Use relative or home-expanded paths:

- Linux / macOS: `~/.ssh/id_ed25519`
- Windows PowerShell: `$HOME\.ssh\id_ed25519`

Ansible playbooks and inventories must reference `~/.ssh/id_ed25519` or `{{ ansible_env.HOME }}/.ssh/id_ed25519`.

---

## 4. Git Hygiene & Pre-Commit Rules

1. **Never commit `.env` or `.env.local` files.** Only `.env.example` containing non-secret placeholder values may be tracked in Git.
2. **Never log credentials.** Python scripts must catch authentication errors without including password values in exception tracebacks or stdout.
3. **Verify Git status before committing**:
   ```bash
   git status
   git diff
   ```
