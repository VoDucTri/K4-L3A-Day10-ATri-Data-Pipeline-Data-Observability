from __future__ import annotations

import sys
from pathlib import Path

# Configure utf-8 encoding on Windows to prevent UnicodeEncodeError on special folder paths
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure src/ is in sys.path
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from pipelines.phase1 import main


if __name__ == "__main__":
    main()

