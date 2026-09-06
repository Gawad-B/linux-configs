#!/usr/bin/env sh
#
# Install the GRUB theme.
#
# Unlike the stow packages, this writes outside $HOME and needs root.
# Tested on Fedora 44 (UEFI). On Debian/Ubuntu the theme directory is
# /boot/grub/themes and the config is regenerated with update-grub.

set -eu

theme='Elegant-mojave-window-left-dark'
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
themes_dir='/boot/grub2/themes'

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'This script must be run as root: sudo ./grub-theme/install.sh' >&2
  exit 1
fi

install -d "$themes_dir"
cp -r "$src/$theme" "$themes_dir/"

# Point GRUB at the theme, replacing any existing GRUB_THEME line.
if grep -q '^GRUB_THEME=' /etc/default/grub; then
  sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"$themes_dir/$theme/theme.txt\"|" /etc/default/grub
else
  printf 'GRUB_THEME="%s/%s/theme.txt"\n' "$themes_dir" "$theme" >> /etc/default/grub
fi

# A theme only renders in graphical mode.
grep -q '^GRUB_TERMINAL_OUTPUT="gfxterm"' /etc/default/grub \
  || printf 'GRUB_TERMINAL_OUTPUT="gfxterm"\n' >> /etc/default/grub

grub2-mkconfig -o /boot/grub2/grub.cfg

printf '%s\n' 'GRUB theme installed. Reboot to see it.'
