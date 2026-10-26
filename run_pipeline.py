#!/usr/bin/env python3
"""
run_pipeline.py
===============
ForensIQ Automated Forensic Analysis Pipeline Runner
Orchestrates and executes all analysis steps sequentially, passing outputs
along the chain, from raw disk extraction to final HTML intelligence dashboards.
Supports modern Windows 7/10 (NIST CFReDS, Lone Wolf) and legacy Windows XP datasets.
"""

import os
import sys
import time
import argparse
import subprocess

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAVE_RICH = True
    console = Console()
except ImportError:
    HAVE_RICH = False
    console = None

from config import validate_config, IMAGE_PATH

STEPS = [
    ("extractor.py", "Data Extraction", "Extract raw files, EVT/EVTX logs, registry hives, and prefetch from disk."),
    ("chain_of_custody.py", "Chain of Custody", "Compute SHA-256 hashes of all raw extracted artifacts."),
    ("feature_engineering.py", "Feature Engineering", "Generate 17-feature matrix and file index from MFT and logs."),
    ("anomaly_detection.py", "ML Anomaly Detection (v1)", "Train Isolation Forest model & output flagged anomalies."),
    ("burst_detection.py", "Burst Detection (v2)", "Perform MFT temporal burst analysis & train Isolation Forest v2."),
    ("confidence_tiers.py", "Confidence Calibration", "Rank flagged anomalies into CRITICAL/HIGH/MEDIUM/LOW tiers."),
    ("mitre_mapper.py", "MITRE ATT&CK Mapping", "Map anomaly signatures to adversary tactics & Navigator layer."),
    ("xai_shap.py", "Explainable AI (SHAP)", "Compute SHAP attribution values & waterfall/beeswarm plots."),
    ("timeline.py", "Timeline Generation", "Construct sorted events CSV and interactive HTML timeline."),
    ("remediation.py", "Remediation Scripts", "Generate PowerShell containment files for detected breach indicators."),
    ("forensiq_report.py", "HTML Report Assembly", "Validate CoC, compile findings, and generate premium HTML dashboard."),
    ("evaluate_baselines.py", "Baseline Benchmark", "Evaluate equal-budget retrieval against rules, k-NN, and ablations."),
]


def log_panel(title, content, border_style="blue"):
    if HAVE_RICH:
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]\n[dim]{content}[/dim]", border_style=border_style))
    else:
        print(f"\n{'='*60}\n{title}\n{content}\n{'='*60}")


def run_step(script_name, description, base_dir, env_overrides=None):
    script_path = os.path.join(base_dir, script_name)
    if not os.path.exists(script_path):
        err_msg = f"[!] Script not found: {script_path}"
        if HAVE_RICH:
            console.print(f"[bold red]{err_msg}[/bold red]")
        else:
            print(err_msg)
        return False, 0.0

    log_panel(f"Executing: {script_name}", description, border_style="blue")

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=base_dir,
            env=env,
            text=True,
            capture_output=False
        )
        elapsed = time.time() - start_time

        if result.returncode == 0:
            if HAVE_RICH:
                console.print(f"[bold green][OK][/bold green] Step [green]{script_name}[/green] completed in {elapsed:.2f}s.\n")
            else:
                print(f"[+] Step {script_name} completed in {elapsed:.2f}s.\n")
            return True, elapsed
        else:
            if HAVE_RICH:
                console.print(f"[bold red][FAIL][/bold red] Step [red]{script_name}[/red] failed with exit code {result.returncode}.\n")
            else:
                print(f"[!] Step {script_name} failed with exit code {result.returncode}.\n")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        if HAVE_RICH:
            console.print(f"[bold red][✗][/bold red] Step [red]{script_name}[/red] crashed: {e}\n")
        else:
            print(f"[✗] Step {script_name} crashed: {e}\n")
        return False, elapsed


