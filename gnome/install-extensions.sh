#!/usr/bin/env sh
#
# Install the GNOME Shell extensions listed in extensions.txt and mark them
# enabled. Safe to re-run: anything already installed is left alone.
#
# Three sources:
#   - extensions.gnome.org, fetched for the running shell version
#   - my own published extensions, cloned into ~/Coding and installed with
#     their own `make install` (needs git, npm and make; bootstrap.sh installs
#     them first)
#   - small local-only extensions kept in local-extensions/, copied as-is
#
# Newly installed extensions only load after logging out and back in; the
# enabled list is written to gsettings so they come up on next login.

set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
shell_ver=$(gnome-shell --version | awk '{print $3}')
user_ext="$HOME/.local/share/gnome-shell/extensions"
# Cloned where I keep code rather than into a cache: a checkout installed with
# `make link` keeps pointing at it.
src_dir="$HOME/Coding"
failed=0

# Extensions I no longer use. Machines set up earlier still have them enabled,
# and this script only ever adds, so they are disabled and removed here.
#   super-search-light: Super opens the overview again; Search Light has its
#   own Super+Space shortcut (2026-11-27).
#   vertical-workspaces (V-Shell): replaced by Mission Control, which reshapes
#   the overview itself and stays off while V-Shell is active (2026-11-28).
retired='super-search-light@gawad-b vertical-workspaces@G-dH.github.com'

printf 'GNOME Shell %s\n\n' "$shell_ver"

mine_repo() {
  case "$1" in
    prayer-times@gawad-b.github.io) echo 'https://github.com/Gawad-B/Prayer_TImes.git' ;;
    desk-widgets@gawad-b.github.io) echo 'https://github.com/Gawad-B/Gnome-Widgets.git' ;;
    dynland@gawad-b.github.io)      echo 'https://github.com/Gawad-B/Dynland.git' ;;
    mission-control@gawad-b.github.io) echo 'https://github.com/Gawad-B/Mission-Control.git' ;;
  esac
}

install_from_ego() {
  uuid=$1
  info_url="https://extensions.gnome.org/extension-info/?uuid=$uuid&shell_version=$shell_ver"
  url=$(curl -fsSL "$info_url" \
    | python3 -I -c 'import json,sys; print(json.load(sys.stdin).get("download_url",""))' 2>/dev/null) || url=''

  if [ -z "$url" ]; then
    printf '  !! no build for shell %s - install manually:\n' "$shell_ver"
    printf '     https://extensions.gnome.org/extension-by-uuid/%s\n' "$uuid"
    return 1
  fi

  tmp=$(mktemp -d)
  curl -fsSL "https://extensions.gnome.org$url" -o "$tmp/ext.zip"
  gnome-extensions install --force "$tmp/ext.zip"
  rm -r "$tmp"
  printf '  installed from extensions.gnome.org\n'
}

install_from_source() {
  repo=$1
  dir="$src_dir/$(basename "$repo" .git)"

  if [ ! -d "$dir/.git" ]; then
    mkdir -p "$src_dir"
    git clone -q "$repo" "$dir"
  fi

  # Each repo's own Makefile knows how to build and install it (Mission
  # Control's compiles its schema with glib-compile-schemas, from glib2).
  (
    cd "$dir"
    if [ -f package-lock.json ]; then npm ci --silent --no-audit --no-fund; fi
    make install >/dev/null
  )
  printf '  built and installed from %s\n' "$dir"
}

while read -r uuid; do
  [ -n "$uuid" ] || continue
  printf '%s\n' "$uuid"

  if [ -d "/usr/share/gnome-shell/extensions/$uuid" ]; then
    printf '  ships with the system\n'
  elif [ -d "$here/local-extensions/$uuid" ]; then
    # The repo copy is authoritative (e.g. my GNOME 51 port of Search Light),
    # so it also replaces an older install from extensions.gnome.org.
    # "Matches" means every file in the repo copy is identical; extra files
    # in the installed copy (backups and the like) don't count.
    src="$here/local-extensions/$uuid"
    if [ -d "$user_ext/$uuid" ] && (cd "$src" && find . -type f) | while read -r f; do
         cmp -s "$src/$f" "$user_ext/$uuid/$f" || exit 1
       done; then
      printf '  up to date with local-extensions/\n'
    else
      mkdir -p "$user_ext"
      rm -rf "${user_ext:?}/$uuid"
      cp -r "$src" "$user_ext/"
      printf '  installed from local-extensions/\n'
    fi
  elif [ -d "$user_ext/$uuid" ]; then
    printf '  already installed\n'
  elif repo=$(mine_repo "$uuid") && [ -n "$repo" ]; then
    install_from_source "$repo" || { printf '  !! build failed\n'; failed=$((failed + 1)); }
  else
    install_from_ego "$uuid" || failed=$((failed + 1))
  fi
done < "$here/extensions.txt"

for uuid in $retired; do
  if [ -d "$user_ext/$uuid" ]; then
    gnome-extensions disable "$uuid" 2>/dev/null || true
    rm -rf "${user_ext:?}/$uuid"
    printf '%s\n  retired: disabled and removed\n' "$uuid"
  fi
done

# Merge extensions.txt into the enabled list rather than replacing it, so
# anything else enabled on this machine stays enabled -- except retired ones.
printf '\nEnabling (takes effect on next login)...\n'
merged=$(gsettings get org.gnome.shell enabled-extensions | python3 -I -c '
import ast, sys
raw = sys.stdin.read().strip()
current = [] if raw.startswith("@as") else ast.literal_eval(raw)
retired = sys.argv[2].split()
current = [u for u in current if u not in retired]
wanted = [l.strip() for l in open(sys.argv[1]) if l.strip()]
print(repr(current + [u for u in wanted if u not in current]))
' "$here/extensions.txt" "$retired")
gsettings set org.gnome.shell enabled-extensions "$merged"

# GNOME treats disabled-extensions as an override: an extension switched off
# once (e.g. V-Shell, disabled months ago) stays off even when it is in the
# enabled list. Drop every wanted extension from it.
undisabled=$(gsettings get org.gnome.shell disabled-extensions | python3 -I -c '
import ast, sys
raw = sys.stdin.read().strip()
current = [] if raw.startswith("@as") else ast.literal_eval(raw)
wanted = {l.strip() for l in open(sys.argv[1]) if l.strip()}
print(repr([u for u in current if u not in wanted]))
' "$here/extensions.txt")
gsettings set org.gnome.shell disabled-extensions "$undisabled"
gsettings set org.gnome.shell disable-user-extensions false

if [ "$failed" -gt 0 ]; then
  printf '\n%s extension(s) could not be installed - see the !! lines above.\n' "$failed"
  exit 1
fi
printf '\nDone. Log out and back in to load newly installed extensions.\n'
