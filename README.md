# Linux dotfiles

Personal Linux configuration, organized as [GNU Stow](https://www.gnu.org/software/stow/) packages. Each top-level directory mirrors the files' destination below `$HOME`; for example, `nvim/.config/nvim/init.lua` is linked to `~/.config/nvim/init.lua`.

## Included

- `shell` — Bash and Zsh startup configuration
- `git` — Git identity and preferences
- `alacritty`, `kitty`, `fastfetch`, `starship`, `tmux` — terminal tooling
- `nvim`, `vscode`, `zed` — editor configuration
- `notchnux` — NotchNux settings
- `gtk-theme` — the user-installed Rosepine Dark GTK theme

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

After installing the tmux package, install its plugins from inside tmux with `prefix` then `I` (the prefix is `Ctrl-a`), or clone TPM to `~/.tmux/plugins/tpm` first.

The GTK theme is linked to `~/.themes/Rosepine-Dark`. Your current GNOME selection is the system-provided `Adwaita` theme with a dark preference; select `Rosepine-Dark` in your desktop's appearance settings whenever you want to use the included theme.

## Adding a config later

1. Put the file under the appropriate package using its path relative to `$HOME`.
2. Keep secrets in a separate encrypted store, never in this repository.
3. Run `git status`, review the diff, and commit.

This layout follows the straightforward Git + Stow approach commonly recommended in Linux dotfiles discussions: simple packages, symlinks to their natural locations, and no generated or secret data committed.