def main():
    parser = argparse.ArgumentParser(description="Orchestrates the ForensIQ forensic analysis pipeline end-to-end.")
    parser.add_argument("--image", "-i", type=str, help="Path to raw/dd target image file.")
    parser.add_argument("--offset", "-o", type=str, help="Partition sector offset (e.g. 63, 206848, 1259520, or auto).")
    parser.add_argument("--contamination", "-c", type=str, help="Contamination rate for Isolation Forest (default: 0.05).")
    parser.add_argument("--skip-extraction", action="store_true", help="Skip extractor and chain of custody generation.")
    parser.add_argument("--start-at", type=str, help="Script filename to start from (e.g. anomaly_detection.py).")
    parser.add_argument("--list-steps", action="store_true", help="List all pipeline steps and exit.")

    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if args.list_steps:
        if HAVE_RICH:
            table = Table(title="ForensIQ Pipeline Analysis Stages")
            table.add_column("Index", style="cyan", no_wrap=True)
            table.add_column("Script Name", style="green")
            table.add_column("Stage Title", style="bold")
            table.add_column("Description", style="dim")
            for idx, (name, title, desc) in enumerate(STEPS, 1):
                table.add_row(str(idx), name, title, desc)
            console.print(table)
        else:
            print("ForensIQ Pipeline Steps:")
            for idx, (name, title, desc) in enumerate(STEPS, 1):
                print(f" {idx:2d}. {name:<22} - {title}: {desc}")
        sys.exit(0)

    # Set up environment overrides from CLI flags
    env_overrides = {}
    if args.image:
        resolved_img = os.path.abspath(args.image)
        env_overrides["FORENSIQ_IMAGE_PATH"] = resolved_img
        os.environ["FORENSIQ_IMAGE_PATH"] = resolved_img
    if args.offset:
        env_overrides["FORENSIQ_PART_OFFSET"] = str(args.offset)
        os.environ["FORENSIQ_PART_OFFSET"] = str(args.offset)
    if args.contamination:
        env_overrides["FORENSIQ_CONTAMINATION"] = str(args.contamination)
        os.environ["FORENSIQ_CONTAMINATION"] = str(args.contamination)

    start_idx = 0
    if args.skip_extraction:
        start_idx = 2
        print("[!] Skipping extraction steps (extractor.py, chain_of_custody.py)...")
    elif args.start_at:
        found = False
        for idx, (name, _, _) in enumerate(STEPS):
            if name.lower() == args.start_at.lower():
                start_idx = idx
                found = True
                print(f"[!] Starting pipeline from step: {name}")
                break
        if not found:
            print(f"[!] Unknown start step name: {args.start_at}")
            sys.exit(1)

    target_img = os.environ.get("FORENSIQ_IMAGE_PATH", IMAGE_PATH)
    header_info = f"Target Image: {target_img}\nOffset: {os.environ.get('FORENSIQ_PART_OFFSET', 'auto-detect')}"
    log_panel("ForensIQ Unified Forensic Intelligence Pipeline", header_info, border_style="bold magenta")

    # If extraction is to be run, validate image existence
    if start_idx < 2 and not validate_config(target_img):
        print(f"[!] Target image '{target_img}' is missing. If you have extracted artifacts, use --skip-extraction.")
        sys.exit(1)

    run_steps = STEPS[start_idx:]
    results = []
    failed = False

    for name, title, desc in run_steps:
        success, elapsed = run_step(name, desc, base_dir, env_overrides=env_overrides)
        results.append((name, title, success, elapsed))
        if not success:
            failed = True
            print("[!] Pipeline aborted due to step failure.")
            break

    # Summary
    total_time = sum(el for _, _, _, el in results)
    if HAVE_RICH:
        table = Table(title="Pipeline Execution Summary", border_style="magenta")
        table.add_column("Script", style="green")
        table.add_column("Stage", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Time (s)", justify="right", style="cyan")
        for name, title, success, elapsed in results:
            status_str = "[bold green]PASS[/bold green]" if success else "[bold red]FAIL[/bold red]"
            table.add_row(name, title, status_str, f"{elapsed:.2f}")
        console.print(table)
        console.print(f"[bold white]Total Execution Time:[/bold white] [cyan]{total_time:.2f}s[/cyan]\n")
    else:
        print("\nPipeline Execution Summary:")
        for name, title, success, elapsed in results:
            status_str = "PASS" if success else "FAIL"
            print(f" - {name:<24} [{status_str}] ({elapsed:.2f}s)")
        print(f"Total Execution Time: {total_time:.2f}s\n")

    if failed:
        sys.exit(1)
    else:
        print("[+] ForensIQ pipeline execution finished successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
