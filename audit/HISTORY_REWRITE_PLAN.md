# Git History Sanitation & Secret Removal Plan

**Project**: `cs525_advanced_distributed_systems`  
**Branch**: `audit/gray-failure-repository-cleanup`  
**Status**: Plan Prepared (Execution Paused — Awaiting Authorization)

---

## 1. Executive Summary

This document specifies the exact steps, safety procedures, and commands required to rewrite Git commit history and permanently remove exposed credentials from past commits using `git-filter-repo`.

> [!CAUTION]
> **DO NOT EXECUTE THIS PLAN UNTIL AUTHORIZED.**  
> History rewriting alters Git commit SHAs and requires all collaborators to re-clone the repository.

---

## 2. Affected Secret Patterns & Commit Scope

- **Exposed Secret Type**: Hardcoded SSH password assignments in python scripts (`PASSWORD = "[REDACTED]"`).
- **Exposed Path Type**: Local SSH key absolute paths (`/Users/ian/.ssh/[REDACTED]`).
- **Affected Commits**: 24 commits spanning from `298b53be` (*feat: complete W1 infrastructure...*) to `0449b276` (*all*).
- **Affected Branches**: `main`, `audit/gray-failure-repository-cleanup`.
- **Affected Tags**: None.

---

## 3. Pre-Rewrite Backup Procedure

Before executing any history-rewriting command, create a full offline mirror backup of the repository:

```bash
# 1. Create a local backup clone outside the workspace
git clone --mirror c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems C:\Users\ian\Desktop\cs525_repo_backup_FULL.git

# 2. Verify backup integrity
git -C C:\Users\ian\Desktop\cs525_repo_backup_FULL.git log -n 5 --oneline
```

---

## 4. Exact `git-filter-repo` Execution Commands

### Step 4.1: Install Tooling
```bash
pip install git-filter-repo
```

### Step 4.2: Create Replacement Rule File (`expressions.txt`)
Create a temporary file `expressions.txt` (do not include actual passwords):

```text
# Replace password assignments with environment variable lookup
regex:PASSWORD\s*=\s*"[REDACTED_SECRET]"==PASSWORD = os.environ.get("CLUSTER_PASSWORD")
regex:PASSWORD\s*=\s*'[REDACTED_SECRET]'==PASSWORD = os.environ.get("CLUSTER_PASSWORD")

# Replace absolute local SSH paths with home variable
regex:/Users/ian/\.ssh/id_ed25519==~/.ssh/id_ed25519
regex:***REMOVED***
```

### Step 4.3: Run Sanitation
```bash
git filter-repo --replace-text expressions.txt --force
```

---

## 5. Post-Rewrite Validation Procedure

Verify that no secret strings remain in any commit object:

```bash
# 1. Search full git log for password assignments
git log -p --all -GPASSWORD

# 2. Verify scripts compile cleanly
python -m py_compile scripts/*.py

# 3. Check git object database size
git count-objects -vH
```

---

## 6. Remote Force-Push & Collaborator Re-Clone Instructions

Once validated locally:

### 1. Force Push to Remote (Requires Repository Admin Approval)
```bash
# Re-add remote if git-filter-repo cleared remotes
git remote add origin git@github.com:IanJ332/cs525_advanced_distributed_systems.git

# Force-push updated main and audit branches
git push origin main --force
git push origin audit/gray-failure-repository-cleanup --force
```

### 2. Collaborator Re-Clone Procedure
All team members (Jisheng Jiang and Maojie Xu) must discard local clones and re-clone from remote:
```bash
git clone git@github.com:IanJ332/cs525_advanced_distributed_systems.git
```

---

## 7. Emergency Rollback Procedure

If history rewriting fails or causes commit corruption:

```bash
# Restore working repository from offline backup
rm -rf c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems
git clone C:\Users\ian\Desktop\cs525_repo_backup_FULL.git c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems
```

---

*End of History Rewrite Plan.*
