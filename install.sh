#!/usr/bin/env sh

set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
packages='shell git alacritty kitty fastfetch starship tmux nvim gtk-theme'

if ! command -v stow >/dev/null 2>&1; then
  printf '%s\n' 'GNU Stow is required. Install it with your distribution package manager, then re-run this script.' >&2
  exit 1
fi

cd "$repo_dir"

for package in $packages; do
  stow --target="$HOME" --restow "$package"
done

printf '%s\n' 'Dotfiles linked successfully.'
