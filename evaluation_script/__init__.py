"""
Vendor-friendly `__init__` for evaluation scripts.

Goal:
- Prefer packages that are included inside the repository under
  `evaluation_script/vendor/` so evaluation does NOT require network access
  or installs outside the repo.

Usage:
- To include a third-party package, add the package directory or a
  locally-downloaded wheel into `evaluation_script/vendor/`.
- Optionally create `evaluation_script/local_requirements.txt` with
  package names (one per line) to document which packages are expected.

Behavior:
- If `vendor/` exists it will be prepended to `sys.path` so imports
  like `from zhipuai import ZhipuAI` will resolve when `zhipuai` is
  present under `evaluation_script/vendor/`.
- If packages listed in `local_requirements.txt` are missing from the
  vendor folder, a warning is printed (no network install is attempted).

This approach ensures all code required for evaluation can live inside
the repo and avoids modifying the host Python environment.
"""

import sys
import importlib.util
from pathlib import Path

VENDOR_DIR = Path(__file__).parent / "vendor"

def add_vendor_to_sys_path():
    if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
        sys.path.insert(0, str(VENDOR_DIR))
        print(f"[evaluation_script] Added vendor directory to sys.path: {VENDOR_DIR}")
        return True
    return False

def is_importable(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None

def check_local_requirements():
    req_file = Path(__file__).parent / "local_requirements.txt"
    missing = []
    if req_file.exists():
        for line in req_file.read_text().splitlines():
            pkg = line.strip()
            if not pkg or pkg.startswith("#"):
                continue
            # only check module base name (before any ==)
            mod_name = pkg.split("==")[0].strip()
            if not is_importable(mod_name):
                missing.append(pkg)
    return missing

# Add vendor path early so downstream imports can find vendored packages.
add_vendor_to_sys_path()

missing = check_local_requirements()
if missing:
    print("[evaluation_script] Warning: The following packages listed in local_requirements.txt were not found in evaluation_script/vendor/:\n  " + "\n  ".join(missing))
    print("[evaluation_script] To avoid network installs, place package directories or wheels into evaluation_script/vendor/")

from .main import evaluate
