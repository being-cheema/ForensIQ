import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_PATH = os.path.join(BASE_DIR, "images/SCHARDT.001")
PART_OFFSET = 63  # sectors — match your mmls output
SECTOR_SIZE = 512
OUT_DIR = os.path.join(BASE_DIR, "artifacts")
FEAT_DIR = os.path.join(BASE_DIR, "features")
MODEL_DIR = os.path.join(BASE_DIR, "models")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
CONTAMINATION = 0.05  # expected anomaly fraction
