import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _find_default_image():
    if "FORENSIQ_IMAGE_PATH" in os.environ and os.path.exists(os.environ["FORENSIQ_IMAGE_PATH"]):
        return os.environ["FORENSIQ_IMAGE_PATH"]
    candidates = [
        os.path.join(BASE_DIR, "Lone Wolf", "LoneWolf.E01"),
        os.path.join(BASE_DIR, "Lone Wolf"),
        os.path.join(BASE_DIR, "images", "dataleak", "cfreds_2015_data_leakage_pc.dd"),
        os.path.join(BASE_DIR, "images", "SCHARDT.001"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

DEFAULT_IMAGE_PATH = _find_default_image()
IMAGE_PATH = os.environ.get("FORENSIQ_IMAGE_PATH", DEFAULT_IMAGE_PATH)

# Partition offset in 512-byte sectors
_raw_offset = os.environ.get("FORENSIQ_PART_OFFSET", "206848")
try:
    PART_OFFSET = int(_raw_offset)
except ValueError:
    PART_OFFSET = 0

SECTOR_SIZE = int(os.environ.get("FORENSIQ_SECTOR_SIZE", "512"))

# Output and pipeline directories
OUT_DIR = os.environ.get("FORENSIQ_OUT_DIR", os.path.join(BASE_DIR, "artifacts"))
FEAT_DIR = os.environ.get("FORENSIQ_FEAT_DIR", os.path.join(BASE_DIR, "features"))
MODEL_DIR = os.environ.get("FORENSIQ_MODEL_DIR", os.path.join(BASE_DIR, "models"))
REPORT_DIR = os.environ.get("FORENSIQ_REPORT_DIR", os.path.join(BASE_DIR, "reports"))

# Isolation Forest anomaly contamination rate
CONTAMINATION = float(os.environ.get("FORENSIQ_CONTAMINATION", "0.05"))

# Policy work-hour thresholds (for insider threat & data leakage detection)
# Default standard: 08:00 - 18:00
# NIST CFReDS Company OOO policy: 10:00 - 16:00
WORK_HOURS_START = int(os.environ.get("FORENSIQ_WORK_HOURS_START", "8"))
WORK_HOURS_END = int(os.environ.get("FORENSIQ_WORK_HOURS_END", "18"))


def validate_config(image_path=None):
    """
    Validates that the target disk image exists or provides instructions.
    """
    target = image_path or IMAGE_PATH
    if not os.path.exists(target):
        print(f"[!] Warning: Disk image not found at '{target}'")
        print("    Set FORENSIQ_IMAGE_PATH or place your disk image in images/")
        print("    Example: set FORENSIQ_IMAGE_PATH=D:\\Datasets\\data_leakage_pc.raw")
        return False
    return True
