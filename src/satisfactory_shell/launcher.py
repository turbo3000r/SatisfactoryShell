"""PyInstaller entry script (absolute import so the package machinery works when frozen)."""

import sys

from satisfactory_shell.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
