#!/usr/bin/env bash
# MacTahoe extras: fill the gaps in the MacTahoe icon theme so every visible launcher gets a
# macOS-style icon. build.py symlinks launchers to MacTahoe artwork that is the app's real
# icon, and generates MacTahoe-style tiles from the original art for the rest, into
# apps/scalable of MacTahoe, MacTahoe-dark and MacTahoe-light. Upstream files are never
# overwritten; installed files are tracked in ~/.local/state/mactahoe-extras/manifest.json.
# Launchers and the active icon theme are left alone.
#
#   ./apply.sh                 build + install
#   ./apply.sh --watch         same, quietly (used by the systemd watcher)
#   ./apply.sh --install-watcher | --remove-watcher
#   ./apply.sh --revert        remove everything it installed, and the watcher
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
units="$HOME/.config/systemd/user"
icons="$HOME/.local/share/icons"

install_watcher() {
  mkdir -p "$units"
  cat > "$units/mactahoe-extras.path" <<EOF
[Unit]
Description=Rebuild MacTahoe extra icons when apps are installed or removed

[Path]
PathChanged=%h/.local/share/applications
PathChanged=/usr/share/applications
PathChanged=/var/lib/flatpak/exports/share/applications
PathChanged=%h/.local/share/flatpak/exports/share/applications
Unit=mactahoe-extras.service

[Install]
WantedBy=default.target
EOF
  cat > "$units/mactahoe-extras.service" <<EOF
[Unit]
Description=Rebuild MacTahoe extra icons

[Service]
Type=oneshot
# Let package managers (and the Nothing Dots watcher) finish writing before scanning.
ExecStartPre=/usr/bin/sleep 10
ExecStart=$here/apply.sh --watch
Nice=10
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now mactahoe-extras.path
}

remove_watcher() {
  systemctl --user disable --now mactahoe-extras.path 2>/dev/null || true
  rm -f "$units/mactahoe-extras.path" "$units/mactahoe-extras.service"
  systemctl --user daemon-reload
}

update_caches() {
  # MacTahoe ships an icon-theme.cache; new files stay invisible until it is rebuilt.
  for t in MacTahoe MacTahoe-dark MacTahoe-light; do
    [[ -f "$icons/$t/index.theme" ]] && gtk-update-icon-cache -f -t -q "$icons/$t" || true
  done
}

case "${1:-}" in
  --install-watcher) install_watcher; exit 0 ;;
  --remove-watcher) remove_watcher; exit 0 ;;
  --revert)
    remove_watcher
    python3 "$here/build.py" --revert
    update_caches
    exit 0 ;;
esac

python3 "$here/build.py"
update_caches

[[ "${1:-}" != "--watch" ]] && echo "MacTahoe extras applied." || true
