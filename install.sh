#!/usr/bin/env sh

set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
packages='shell git alacritty kitty fastfetch starship tmux nvim btop zed vscode gtk-theme'

if ! command -v stow >/dev/null 2>&1; then
  printf '%s\n' 'GNU Stow is required. Install it with your distribution package manager, then re-run this script.' >&2
  printf '%s\n' '  Fedora: sudo dnf install stow    Debian/Ubuntu: sudo apt install stow' >&2
  exit 1
fi

cd "$repo_dir"

for package in $packages; do
  stow --target="$HOME" --restow "$package"
done

printf '%s\n' 'Dotfiles linked successfully.'
printf '%s\n' ''
printf '%s\n' 'Themes are installed separately (they live outside the stow tree):'
printf '%s\n' '  ./icons/install.sh          # MacTahoe icon theme, fetched from upstream'
printf '%s\n' '  sudo ./grub-theme/install.sh  # Elegant Mojave GRUB theme'
