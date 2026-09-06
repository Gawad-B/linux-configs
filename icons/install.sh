#!/usr/bin/env sh
#
# Install the icon themes used by this setup.
#
# The icon themes are NOT vendored into this repository: the MacTahoe set alone
# is ~215 MB across 44k files, the vast majority of them symlinks. Fetching from
# upstream keeps the repository small and the themes up to date.
#
# Active theme on this machine: MacTahoe
# (set with: gsettings set org.gnome.desktop.interface icon-theme MacTahoe)

set -eu

dest="${ICON_DEST:-$HOME/.local/share/icons}"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if ! command -v git >/dev/null 2>&1; then
  printf '%s\n' 'git is required.' >&2
  exit 1
fi

mkdir -p "$dest"

install_theme() {
  repo=$1
  name=$2
  printf 'Installing %s from %s\n' "$name" "$repo"
  git clone --depth 1 "$repo" "$tmp/$name"
  (cd "$tmp/$name" && ./install.sh -d "$dest")
}

install_theme https://github.com/vinceliuice/MacTahoe-icon-theme.git MacTahoe

# WhiteSur is also installed on this machine but is not the active theme.
# Uncomment to install it as well.
# install_theme https://github.com/vinceliuice/WhiteSur-icon-theme.git WhiteSur

printf '\nInstalled to %s\n' "$dest"
printf '%s\n' 'Select it with:'
printf '%s\n' '  gsettings set org.gnome.desktop.interface icon-theme MacTahoe'
