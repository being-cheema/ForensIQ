"""ForensIQ E01 to Raw Image Converter

Converts Expert Witness Format (.E01 / .Exx) disk image containers
into consolidated raw dd (.raw / .dd) disk images with integrity hashing.
"""
import argparse
import os
import shutil
import sys
import time
import hashlib
from pathlib import Path

try:
    import pyewf
except ImportError:
    pyewf = None

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.table import Table

console = Console()


def get_free_space_gb(path):
    """Return free disk space in GB for the drive containing path."""
    try:
        drive = os.path.splitdrive(os.path.abspath(path))[0]
        usage = shutil.disk_usage(drive if drive else ".")
        return usage.free / (1024 ** 3)
    except Exception:
        return 999.0


def convert_e01_to_raw(image_path, output_path=None, chunk_size_mb=32, force=False):
    """Stream-converts multi-segment E01 images into a raw .dd/.raw image file."""
    if pyewf is None:
        console.print("[bold red][!] pyewf is required for E01 conversion but is not installed.[/bold red]")
        console.print("    To install: [bold cyan]pip install libewf-python[/bold cyan] or use pre-converted raw images (.dd / .raw).")
        return None

    image_path = os.path.abspath(image_path)
    if os.path.isdir(image_path):
        candidates = sorted(Path(image_path).glob("*.[eE]01"))
        if not candidates:
            console.print(f"[bold red][!] No .E01 files found in directory:[/bold red] {image_path}")
            return None
        image_path = str(candidates[0])

    if not os.path.exists(image_path):
        console.print(f"[bold red][!] File not found:[/bold red] {image_path}")
        return None

    # Resolve all segment filenames
    try:
        filenames = pyewf.glob(image_path)
    except Exception:
        filenames = [image_path]

    if not filenames:
        filenames = [image_path]

    # Derive default output path if none given
    if not output_path:
        stem = Path(filenames[0]).stem
        output_path = os.path.join(os.path.dirname(filenames[0]), f"{stem}_raw.dd")
    output_path = os.path.abspath(output_path)

    ewf_handle = pyewf.handle()
    ewf_handle.open(filenames)
    media_size = ewf_handle.get_media_size()
    media_size_gb = media_size / (1024 ** 3)

    # Check disk space
    free_gb = get_free_space_gb(output_path)
    table = Table(title="E01 -> Raw Conversion Parameters", box=None)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Primary Segment", os.path.basename(filenames[0]))
    table.add_row("Total Segments", str(len(filenames)))
    table.add_row("Virtual Media Size", f"{media_size_gb:.2f} GB ({media_size:,} bytes)")
    table.add_row("Destination", output_path)
    table.add_row("Available Disk Space", f"{free_gb:.2f} GB")
    console.print(Panel(table, title="[bold blue]ForensIQ EWF Imager[/bold blue]", border_style="blue"))

    if free_gb < (media_size_gb + 1.0) and not force:
        console.print(
            f"[bold red][!] Insufficient disk space on target drive![/bold red]\n"
            f"    Virtual size: [bold yellow]{media_size_gb:.2f} GB[/bold yellow]\n"
            f"    Free space  : [bold yellow]{free_gb:.2f} GB[/bold yellow]\n"
            f"    A raw image must expand all uncompressed sectors. To force conversion anyway, use [bold cyan]--force[/bold cyan].\n"
            f"    [bold green][i] Tip: ForensIQ can mount and parse E01 images directly without converting if disk space is limited.[/bold green]"
        )
        ewf_handle.close()
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    chunk_size = chunk_size_mb * 1024 * 1024
    bytes_written = 0
    start_time = time.time()
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Converting E01 -> Raw...", total=media_size)
        with open(output_path, "wb") as out_f:
            while bytes_written < media_size:
                to_read = min(chunk_size, media_size - bytes_written)
                data = ewf_handle.read(to_read)
                if not data:
                    break
                out_f.write(data)
                sha256.update(data)
                md5.update(data)
                bytes_written += len(data)
                progress.update(task, completed=bytes_written)

    ewf_handle.close()
    elapsed = max(time.time() - start_time, 0.1)
    rate_mb = (bytes_written / (1024 ** 2)) / elapsed

    res_table = Table(title="Conversion Complete", box=None)
    res_table.add_column("Item", style="cyan")
    res_table.add_column("Result", style="green")
    res_table.add_row("Output File", output_path)
    res_table.add_row("Bytes Written", f"{bytes_written:,} bytes ({bytes_written / (1024**3):.2f} GB)")
    res_table.add_row("Throughput", f"{rate_mb:.2f} MB/s")
    res_table.add_row("MD5", md5.hexdigest())
    res_table.add_row("SHA-256", sha256.hexdigest())
    console.print(Panel(res_table, title="[bold green]Conversion Success[/bold green]", border_style="green"))

    # Save hash sidecar
    hash_file = f"{output_path}.sha256"
    with open(hash_file, "w") as hf:
        hf.write(f"{sha256.hexdigest()}  {os.path.basename(output_path)}\n")
        hf.write(f"{md5.hexdigest()}  {os.path.basename(output_path)} (MD5)\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert E01 disk images to raw (.dd / .raw) image files.")
    parser.add_argument("--image", "-i", required=True, help="Path to primary .E01 file or image directory")
    parser.add_argument("--output", "-o", default=None, help="Path to output raw image (.dd)")
    parser.add_argument("--chunk-size", "-c", type=int, default=32, help="Chunk size in MB (default: 32)")
    parser.add_argument("--force", "-f", action="store_true", help="Force conversion even if free space check fails")
    args = parser.parse_args()

    result = convert_e01_to_raw(args.image, args.output, args.chunk_size, args.force)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
