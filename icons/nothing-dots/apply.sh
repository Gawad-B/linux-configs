#!/usr/bin/env bash
# Build + install Nothing Dots. build.py also gives every launcher without a hand-drawn
# glyph an automatic one, and repoints user launchers that use absolute icon paths.
#
#   ./apply.sh             build, install, switch to the theme
#   ./apply.sh --watch     build only (used by the systemd watcher; leaves your theme choice alone)
#   ./apply.sh --install-watcher | --remove-watcher
#   ./apply.sh --revert    restore original launchers + previous theme, remove watcher
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
apps="$HOME/.local/share/applications"
backup="$here/desktop-backup"
units="$HOME/.config/systemd/user"

install_watcher() {
  mkdir -p "$units"
  cat > "$units/nothing-dots.path" <<EOF
[Unit]
Description=Rebuild Nothing Dots icons when apps are installed or removed

[Path]
PathChanged=%h/.local/share/applications
PathChanged=/usr/share/applications
PathChanged=/var/lib/flatpak/exports/share/applications
PathChanged=%h/.local/share/flatpak/exports/share/applications
Unit=nothing-dots.service

[Install]
WantedBy=default.target
EOF
  cat > "$units/nothing-dots.service" <<EOF
[Unit]
Description=Rebuild Nothing Dots icons

[Service]
Type=oneshot
# Let package managers finish writing before scanning.
ExecStartPre=/usr/bin/sleep 5
ExecStart=$here/apply.sh --watch
Nice=10
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now nothing-dots.path
}

remove_watcher() {
  systemctl --user disable --now nothing-dots.path 2>/dev/null || true
  rm -f "$units/nothing-dots.path" "$units/nothing-dots.service"
  systemctl --user daemon-reload
}

case "${1:-}" in
  --install-watcher) install_watcher; exit 0 ;;
  --remove-watcher) remove_watcher; exit 0 ;;
  --revert)
    remove_watcher
    [[ -d "$backup" ]] && cp -v "$backup"/*.desktop "$apps"/
    gsettings set org.gnome.desktop.interface icon-theme "$(cat "$backup/previous-theme" 2>/dev/null || echo Adwaita)"
    exit 0 ;;
esac

mkdir -p "$backup"
current="$(gsettings get org.gnome.desktop.interface icon-theme | tr -d "'")"
[[ "$current" != "Nothing-Dots" && ! -f "$backup/previous-theme" ]] && echo "$current" > "$backup/previous-theme"

python3 "$here/build.py" "$HOME/.local/share/icons/Nothing-Dots"
gtk-update-icon-cache -f -q "$HOME/.local/share/icons/Nothing-Dots" || true

if [[ "${1:-}" != "--watch" ]]; then
  gsettings set org.gnome.desktop.interface icon-theme Nothing-Dots
  echo "Nothing Dots applied."
fi
