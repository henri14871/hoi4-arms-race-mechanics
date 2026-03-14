#!/usr/bin/env python3
"""
One-command rebuild for ARM's bundled major-mod compatibility profiles.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent


def run_step(args: list[str]) -> None:
    completed = subprocess.run([sys.executable, *args], cwd=TOOLS_DIR.parent)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    run_step(["Tools/manage_compat_profiles.py", "rebuild"])
    print("Rebuilt bundled major-mod compatibility profiles.")


if __name__ == "__main__":
    main()
