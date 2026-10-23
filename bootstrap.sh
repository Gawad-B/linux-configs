#!/usr/bin/env bash
#
# Set up a fresh Fedora + GNOME machine the way I like it, in one go:
# packages and apps, dotfiles, shell, fonts, icons, GRUB theme, wallpaper,
# GNOME extensions and desktop settings.
#
# On a new laptop (no clone needed):
#   curl -fsSL https://raw.githubusercontent.com/Gawad-B/linux-configs/main/bootstrap.sh | bash
#
# From a clone:
#   ./bootstrap.sh                  # everything
#   ./bootstrap.sh gnome dotfiles   # only these steps
#   ./bootstrap.sh --list           # show the steps
#
# You are asked for your sudo password once, at the start. Every step skips
# work that is already done, so re-running is safe -- it is also how a second
# machine picks up changes pushed from the first. A failing step is reported
# at the end instead of stopping the steps after it.

set -uo pipefail

repo_url='https://github.com/Gawad-B/linux-configs.git'
default_dir="$HOME/Coding/linux-configs"
wallpaper='chatgpt-2026-09-20.png'
# Not $USER: it is unset under sudo -i, cron, containers and some SSH setups.
user=$(id -un)
all_steps=(repos packages flatpaks dotfiles tools shell themes grub gnome services neovim)

declare -A step_help=(
  [repos]='RPM Fusion, COPR and vendor repositories'
  [packages]='dnf packages from packages/dnf.txt, full ffmpeg'
  [flatpaks]='Flathub apps from packages/flatpak.txt'
  [dotfiles]='back up conflicting files, then stow every config package'
  [tools]='Starship, Zed, Claude Code, vex, Oh My Zsh, tmux plugins, npm/pipx tools'
  [shell]='make zsh the login shell'
  [themes]='MacTahoe icons and cursors, wallpapers, font cache'
  [grub]='Elegant Mojave GRUB theme'
  [gnome]='extensions, extension settings, desktop settings, wallpaper'
  [services]='docker and postgresql'
  [neovim]='install Neovim plugins pinned in lazy-lock.json'
)

# ------------------------------------------------------------------ output

if [ -t 1 ]; then
  bold=$'\e[1m' red=$'\e[31m' green=$'\e[32m' yellow=$'\e[33m' reset=$'\e[0m'
else
  bold='' red='' green='' yellow='' reset=''
fi

