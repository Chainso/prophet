#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    src_root = root / "src"
    generated_src = root / "gen" / "python" / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    if str(generated_src) not in sys.path:
        sys.path.insert(0, str(generated_src))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prophet_example_django.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
