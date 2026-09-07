
#!/usr/bin/env python3
"""
ForensIQ Analysis Pipeline Runner
=================================
Orchestrates and executes all analysis steps sequentially, passing outputs
along the chain, from raw disk extraction to final HTML dashboard.
"""

import os
import sys
import time
import argparse
import subprocess
# pyrefly: ignore [missing-import]
from rich.console import Console
# pyrefly: ignore [missing-import]
from rich.table import Table
# pyrefly: ignore [missing-import]
from rich.panel import Panel

# Initialize rich console for premium styling
console = Console()

STEPS = [
    ("extractor.py", "Data Extraction", "Extract raw files, EVT log files, registry hives, and prefetch from disk."),
    ("chain_of_custody.py", "Chain of Custody", "Compute SHA-256 hashes of all raw extracted artifacts."),
    ("feature_eng2.py", "Feature Engineering", "Generate 17-feature matrix and file index from MFT and logs."),
    ("anomaly_detection.py", "ML Anomaly Detection (v1)", "Train Isolation Forest model & output flagged anomalies."),
    ("burst_detection.py", "Burst Detection (v2)", "Perform MFT temporal burst analysis & train Isolation Forest v2."),
    ("confidence_tiers.py", "Confidence Calibration", "Rank flagged anomalies into CRITICAL/HIGH/MEDIUM/LOW tiers."),
    ("mitre_mapper.py", "MITRE ATT&CK Mapping", "Map anomaly signatures to adversary tactics & Navigator layer."),
    ("xai_shap.py", "Explainable AI (SHAP)", "Compute SHAP attribution values & waterfall/beeswarm plots."),
    ("timeline.py", "Timeline Generation", "Construct sorted events CSV and interactive HTML timeline."),
    ("remediation.py", "Remediation Scripts", "Generate PowerShell containment files for detected breach indicators."),
    ("forensiq_report.py", "HTML Report Assembly", "Validate CoC, compile findings, and generate premium HTML dashboard."),
]

def run_step(script_name, description, base_dir):
    script_path = os.path.join(base_dir, script_name)
    if not os.path.exists(script_path):
        console.print(f"[bold red][!][/bold red] Script not found: [yellow]{script_path}[/yellow]")
        return False, 0.0

    console.print(Panel(
        f"[bold cyan]Executing Step:[/bold cyan] [green]{script_name}[/green]\n[dim]{description}[/dim]",
        border_style="blue"
    ))

    start_time = time.time()
    try:
        # Run step using the same Python interpreter
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=base_dir,
            text=True,
            capture_output=False  # Print directly to terminal for live progress
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            console.print(f"[bold green][✓][/bold green] Step [green]{script_name}[/green] completed successfully in {elapsed:.2f}s.\n")
            return True, elapsed
        else:
            console.print(f"[bold red][✗][/bold red] Step [red]{script_name}[/red] failed with exit code {result.returncode}.\n")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        console.print(f"[bold red][✗][/bold red] Step [red]{script_name}[/red] crashed: {e}\n")
        return False, elapsed

def main():
    parser = argparse.ArgumentParser(description="Orchestrates the ForensIQ analysis pipeline from end to end.")
    parser.add_argument("--skip-extraction", action="store_true", help="Skip extractor and chain of custody generation.")
    parser.add_argument("--start-at", type=str, help="Script filename to start execution from (e.g. anomaly_detection.py).")
    parser.add_argument("--list-steps", action="store_true", help="List all the pipeline steps and description then exit.")
    
    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if args.list_steps:
        table = Table(title="ForensIQ Pipeline Steps")
        table.add_column("Index", style="cyan", no_wrap=True)
        table.add_column("Script Name", style="green")
        table.add_column("Stage Title", style="bold")
        table.add_column("Description", style="dim")
        for idx, (name, title, desc) in enumerate(STEPS, 1):
            table.add_row(str(idx), name, title, desc)
        console.print(table)
        sys.exit(0)

    # Determine start step index
    start_idx = 0
    if args.skip_extraction:
        # Skip steps 1 and 2 (indices 0 and 1)
        start_idx = 2
        console.print("[bold yellow][!][/bold yellow] Skipping extraction steps (extractor.py, chain_of_custody.py)...")
    
    if args.start_at:
        found = False
        for idx, (name, _, _) in enumerate(STEPS):
            if name.lower() == args.start_at.lower():
                start_idx = idx
                found = True
                console.print(f"[bold yellow][!][/bold yellow] Starting pipeline from step: [green]{name}[/green]")
                break
        if not found:
            console.print(f"[bold red][!][/bold red] Unknown step name: [yellow]{args.start_at}[/yellow]")
            sys.exit(1)

    console.print(Panel.fit(
        "[bold white]ForensIQ Analysis Pipeline Runner[/bold white]\n[dim]Windows XP (SCHARDT.001) Forensic Analysis[/dim]",
        border_style="bold magenta"
    ))

    run_steps = STEPS[start_idx:]
    results = []
    failed = False

    for name, title, desc in run_steps:
        success, elapsed = run_step(name, desc, base_dir)
        results.append((name, title, success, elapsed))
        if not success:
            failed = True
            console.print("[bold red][!][/bold red] Pipeline aborted due to step failure.")
            break

    # Summary
    table = Table(title="Pipeline Execution Summary", border_style="magenta")
    table.add_column("Script", style="green")
    table.add_column("Stage", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Time (s)", justify="right", style="cyan")

    total_time = 0.0
    for name, title, success, elapsed in results:
        status_str = "[bold green]PASS[/bold green]" if success else "[bold red]FAIL[/bold red]"
        table.add_row(name, title, status_str, f"{elapsed:.2f}")
        total_time += elapsed

    console.print(table)
    console.print(f"[bold white]Total Execution Time:[/bold white] [cyan]{total_time:.2f}s[/cyan]\n")

    if failed:
        sys.exit(1)
    else:
        console.print("[bold green][✓] Pipeline execution finished successfully![/bold green]")
        sys.exit(0)

if __name__ == "__main__":
    main()
