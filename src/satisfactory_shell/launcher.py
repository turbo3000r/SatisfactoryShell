"""PyInstaller entry script (absolute import so the package machinery works when frozen)."""

# Redirects must happen before importing the package; handles stay open for process life.
# pylint: disable=wrong-import-position,consider-using-with

import os
import sys

# When frozen with --noconsole/--windowed on Windows, stdout/stderr are None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

from satisfactory_shell.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
