# Git History Sanitation Migration Guide

**Project**: `cs525_advanced_distributed_systems`  
**Date**: August 6, 2026  
**Target Audience**: Project Collaborators (Jisheng Jiang & Maojie Xu)

---

## 1. Reason for History Rewriting

The Git history of `cs525_advanced_distributed_systems` was rewritten using `git-filter-repo` to permanently remove legacy hardcoded SSH password assignments and personal local SSH key paths from historical commit objects. 

> [!WARNING]
> No plaintext secret strings are documented here. All collaborators must transition to the new repository HEAD immediately.

---

## 2. Migration Timeline & Cutoff Details

- **Cutoff Date**: August 6, 2026
- **Primary Branch**: `audit/gray-failure-repository-cleanup`
- **Action Required**: All team members must delete old local repository clones and perform a fresh clone from GitHub origin.

---

## 3. Step-by-Step Collaborator Migration Protocol

### Step 3.1: Save Uncommitted Local Work (If Applicable)
If you have uncommitted changes or unpushed work in an old clone, generate a patch before deleting the folder:
```bash
# In your OLD clone folder:
git diff > my_local_work.patch
```

### Step 3.2: Remove Old Clone
```bash
# Delete the old repository directory completely
rm -rf cs525_advanced_distributed_systems
```

### Step 3.3: Clone Fresh Repository
```bash
# Clone the updated repository from GitHub origin
git clone git@github.com:IanJ332/cs525_advanced_distributed_systems.git
cd cs525_advanced_distributed_systems
git checkout audit/gray-failure-repository-cleanup
```

### Step 3.4: Apply Saved Patch (If Applicable)
```bash
# Apply your saved patch to the fresh clone
git apply path/to/my_local_work.patch
```

---

## 4. CRITICAL RULES & WARNINGS

> [!CAUTION]
> 1. **DO NOT MERGE OR PUSH OLD BRANCHES**: Pushing an old un-sanitized commit will re-introduce historical secret strings into GitHub.
> 2. **ALWAYS USE LOCAL ENVIRONMENT VARIABLES**: Configure `CLUSTER_PASSWORD` in your local environment or `.env` file. Never hardcode credentials in source files.

---

## 5. Verification Commands

Run these commands in your fresh clone to verify proper setup:
```bash
# 1. Verify git log is clean
git log -n 5 --oneline

# 2. Verify environment variable enforcement
python scripts/cluster_ops.py
# (Expected output: RuntimeError: CLUSTER_PASSWORD environment variable is required)
```

---

## 6. Incident Contact

If an old branch is accidentally pushed or if you encounter any issue during migration, contact the repository maintainers immediately:
- Jisheng Jiang (`jisheng3@illinois.edu`)
- Maojie Xu (`maojiex2@illinois.edu`)
