# GNOME Shell extensions

Captured on 2026-10-22 from Fedora 44, GNOME Shell 50.5.

12 extensions are enabled. Ten come from [extensions.gnome.org](https://extensions.gnome.org);
two are my own.

## Enabled

| Extension | Version | UUID | Source |
| --- | --- | --- | --- |
| AppIndicator / KStatusNotifierItem Support | 66 | `appindicatorsupport@rgcjonas.gmail.com` | [ubuntu/gnome-shell-extension-appindicator](https://github.com/ubuntu/gnome-shell-extension-appindicator) |
| Blur my Shell | 76 | `blur-my-shell@aunetx` | [aunetx/blur-my-shell](https://github.com/aunetx/blur-my-shell) |
| Caffeine | 61 | `caffeine@patapon.info` | [eonpatapon/gnome-shell-extension-caffeine](https://github.com/eonpatapon/gnome-shell-extension-caffeine) |
| Clipboard Indicator | 71 | `clipboard-indicator@tudmotu.com` | [Tudmotu/gnome-shell-extension-clipboard-indicator](https://github.com/Tudmotu/gnome-shell-extension-clipboard-indicator) |
| Compiz alike magic lamp effect | 25 | `compiz-alike-magic-lamp-effect@hermes83.github.com` | [hermes83/compiz-alike-magic-lamp-effect](https://github.com/hermes83/compiz-alike-magic-lamp-effect) |
| Dash to Dock | 110 | `dash-to-dock@micxgx.gmail.com` | [micheleg/dash-to-dock](https://micheleg.github.io/dash-to-dock/) |
| Just Perfection | 37 | `just-perfection-desktop@just-perfection` | [jrahmatzadeh/just-perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) |
| Search Light | 101 | `search-light@icedman.github.com` | [icedman/search-light](https://github.com/icedman/search-light) |
| Vitals | 86 | `Vitals@CoreCoding.com` | [corecoding/Vitals](https://github.com/corecoding/Vitals) |
| Apps Menu | — | `apps-menu@gnome-shell-extensions.gcampax.github.com` | ships with `gnome-shell-extensions` (system) |

### My own

| Extension | UUID | Source |
| --- | --- | --- |
| Prayer Times | `prayer-times@gawad-b.github.io` | [Gawad-B/Prayer_TImes](https://github.com/Gawad-B/Prayer_TImes) |
| Desk Widgets | `desk-widgets@gawad-b.github.io` | [Gawad-B/Gnome-Widgets](https://github.com/Gawad-B/Gnome-Widgets) |

## Installed but disabled

These ship with Fedora and are not enabled:

- `background-logo@fedorahosted.org`
- `launch-new-instance@gnome-shell-extensions.gcampax.github.com`
- `places-menu@gnome-shell-extensions.gcampax.github.com`
- `window-list@gnome-shell-extensions.gcampax.github.com`

## Restoring on a new machine

`./bootstrap.sh` does all of this as its `gnome` step. To run just this part:

```sh
./gnome/install-extensions.sh
```

Then restore the tweaked settings:

```sh
dconf load /org/gnome/shell/extensions/ < gnome/extension-settings.dconf
```

Log out and back in (or `Alt+F2` → `r` on X11) for the shell to pick them up.

> **Note:** `extension-settings.dconf` has the Prayer Times latitude and longitude
> stripped out, since this repository is public. Set your own location in the
> extension's preferences after loading, or leave `location-auto=true`.

## Re-capturing this list

```sh
./gnome/dump-extensions.sh
```
