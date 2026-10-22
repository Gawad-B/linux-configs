#!/usr/bin/env sh
#
# Install the GNOME Shell extensions listed in extensions.txt.
#
# Extensions from extensions.gnome.org are fetched for the running shell
# version. The two extensions I wrote myself are not on e.g.o and are cloned
# from GitHub instead.

set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
shell_ver=$(gnome-shell --version | awk '{print $3}')
user_ext="$HOME/.local/share/gnome-shell/extensions"

printf 'GNOME Shell %s\n\n' "$shell_ver"

mine_uuids='prayer-times@gawad-b.github.io desk-widgets@gawad-b.github.io'

mine_repo() {
  case "$1" in
    prayer-times@gawad-b.github.io) echo 'https://github.com/Gawad-B/Prayer_TImes.git' ;;
    desk-widgets@gawad-b.github.io) echo 'https://github.com/Gawad-B/Gnome-Widgets.git' ;;
  esac
}

is_mine() {
  for u in $mine_uuids; do
    [ "$u" = "$1" ] && return 0
  done
  return 1
}

install_from_ego() {
  uuid=$1
  info_url="https://extensions.gnome.org/extension-info/?uuid=$uuid&shell_version=$shell_ver"
  url=$(curl -fsSL "$info_url" \
    | python3 -I -c 'import json,sys; print(json.load(sys.stdin).get("download_url",""))' 2>/dev/null) || url=''

  if [ -z "$url" ]; then
    printf '  !! no build for shell %s - install manually:\n' "$shell_ver"
    printf '     https://extensions.gnome.org/extension-by-uuid/%s\n' "$uuid"
    return 0
  fi

  tmp=$(mktemp -d)
  curl -fsSL "https://extensions.gnome.org$url" -o "$tmp/ext.zip"
  gnome-extensions install --force "$tmp/ext.zip"
  rm -r "$tmp"
  printf '  installed\n'
}

while read -r uuid; do
  [ -n "$uuid" ] || continue
  printf '%s\n' "$uuid"

  if [ -d "/usr/share/gnome-shell/extensions/$uuid" ]; then
    printf '  ships with the system, skipping\n'
  elif is_mine "$uuid"; then
    printf '  mine - clone and install from %s\n' "$(mine_repo "$uuid")"
  elif [ -d "$user_ext/$uuid" ]; then
    printf '  already installed\n'
  else
    install_from_ego "$uuid"
  fi
done < "$here/extensions.txt"

printf '\nEnabling...\n'
while read -r uuid; do
  [ -n "$uuid" ] || continue
  gnome-extensions enable "$uuid" 2>/dev/null \
    || printf '  could not enable %s (not installed yet?)\n' "$uuid"
done < "$here/extensions.txt"

printf '\nRestore settings with:\n'
printf '  dconf load /org/gnome/shell/extensions/ < %s/extension-settings.dconf\n' "$here"
printf 'Then log out and back in.\n'
