---
name: sync-docs
description: Run the Automated Documentation Sync engine against the current git working tree or a specified diff range.
---

# Run Documentation Sync

Execute the sync engine CLI to synchronise Markdown documentation with Python source changes.

## Instructions

1. Check that `scripts/run_sync.py` exists. If not, Stage 5 (implementation) has not completed — stop and say so.
2. Ensure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the sync engine in the appropriate mode:

   **Manual mode** (current working tree):
   ```bash
   python scripts/run_sync.py --mode manual
   ```

   **PR mode** (diff between two refs):
   ```bash
   python scripts/run_sync.py --mode pr --base-ref HEAD~1 --head-ref HEAD
   ```

   **Explicit file list**:
   ```bash
   python scripts/run_sync.py --mode manual --changed-files "modified:src/sync_engine/mapper.py"
   ```

4. Show the sync report output.
5. If the report indicates any validation failures or errors, display them clearly and suggest fixes.