info() { printf '  %s\n' "$*"; }
warn() { printf '  %s!! %s%s\n' "$yellow" "$*" "$reset"; }
die()  { printf '%serror:%s %s\n' "$red" "$reset" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# Inside a step: stop it and report it as skipped rather than failed.
skip() { warn "$*"; exit 2; }

# Non-comment, non-blank first words of a list file in the repo.
read_list() { sed 's/#.*//' "$repo/$1" | awk 'NF { print $1 }'; }

clone_once() {
  if [ -d "$2/.git" ]; then
    info "$(basename "$2") already present"
  else
    git clone -q --depth 1 "$1" "$2"
    info "cloned $(basename "$2")"
  fi
}

# ------------------------------------------------------------------- steps
#
# Each step runs in a subshell with `set -e`, so the first failing command
# ends that step only. Steps must not end on a bare `a && b` (a false `a`
# would read as failure); use `if` instead.

step_repos() {
  local fedora
  fedora=$(rpm -E %fedora)

  if rpm -q rpmfusion-free-release rpmfusion-nonfree-release >/dev/null 2>&1; then
    info 'RPM Fusion already enabled'
  else
    sudo dnf install -y \
      "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$fedora.noarch.rpm" \
      "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$fedora.noarch.rpm"
  fi

  if [ -f '/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:imput:helium.repo' ]; then
    info 'Helium COPR already enabled'
  else
    dnf copr --help >/dev/null 2>&1 || sudo dnf install -y dnf5-plugins
    sudo dnf copr enable -y imput/helium
  fi

  # WhatsApp comes from the Shinux repository, set up by its release package.
  if rpm -q shinux-release >/dev/null 2>&1; then
    info 'Shinux repository already enabled'
  else
    sudo dnf install -y https://abdallah-shehawey.github.io/shinux-repo/rpm/shinux-release-1.2-1.noarch.rpm
  fi

  # Brave, VS Code, Claude Desktop and ChatGPT: plain .repo files, plus the
  # ChatGPT signing key, which its repo file references by local path.
  sudo install -m 644 "$repo"/packages/repos/*.repo /etc/yum.repos.d/
  sudo install -m 644 "$repo"/packages/keys/*.asc /etc/pki/rpm-gpg/
  info "vendor repositories: $(cd "$repo/packages/repos" && ls *.repo | tr '\n' ' ')"
}

step_packages() {
  local pkgs missing=() p
  mapfile -t pkgs < <(read_list packages/dnf.txt)

  # Fedora ships a patent-stripped ffmpeg; swap in RPM Fusion's full build.
  if rpm -q ffmpeg >/dev/null 2>&1; then
    info 'full ffmpeg already installed'
  elif rpm -q ffmpeg-free >/dev/null 2>&1; then
    sudo dnf swap -y ffmpeg-free ffmpeg --allowerasing
  else
    sudo dnf install -y --allowerasing ffmpeg
  fi

  info "installing ${#pkgs[@]} packages (already-installed ones are skipped)"
  sudo dnf install -y --skip-unavailable "${pkgs[@]}"

  for p in "${pkgs[@]}"; do
    rpm -q --whatprovides "$p" >/dev/null 2>&1 || missing+=("$p")
  done
  if [ ${#missing[@]} -gt 0 ]; then
    warn "not available, so not installed: ${missing[*]}"
    return 1
  fi
}

step_flatpaks() {
  local apps todo=() a
  have flatpak || sudo dnf install -y flatpak

  if flatpak remotes --system --columns=name | grep -qx flathub; then
    info 'Flathub already configured'
  else
    sudo flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  fi

  mapfile -t apps < <(read_list packages/flatpak.txt)
  for a in "${apps[@]}"; do
    flatpak info --system "$a" >/dev/null 2>&1 || todo+=("$a")
  done

  if [ ${#todo[@]} -eq 0 ]; then
    info "all ${#apps[@]} Flatpaks already installed"
  else
    sudo flatpak install -y --noninteractive --system flathub "${todo[@]}"
  fi
}

step_dotfiles() {
  local packages backup moved=0 p target
  have stow || sudo dnf install -y stow

  # install.sh owns the list of stow packages; read it rather than repeat it.
  packages=$(sed -n "s/^packages='\(.*\)'$/\1/p" "$repo/install.sh")
  if [ -z "$packages" ]; then
    warn 'could not read the package list from install.sh'
    return 1
  fi

  # A fresh machine already has a stock .bashrc, .bash_profile and so on, which
  # stow refuses to overwrite. Ask stow which targets conflict, move exactly
  # those aside, then link.
  backup="$HOME/dotfiles-backup-$(date +%Y%m%d-%H%M%S)"
  for p in $packages; do
    while IFS= read -r target; do
      [ -n "$target" ] || continue
      mkdir -p "$backup/$(dirname "$target")"
      mv "$HOME/$target" "$backup/$target"
      info "backed up ~/$target"
      moved=$((moved + 1))
    done < <(cd "$repo" && stow -n --no-folding --target="$HOME" --restow "$p" 2>&1 | sed -n \
               -e 's/.* over existing target \(.*\) since .*/\1/p' \
               -e 's/.*existing target is not owned by stow: \(.*\)$/\1/p' \
               -e 's/.*existing target is neither a link nor a directory: \(.*\)$/\1/p')
  done

  if [ "$moved" -gt 0 ]; then
    info "$moved existing file(s) moved to $backup"
  fi

  BOOTSTRAP=1 "$repo/install.sh"
}

step_tools() {
  local custom url npms todo=() n app

  if have starship; then
    info 'Starship already installed'
  else
    curl -fsSL https://starship.rs/install.sh | sh -s -- --yes
  fi

  if [ -x "$HOME/.local/bin/zed" ]; then
    info 'Zed already installed'
  else
    curl -fsSL https://zed.dev/install.sh | sh
  fi

  if have claude || [ -x "$HOME/.local/bin/claude" ]; then
    info 'Claude Code already installed'
  else
    curl -fsSL https://claude.ai/install.sh | bash
  fi

  # vex, my editor: the RPM from its latest GitHub release. The repo is
  # private, so this needs a signed-in gh; without one, skip it and carry on.
  if rpm -q vex >/dev/null 2>&1; then
    info 'vex already installed'
  elif gh auth status >/dev/null 2>&1; then
    tmp=$(mktemp -d)
    gh release download -R Gawad-B/vex --pattern '*.x86_64.rpm' --dir "$tmp"
    sudo dnf install -y "$tmp"/*.rpm
    rm -r "$tmp"
  else
    warn 'vex skipped: its repo is private. Run `gh auth login`, then ./bootstrap.sh tools'
  fi

  # --keep-zshrc: .zshrc is already linked from this repo by the dotfiles step.
  if [ -d "$HOME/.oh-my-zsh" ]; then
    info 'Oh My Zsh already installed'
  else
    RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c \
      "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
      '' --unattended --keep-zshrc
  fi
  custom="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins"
  clone_once https://github.com/zsh-users/zsh-autosuggestions "$custom/zsh-autosuggestions"
  clone_once https://github.com/zsh-users/zsh-syntax-highlighting "$custom/zsh-syntax-highlighting"

  # TPM, then the plugins tmux.conf asks for.
  clone_once https://github.com/tmux-plugins/tpm "$HOME/.config/tmux/plugins/tpm"
  "$HOME/.config/tmux/plugins/tpm/bin/install_plugins" >/dev/null
  info 'tmux plugins installed'

  # Global npm packages go under /usr/local, so they need sudo.
  mapfile -t npms < <(read_list packages/npm-global.txt)
  for n in "${npms[@]}"; do
    npm ls -g --depth=0 "$n" >/dev/null 2>&1 || todo+=("$n")
  done
  if [ ${#todo[@]} -eq 0 ]; then
    info 'npm globals already installed'
  else
    sudo npm install -g --no-fund --no-audit "${todo[@]}"
  fi

  while IFS= read -r app; do
    if pipx list --short 2>/dev/null | grep -q "^$app "; then
      info "$app (pipx) already installed"
    else
      pipx install "$app"
    fi
  done < <(read_list packages/pipx.txt)
}

step_shell() {
  local zsh_path current
  zsh_path=$(command -v zsh) || { warn 'zsh is not installed'; return 1; }
  current=$(getent passwd "$user" | cut -d: -f7)

  if [ "$current" = "$zsh_path" ]; then
    info 'login shell is already zsh'
  else
    sudo usermod -s "$zsh_path" "$user"
    info 'login shell set to zsh (takes effect on next login)'
  fi
}

step_themes() {
  if [ -d "$HOME/.local/share/icons/MacTahoe-dark" ]; then
    info 'MacTahoe icons already installed'
  else
    "$repo/icons/install.sh"
  fi

  # Every wallpaper, so they are all selectable in Settings > Appearance.
  mkdir -p "$HOME/.local/share/backgrounds"
  cp -u "$repo"/wallpapers/* "$HOME/.local/share/backgrounds/"
  info "wallpapers copied to ~/.local/share/backgrounds"

  fc-cache -f >/dev/null
  info 'font cache refreshed'
}

step_grub() {
  local theme_txt=/boot/grub2/themes/Elegant-mojave-window-left-dark/theme.txt

  if sudo test -f "$theme_txt" && grep -q "^GRUB_THEME=\"$theme_txt\"" /etc/default/grub; then
    info 'GRUB theme already installed'
  else
    sudo "$repo/grub-theme/install.sh"
  fi
}

step_gnome() {
  local uri ext_failed=0

  if [ "$gnome_session" != yes ]; then
    skip 'no GNOME session here -- run this step from a logged-in GNOME desktop'
  fi

  "$repo/gnome/install-extensions.sh" || ext_failed=1

  dconf load /org/gnome/shell/extensions/ < "$repo/gnome/extension-settings.dconf"
  # The repo carries no coordinates for Prayer Times (it is public), so on a
  # machine that has none set, let the extension locate itself.
  if [ -z "$(dconf read /org/gnome/shell/extensions/prayer-times/latitude)" ]; then
    dconf write /org/gnome/shell/extensions/prayer-times/location-auto true
    info 'Prayer Times set to detect your location automatically'
  fi
  info 'extension settings loaded'

  dconf load /org/gnome/ < "$repo/gnome/desktop-settings.dconf"
  info 'desktop settings loaded (theme, keybindings, touchpad, dock favourites)'

  uri="file://$HOME/.local/share/backgrounds/$wallpaper"
  gsettings set org.gnome.desktop.background picture-uri "$uri"
  gsettings set org.gnome.desktop.background picture-uri-dark "$uri"
  gsettings set org.gnome.desktop.screensaver picture-uri "$uri"
  info "wallpaper set to $wallpaper"

  if [ "$ext_failed" -ne 0 ]; then
    warn 'some extensions could not be installed (see above)'
    return 1
  fi
}

step_services() {
  sudo systemctl enable --now docker
  if id -nG "$user" | grep -qw docker; then
    info 'already in the docker group'
  else
    sudo usermod -aG docker "$user"
    info 'added to the docker group (takes effect on next login)'
  fi

  if sudo test -f /var/lib/pgsql/data/PG_VERSION; then
    info 'PostgreSQL data directory already initialised'
  else
    sudo postgresql-setup --initdb
  fi
  sudo systemctl enable --now postgresql
  info 'docker and postgresql enabled'
}

step_neovim() {
  have nvim || { warn 'neovim is not installed'; return 1; }
  # `restore` installs the exact versions in lazy-lock.json; `sync` would
  # update them and dirty the tracked lockfile.
  nvim --headless '+Lazy! restore' +qa
  info 'Neovim plugins installed from lazy-lock.json'
}

# -------------------------------------------------------------------- setup

usage() {
  cat <<EOF
Usage: bootstrap.sh [--list] [step ...]

With no steps, runs all of them in order. Steps:
EOF
  for s in "${all_steps[@]}"; do printf '  %-10s %s\n' "$s" "${step_help[$s]}"; done
}

preflight() {
  [ "$EUID" -ne 0 ] || die 'run this as your normal user, not root; it asks for sudo itself'

  # shellcheck disable=SC1091
  . /etc/os-release
  [ "${ID:-}" = fedora ] || die "this script targets Fedora; this machine runs ${PRETTY_NAME:-something else}"

  curl -fsI --max-time 15 https://github.com >/dev/null || die "can't reach github.com -- check the network"

  if [[ "${XDG_CURRENT_DESKTOP:-}" == *GNOME* ]] && [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    gnome_session=yes
  else
    gnome_session=no
  fi
}

start_sudo() {
  printf '%sThis needs sudo for packages, repositories and the GRUB theme.%s\n' "$bold" "$reset"
  sudo -v || die 'sudo authentication failed'
  # Keep the credentials fresh for the whole run so you are only asked once.
  ( while kill -0 "$$" 2>/dev/null; do sudo -n true; sleep 50; done ) 2>/dev/null &
  keepalive=$!
  trap 'kill "$keepalive" 2>/dev/null' EXIT
}

locate_repo() {
  local self=${BASH_SOURCE[0]:-}

  if [ -n "$self" ] && [ -f "$self" ] && [ -f "$(dirname "$self")/packages/dnf.txt" ]; then
    repo=$(cd "$(dirname "$self")" && pwd)
  else
    # Piped from curl: fetch the repository first.
    repo=${REPO_DIR:-$default_dir}
    if [ ! -d "$repo/.git" ]; then
      have git || sudo dnf install -y git
      mkdir -p "$(dirname "$repo")"
      git clone -q "$repo_url" "$repo"
      info "cloned configs to $repo"
    fi
  fi

  # Pick up anything pushed from another machine -- unless there are local
  # edits, which a pull could conflict with.
  if [ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]; then
    warn "local changes in $repo, so not pulling; using the files as they are"
  elif git -C "$repo" pull -q --ff-only 2>/dev/null; then
    info "configs up to date ($(git -C "$repo" log -1 --format=%h))"
  else
    warn 'could not pull the latest configs; using the local copy'
  fi
}

main() {
  local steps=() s rc
  local -a done_ok=() done_failed=() done_skipped=()

  case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    -l|--list) usage; exit 0 ;;
  esac

  if [ $# -eq 0 ]; then
    steps=("${all_steps[@]}")
  else
    for s in "$@"; do
      [ -n "${step_help[$s]:-}" ] || { usage; die "unknown step: $s"; }
      steps+=("$s")
    done
  fi

  log="$HOME/linux-configs-bootstrap-$(date +%Y%m%d-%H%M%S).log"
  exec > >(tee -a "$log") 2>&1

  printf '%sBootstrapping: %s%s\n\n' "$bold" "${steps[*]}" "$reset"
  preflight
  start_sudo
  locate_repo
  [ "$gnome_session" = yes ] || warn 'not in a GNOME session: the gnome step will be skipped'

  for s in "${steps[@]}"; do
    printf '\n%s==> %s%s  (%s)\n' "$bold" "$s" "$reset" "${step_help[$s]}"
    # Children get /dev/null on stdin: when this script is piped from curl,
    # stdin is the script itself, and anything reading it would eat the rest.
    ( set -e; "step_$s" ) </dev/null
    rc=$?
    case $rc in
      0) done_ok+=("$s") ;;
      2) done_skipped+=("$s") ;;
      *) done_failed+=("$s"); warn "step '$s' failed (exit $rc)" ;;
    esac
  done

  printf '\n%s==> Summary%s\n' "$bold" "$reset"
  [ ${#done_ok[@]} -eq 0 ]      || printf '  %sdone:%s    %s\n' "$green"  "$reset" "${done_ok[*]}"
  [ ${#done_skipped[@]} -eq 0 ] || printf '  %sskipped:%s %s\n' "$yellow" "$reset" "${done_skipped[*]}"
  [ ${#done_failed[@]} -eq 0 ]  || printf '  %sfailed:%s  %s  (re-run with: ./bootstrap.sh %s)\n' \
                                     "$red" "$reset" "${done_failed[*]}" "${done_failed[*]}"

  cat <<EOF

${bold}Still up to you:${reset}
  - Log out and back in: loads new extensions, zsh and the docker group.
  - Sign in where needed: tailscale up, gh auth login, claude.
  - vex is private: if it was skipped, run gh auth login, then ./bootstrap.sh tools.
  - Not automated (no reliable installer): codex, agy, hermes, rtk, cua-driver.
  - GPU drivers are not installed; on an NVIDIA laptop install akmod-nvidia yourself.

Full log: $log
EOF

  [ ${#done_failed[@]} -eq 0 ]
}

main "$@"
