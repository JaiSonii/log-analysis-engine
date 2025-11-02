import logging
import os
import sys
from datetime import datetime

# --- CONFIGURABLE PARAMETERS ---
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE_NAME = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

# --- Ensure log directory exists ---
os.makedirs(LOG_DIR, exist_ok=True)

# --- Create the global logger ---
logger = logging.getLogger("IntelligentPythonAgent")
logger.setLevel(logging.INFO)

# --- Avoid duplicate handlers when re-imported ---
if not logger.handlers:

    # --- Formatter ---
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # --- File Handler ---
    try:
        file_handler = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except (IOError, PermissionError) as e:
        sys.stderr.write(f"[LOGGER] Failed to write to file: {e}\n")

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    logger.info(f"✅ Logger initialized. Writing logs to: {LOG_PATH}")
