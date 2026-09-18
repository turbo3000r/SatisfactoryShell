#!/usr/bin/env bash
# Install Satisfactory Shell to /opt and enable a systemd unit.
# Does not download SteamCMD or the dedicated server.
set -euo pipefail

REPO="${GITHUB_REPO:-turbo3000r/SatisfactoryShell}"
PREFIX="${INSTALL_PREFIX:-/opt/satisfactory-shell}"
UNIT_NAME="satisfactory-shell.service"
UNIT_DST="/etc/systemd/system/${UNIT_NAME}"

usage() {
  cat <<'EOF'
Install Satisfactory Shell (the WebUI / process manager only).

Usage:
  sudo ./install.sh [tarball]
  curl -fsSL https://github.com/turbo3000r/SatisfactoryShell/releases/latest/download/install.sh | sudo bash

If no tarball is given, the latest GitHub Release linux-x64 archive is downloaded.

Override the install path with INSTALL_PREFIX (default /opt/satisfactory-shell).
The systemd unit WorkingDirectory and ExecStart are rewritten to match.

After install, set paths.server_root and paths.steamcmd in
~/.config/satisfactory-shell/config.json (created on first start) so they
point at an existing Linux dedicated server and SteamCMD.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "install.sh must run as root (sudo)." >&2
  exit 1
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "install.sh is for Linux." >&2
  exit 1
fi

RUN_USER="${SUDO_USER:-}"
if [[ -z "$RUN_USER" || "$RUN_USER" == "root" ]]; then
  echo "Set SUDO_USER to the account that should own the service (sudo ./install.sh)." >&2
  exit 1
fi
RUN_GROUP="$(id -gn "$RUN_USER")"

WORKDIR="$(mktemp -d)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

TARBALL="${1:-}"
if [[ -n "$TARBALL" ]]; then
  if [[ ! -f "$TARBALL" ]]; then
    echo "Tarball not found: $TARBALL" >&2
    exit 1
  fi
  cp "$TARBALL" "$WORKDIR/pack.tar.gz"
else
  API="https://api.github.com/repos/${REPO}/releases/latest"
  echo "Fetching latest release asset from ${REPO}…"
  JSON="$(curl -fsSL "$API")"
  URL="$(printf '%s\n' "$JSON" | sed -n 's/.*"browser_download_url": "\([^"]*linux-x64\.tar\.gz\)".*/\1/p' | head -n 1)"
  if [[ -z "$URL" ]]; then
    echo "Could not find a linux-x64.tar.gz asset on the latest GitHub Release." >&2
    exit 1
  fi
  curl -fL --progress-bar -o "$WORKDIR/pack.tar.gz" "$URL"
fi

tar -xzf "$WORKDIR/pack.tar.gz" -C "$WORKDIR"

UNIT_SRC="$WORKDIR/satisfactory-shell.service"
if [[ ! -f "$WORKDIR/satisfactory-shell" ]]; then
  echo "Archive is missing the satisfactory-shell binary." >&2
  exit 1
fi
if [[ ! -d "$WORKDIR/webui" ]]; then
  echo "Archive is missing the webui/ folder." >&2
  exit 1
fi
if [[ ! -f "$UNIT_SRC" ]]; then
  echo "Archive is missing satisfactory-shell.service." >&2
  exit 1
fi

if systemctl is-active --quiet "$UNIT_NAME"; then
  echo "Stopping ${UNIT_NAME}…"
  systemctl stop "$UNIT_NAME"
fi

echo "Installing to ${PREFIX}"
rm -rf "$PREFIX"
mkdir -p "$PREFIX"
cp "$WORKDIR/satisfactory-shell" "$PREFIX/satisfactory-shell"
chmod +x "$PREFIX/satisfactory-shell"
cp -R "$WORKDIR/webui" "$PREFIX/webui"

sed -e "s|__USER__|${RUN_USER}|g" \
    -e "s|__GROUP__|${RUN_GROUP}|g" \
    -e "s|__PREFIX__|${PREFIX}|g" \
    "$UNIT_SRC" > "$UNIT_DST"
chmod 644 "$UNIT_DST"

systemctl daemon-reload
systemctl enable --now "$UNIT_NAME"

echo
echo "Satisfactory Shell is installed and the systemd unit is enabled."
echo "WebUI: http://127.0.0.1:8080"
echo "Config (created on first start): /home/${RUN_USER}/.config/satisfactory-shell/config.json"
echo "Set paths.server_root and paths.steamcmd there if they are empty."
