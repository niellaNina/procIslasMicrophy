# utils/config.py
from pathlib import Path
import os
import yaml

ROOT = Path(__file__).resolve().parent.parent  # points to postprocessing/

# Location of the YAML config file
_CONFIG_PATH = ROOT / "config.yaml"

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _env_or_cfg(env_name: str, cfg_value, base: Path = None) -> Path:
    """
    If env var exists, use it; otherwise use cfg_value.
    If result is a relative path, make it relative to ROOT (or provided base).
    Returns a resolved Path.
    """
    val = os.environ.get(env_name)
    if val:
        p = Path(val)
    else:
        p = Path(cfg_value) if cfg_value is not None else None

    if p is None:
        return None

    # Expand user (~) and make absolute relative to base or ROOT
    p = p.expanduser()
    if not p.is_absolute():
        anchor = base if base is not None else ROOT
        p = (anchor / p)
    return p.resolve()

# Load YAML once on import
_cfg = _load_yaml(_CONFIG_PATH)

DATA_DIR = _env_or_cfg("POSTPROC_DATA_DIR", _cfg.get("data_dir"))
SAVE_DIR = _env_or_cfg("POSTPROC_SAVE_DIR", _cfg.get("save_dir"))
LOG_DIR  = _env_or_cfg("POSTPROC_LOG_DIR", _cfg.get("log_dir"))

# Create directories intended for writing
for d in (SAVE_DIR, LOG_DIR):
    if d is not None:
        d.mkdir(parents=True, exist_ok=True)

# Expose other non-path settings
SAMPLE_RATE = _cfg.get("sample_rate")
USE_CACHE = bool(_cfg.get("use_cache", False))

# Optionally expose the raw config and root
RAW_CONFIG = _cfg
ROOT_DIR = ROOT
