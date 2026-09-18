#!/usr/bin/env bash
# Freeze Satisfactory Shell and write dist/satisfactory-shell-<ver>-linux-x64.tar.gz
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "pack-linux.sh must run on Linux (PyInstaller does not cross-compile)." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v poetry >/dev/null 2>&1; then
  echo "poetry not found. Install Poetry, then: poetry install --with dev" >&2
  exit 1
fi

VERSION="$(poetry version -s)"
poetry run build-exe

STAGE="$ROOT/dist/linux-pack"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp "$ROOT/dist/satisfactory-shell" "$STAGE/satisfactory-shell"
chmod +x "$STAGE/satisfactory-shell"
cp -R "$ROOT/dist/webui" "$STAGE/webui"
cp "$ROOT/packaging/linux/satisfactory-shell.service" "$STAGE/satisfactory-shell.service"
cp "$ROOT/scripts/install.sh" "$STAGE/install.sh"
chmod +x "$STAGE/install.sh"

TARBALL="$ROOT/dist/satisfactory-shell-${VERSION}-linux-x64.tar.gz"
tar -C "$STAGE" -czf "$TARBALL" \
  satisfactory-shell \
  webui \
  satisfactory-shell.service \
  install.sh

echo "Wrote $TARBALL"
