# Linux dotfiles

Personal Linux configuration (Fedora 44, GNOME), organized as [GNU Stow](https://www.gnu.org/software/stow/) packages. Each top-level directory mirrors the files' destination below `$HOME`; for example, `nvim/.config/nvim/init.lua` is linked to `~/.config/nvim/init.lua`.

## Included

### Stow packages (linked into `$HOME`)

- `shell` — Bash and Zsh startup configuration (Oh My Zsh + Starship)
- `git` — Git identity and preferences
- `alacritty`, `kitty`, `fastfetch`, `starship`, `tmux`, `btop` — terminal tooling
- `nvim`, `vscode`, `zed` — editor configuration
- `gtk-theme` — the Rosepine Dark GTK theme

### Installed separately

These live outside `$HOME` or are too large to vendor, so they have their own scripts:

- `icons/install.sh` — **MacTahoe** icon theme (the active one), fetched from
  [vinceliuice/MacTahoe-icon-theme](https://github.com/vinceliuice/MacTahoe-icon-theme).
  Not vendored: the theme is ~215 MB across 44k files.
- `grub-theme/install.sh` — **Elegant Mojave (window-left-dark)** GRUB theme.
  Vendored in `grub-theme/`, copied to `/boot/grub2/themes` and wired into
  `/etc/default/grub`. Needs root.
- `wallpapers/` — desktop backgrounds, set manually.

Only portable, intentional configuration is tracked. Browser profiles, SSH/GPG keys, passwords, tokens, shell history, caches, generated state, editor workspaces, and vendored plugin/theme repositories are deliberately excluded.

## Install on a new machine

Install GNU Stow with your distribution package manager, clone this repository anywhere, then run:

```sh
./install.sh
```

The script uses `stow` to create symlinks in your home directory. It will stop on a conflict rather than overwrite an existing file. Review or back up conflicting files, then re-run it. To install only one package:

```sh
stow -t "$HOME" nvim
```

Then install the themes:

```sh
./icons/install.sh
sudo ./grub-theme/install.sh
```

After installing the tmux package, install its plugins from inside tmux with `prefix` then `I` (the prefix is `Ctrl-a`), or clone TPM to `~/.tmux/plugins/tpm` first.

## Current appearance settings

```sh
gsettings set org.gnome.desktop.interface icon-theme MacTahoe
gsettings set org.gnome.desktop.interface gtk-theme Adwaita
```

The GTK theme in use is the system-provided `Adwaita` with a dark preference. `Rosepine-Dark` is included and linked to `~/.themes/Rosepine-Dark`; select it in your desktop's appearance settings if you want it.

## Keeping this repo in sync

Because the packages are stowed, `~/.bashrc` and friends are **symlinks into this
repository**. Editing them in place edits the repo, so changes show up in
`git status` directly:

```sh
git status
git diff
git commit -am 'update configs'
git push
```

If `git status` is empty after you have changed a config, the file is probably a
real file rather than a symlink — re-run `./install.sh` for that package.

## Adding a config later

1. Put the file under the appropriate package using its path relative to `$HOME`.
2. Keep secrets in a separate encrypted store, never in this repository.
3. Run `stow -t "$HOME" --restow <package>` to link it.
4. Run `git status`, review the diff, and commit.
