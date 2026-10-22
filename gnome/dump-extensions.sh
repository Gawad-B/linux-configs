#!/usr/bin/env sh
#
# Re-capture the enabled GNOME extensions and their settings into this folder.
#
# Run this after installing, removing, or reconfiguring an extension, then
# review the diff and commit.
#
# Personal data is stripped before writing, because this repository is public:
#   - Prayer Times latitude/longitude  -> replaced with a comment
#   - Desk Widgets background video path -> blanked
# Re-check the diff for anything else personal before you commit.

set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

gsettings get org.gnome.shell enabled-extensions \
  | tr -d "[]'" \
  | tr ',' '\n' \
  | sed 's/^ *//;s/ *$//' \
  | grep -v '^$' \
  | sort > "$here/extensions.txt"

dconf dump /org/gnome/shell/extensions/ \
  | sed -E "s|^latitude=.*|# latitude stripped (public repo) -- set via Prayer Times prefs|" \
  | sed -E "s|^longitude=.*|# longitude stripped (public repo) -- set via Prayer Times prefs|" \
  | sed -E "s|^background-video-path=.*|background-video-path=''|" \
  > "$here/extension-settings.dconf"

printf 'Wrote:\n'
printf '  %s (%s extensions)\n' "$here/extensions.txt" "$(wc -l < "$here/extensions.txt")"
printf '  %s\n' "$here/extension-settings.dconf"
printf '\nEXTENSIONS.md is maintained by hand - update it if the list changed.\n'
printf 'Review the diff for personal data before committing.\n'
