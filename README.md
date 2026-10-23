# Linux dotfiles

My whole Fedora 44 + GNOME setup: configs, apps, fonts, icons, GRUB theme,
wallpaper, GNOME extensions and desktop settings — reproducible on any machine
with one command.

## New machine: one command

On a fresh Fedora install, logged in to the GNOME desktop:

```sh
curl -fsSL https://raw.githubusercontent.com/Gawad-B/linux-configs/main/bootstrap.sh | bash
```

That clones this repo to `~/Coding/linux-configs` and sets everything up. It
asks for your sudo password **once**, at the start, then runs unattended.
When it finishes, log out and back in.

Already have a clone? Run it from there instead:

```sh
./bootstrap.sh                 # everything
./bootstrap.sh gnome dotfiles  # only some steps
./bootstrap.sh --list          # what each step does
```

| Step | What it does |
| --- | --- |
| `repos` | RPM Fusion, Helium COPR, Shinux, and the Brave / VS Code / Claude Desktop / ChatGPT repos |
| `packages` | everything in [`packages/dnf.txt`](packages/dnf.txt), plus RPM Fusion's full ffmpeg |
| `flatpaks` | [`packages/flatpak.txt`](packages/flatpak.txt) from Flathub |
| `dotfiles` | backs up any file in the way, then stows every config package |
| `tools` | Starship, Zed, Claude Code, vex, Oh My Zsh + plugins, tmux plugins, npm and pipx tools |
| `shell` | makes zsh the login shell |
| `themes` | MacTahoe icons and cursors, wallpapers, font cache |
| `grub` | the Elegant Mojave GRUB theme |
| `gnome` | extensions (incl. my own Prayer Times and Desk Widgets, built from source), their settings, keybindings, touchpad, dock favourites, wallpaper |
| `services` | enables docker (and adds you to its group) and postgresql |
| `neovim` | installs the plugins pinned in `lazy-lock.json` |

Every step checks before acting, so **re-running is safe** — it only does what
is missing. A step that fails is reported in the summary without stopping the
rest; fix the cause and re-run just that step. Everything is logged to
`~/linux-configs-bootstrap-<timestamp>.log`, and any file the dotfiles step
replaces is moved to `~/dotfiles-backup-<timestamp>/`, never deleted.

**Not automated**, listed at the end of every run:

- signing in: `tailscale up`, `gh auth login`, `claude`
- `codex`, `agy`, `hermes`, `rtk`, `cua-driver` — no installer I can rely on
- GPU drivers — they depend on each laptop's hardware

## Keeping several machines in sync

The configs are **symlinks into this repo**, so editing `~/.zshrc` or
`~/.config/kitty/kitty.conf` edits the repo directly. GNOME settings live in
dconf rather than files, so capture those explicitly:

```sh
./gnome/dump-desktop.sh      # keybindings, touchpad, theme, dock favourites
./gnome/dump-extensions.sh   # extension list and settings
git add -A && git commit -m 'update configs' && git push
```

On the other machine:

```sh
./bootstrap.sh
```

It pulls the latest commit first — unless the clone there has uncommitted
changes, in which case it warns and uses the files as they are.

> Re-running applies the repo's GNOME settings over the machine's. Capture any
> tweaks you want to keep **before** you re-run.

## Layout

### Stow packages (linked into `$HOME`)

Each directory mirrors its destination below `$HOME`; for example,
`nvim/.config/nvim/init.lua` is linked to `~/.config/nvim/init.lua`.

- `shell` — Bash and Zsh startup configuration (Oh My Zsh + Starship)
- `git` — Git identity and preferences
- `alacritty`, `kitty`, `fastfetch`, `starship`, `tmux`, `btop` — terminal tooling
- `nvim`, `vscode`, `zed` — editor configuration
- `gtk-theme` — the Rosepine Dark GTK theme (installed, not active)

Files are linked individually (`stow --no-folding`), never whole directories,
so apps can't write their caches into this repo.

### Everything else

- `packages/` — dnf, Flatpak, npm and pipx package lists, plus the third-party
  `.repo` files and the ChatGPT repo's public signing key.
- `icons/install.sh` — **MacTahoe** icons and cursors, fetched from
  [vinceliuice/MacTahoe-icon-theme](https://github.com/vinceliuice/MacTahoe-icon-theme)
  (not vendored: ~215 MB).
- `grub-theme/` — **Elegant Mojave (window-left-dark)**, vendored, with an
  installer that wires it into `/etc/default/grub`.
- `gnome/` — see [`gnome/EXTENSIONS.md`](gnome/EXTENSIONS.md) for the
  extension list. `desktop-settings.dconf` and `extension-settings.dconf` hold
  the settings; the `dump-*.sh` scripts re-capture them.
- `wallpapers/` — all copied to `~/.local/share/backgrounds`; the active one is
  set by the `wallpaper` variable at the top of `bootstrap.sh`.

## Current look

- Icons and cursor: `MacTahoe-dark`
- GTK: system `Adwaita`, dark preference
- Fonts: JetBrains Mono in the terminals
- Buttons on the left: close, minimize, maximize

## Privacy

This repo is public. Only portable, intentional configuration is tracked —
never SSH/GPG keys, tokens, shell history, caches or browser profiles. The dump
scripts strip personal data before writing: the Prayer Times coordinates, the
Desk Widgets video path, and GNOME's night-light location. On a new machine,
Prayer Times is set to find your location automatically.

## Adding a config later

1. Put the file under the right package, at its path relative to `$HOME`.
2. Keep secrets in a separate encrypted store, never in this repository.
3. `stow --no-folding -t "$HOME" --restow <package>` to link it.
4. `git status`, review the diff, commit.

New package to install everywhere? Add it to the matching list in `packages/`.
