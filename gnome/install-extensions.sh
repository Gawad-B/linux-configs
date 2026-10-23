#!/usr/bin/env sh
#
# Install the GNOME Shell extensions listed in extensions.txt and mark them
# enabled. Safe to re-run: anything already installed is left alone.
#
# Extensions from extensions.gnome.org are fetched for the running shell
# version. The two I wrote myself are not on e.g.o, so they are built from
# source (needs git, npm and make, which bootstrap.sh installs first).
#
# Newly installed extensions only load after logging out and back in; the
# enabled list is written to gsettings so they come up on next login.

set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
shell_ver=$(gnome-shell --version | awk '{print $3}')
user_ext="$HOME/.local/share/gnome-shell/extensions"
src_cache="${XDG_CACHE_HOME:-$HOME/.cache}/linux-configs/src"
failed=0

printf 'GNOME Shell %s\n\n' "$shell_ver"

mine_repo() {
  case "$1" in
    prayer-times@gawad-b.github.io) echo 'https://github.com/Gawad-B/Prayer_TImes.git' ;;
    desk-widgets@gawad-b.github.io) echo 'https://github.com/Gawad-B/Gnome-Widgets.git' ;;
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
  dir="$src_cache/$(basename "$repo" .git)"

  if [ -d "$dir/.git" ]; then
    git -C "$dir" pull -q --ff-only
  else
    mkdir -p "$src_cache"
    git clone -q --depth 1 "$repo" "$dir"
  fi

  (cd "$dir" && npm ci --silent --no-audit --no-fund && make install >/dev/null)
  printf '  built and installed from %s\n' "$repo"
}

while read -r uuid; do
  [ -n "$uuid" ] || continue
  printf '%s\n' "$uuid"

  if [ -d "/usr/share/gnome-shell/extensions/$uuid" ]; then
    printf '  ships with the system\n'
  elif [ -d "$user_ext/$uuid" ]; then
    printf '  already installed\n'
  elif repo=$(mine_repo "$uuid") && [ -n "$repo" ]; then
    install_from_source "$repo" || { printf '  !! build failed\n'; failed=$((failed + 1)); }
  else
    install_from_ego "$uuid" || failed=$((failed + 1))
  fi
done < "$here/extensions.txt"

# Merge extensions.txt into the enabled list rather than replacing it, so
# anything else enabled on this machine stays enabled.
printf '\nEnabling (takes effect on next login)...\n'
merged=$(gsettings get org.gnome.shell enabled-extensions | python3 -I -c '
import ast, sys
raw = sys.stdin.read().strip()
current = [] if raw.startswith("@as") else ast.literal_eval(raw)
wanted = [l.strip() for l in open(sys.argv[1]) if l.strip()]
print(repr(current + [u for u in wanted if u not in current]))
' "$here/extensions.txt")
gsettings set org.gnome.shell enabled-extensions "$merged"
gsettings set org.gnome.shell disable-user-extensions false

if [ "$failed" -gt 0 ]; then
  printf '\n%s extension(s) could not be installed - see the !! lines above.\n' "$failed"
  exit 1
fi
printf '\nDone. Log out and back in to load newly installed extensions.\n'
