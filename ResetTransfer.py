#!/usr/bin/env python3
"""Reset script for P4Transfer workspaces.

Convenience script to clean workspace state before re-running P4Transfer.py.
Reads transfer.yaml (or a config specified via -c) and:
  - Reverts open files, syncs to #none, and deletes pending CLs on source workspace
  - Reverts open files, syncs to #none, and deletes pending CLs on target workspace
  - Deletes all contents under workspace_root
  - Deletes *.log files in the script's directory
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys

from ruamel.yaml import YAML


def load_config(config_file):
    """Load and return the transfer YAML config."""
    yaml = YAML()
    with open(config_file, "r") as f:
        config = yaml.load(f)
    return config


def build_p4_cmd(section):
    """Build base p4 command list from a config section (source or target)."""
    cmd = ["p4"]
    if section.get("p4port"):
        cmd += ["-p", str(section["p4port"])]
    if section.get("p4user"):
        cmd += ["-u", str(section["p4user"])]
    if section.get("p4client"):
        cmd += ["-c", str(section["p4client"])]
    if section.get("p4charset"):
        cmd += ["-C", str(section["p4charset"])]
    if section.get("p4passwd"):
        cmd += ["-P", str(section["p4passwd"])]
    return cmd


def run_p4(base_cmd, args, label):
    """Run a p4 command, printing what is executed. Raises on failure."""
    cmd = base_cmd + args
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    if result.returncode != 0:
        err = result.stderr.strip() if result.stderr else "unknown error"
        raise RuntimeError(f"[{label}] p4 command failed (exit {result.returncode}): {err}")
    return result.stdout


def reset_workspace(base_cmd, label):
    """Revert files, sync to #none, and delete pending CLs for a workspace."""
    print(f"\n--- Resetting {label} workspace ---")

    # Revert any open files
    try:
        run_p4(base_cmd, ["revert", "//..."], label)
    except RuntimeError as e:
        # "file(s) not opened" is not a real error
        if "not opened" in str(e):
            print(f"  (No open files to revert)")
        else:
            raise

    # Sync to nothing
    run_p4(base_cmd, ["sync", "//...#none"], label)

    # Delete empty pending changelists owned by this client
    output = run_p4(base_cmd, ["changes", "-s", "pending", "-c", base_cmd[base_cmd.index("-c") + 1]], label)
    for line in output.strip().splitlines():
        if line.startswith("Change "):
            change_num = line.split()[1]
            print(f"  Deleting pending changelist {change_num}")
            run_p4(base_cmd, ["change", "-d", change_num], label)


def clean_workspace_root(workspace_root):
    """Delete all contents under workspace_root."""
    print(f"\n--- Cleaning workspace root: {workspace_root} ---")
    if not os.path.isdir(workspace_root):
        print(f"  Directory does not exist, skipping: {workspace_root}")
        return
    for entry in os.listdir(workspace_root):
        entry_path = os.path.join(workspace_root, entry)
        if os.path.isdir(entry_path):
            print(f"  Removing directory: {entry_path}")
            shutil.rmtree(entry_path)
        else:
            print(f"  Removing file: {entry_path}")
            os.remove(entry_path)
    print("  Workspace root cleaned.")


def clean_intermediate_files(script_dir):
    """Delete *.log files in the script's directory."""
    print(f"\n--- Cleaning log files in: {script_dir} ---")
    log_files = glob.glob(os.path.join(script_dir, "*.log"))
    if not log_files:
        print("  No log files found.")
        return
    for log_file in log_files:
        print(f"  Removing: {log_file}")
        os.remove(log_file)
    print(f"  Removed {len(log_files)} log file(s).")

    print(f"\n--- Cleaning other files in: {script_dir} ---")
    files_to_clean = set()
    files_to_clean.add(os.path.join(script_dir, ".p4transfer_failed_files.json"))
    files_to_clean.add(os.path.join(script_dir, ".p4transfer_checkpoint.json"))
    for file in files_to_clean:
        if os.path.exists(file):
            print(f"  Removing: {file}")
            os.remove(file)

def main():
    parser = argparse.ArgumentParser(
        description="Reset P4Transfer workspaces, local files, and logs for a clean state."
    )
    parser.add_argument("-c", "--config", default="transfer.yaml",
                        help="Path to transfer config YAML file (default: transfer.yaml)")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip confirmation prompt")
    args = parser.parse_args()

    config = load_config(args.config)

    source = config.get("source", {})
    target = config.get("target", {})
    workspace_root = config.get("workspace_root", "")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("P4Transfer Workspace Reset")
    print("==========================")
    print(f"Config file:    {args.config}")
    print(f"Source server:  {source.get('p4port', 'N/A')} (client: {source.get('p4client', 'N/A')})")
    print(f"Target server:  {target.get('p4port', 'N/A')} (client: {target.get('p4client', 'N/A')})")
    print(f"Workspace root: {workspace_root or 'N/A'}")
    print(f"Log file dir:   {script_dir}")
    print()
    print("This will:")
    print("  1. Revert open files, sync to #none, and delete pending CLs on SOURCE workspace")
    print("  2. Revert open files, sync to #none, and delete pending CLs on TARGET workspace")
    print(f"  3. Delete all contents under: {workspace_root}")
    print(f"  4. Delete all *.log files in: {script_dir}")

    if not args.yes:
        print()
        if not confirm():
            print("Aborted.")
            sys.exit(0)

    # Reset source workspace
    source_cmd = build_p4_cmd(source)
    reset_workspace(source_cmd, "source")

    # Reset target workspace
    target_cmd = build_p4_cmd(target)
    reset_workspace(target_cmd, "target")

    # Clean local workspace files
    if workspace_root:
        clean_workspace_root(workspace_root)

    # Clean log files
    clean_intermediate_files(script_dir)


    print("\n=== Reset complete ===")


if __name__ == "__main__":
    main()
