# GNOME Shell extensions

Captured on 2026-11-24 from Fedora 45, GNOME Shell 50.

12 extensions are enabled: eight from [extensions.gnome.org](https://extensions.gnome.org)
and four of my own.

## Enabled

| Extension | Version | UUID | Source |
| --- | --- | --- | --- |
| AppIndicator / KStatusNotifierItem Support | 66 | `appindicatorsupport@rgcjonas.gmail.com` | [ubuntu/gnome-shell-extension-appindicator](https://github.com/ubuntu/gnome-shell-extension-appindicator) |
| Blur my Shell | 78 | `blur-my-shell@aunetx` | [aunetx/blur-my-shell](https://github.com/aunetx/blur-my-shell) |
| Caffeine | 61 | `caffeine@patapon.info` | [eonpatapon/gnome-shell-extension-caffeine](https://github.com/eonpatapon/gnome-shell-extension-caffeine) |
| Clipboard Indicator | 74 | `clipboard-indicator@tudmotu.com` | [Tudmotu/gnome-shell-extension-clipboard-indicator](https://github.com/Tudmotu/gnome-shell-extension-clipboard-indicator) |
| Compiz alike magic lamp effect | 25 | `compiz-alike-magic-lamp-effect@hermes83.github.com` | [hermes83/compiz-alike-magic-lamp-effect](https://github.com/hermes83/compiz-alike-magic-lamp-effect) |
| Dash to Dock | 110 | `dash-to-dock@micxgx.gmail.com` | [micheleg/dash-to-dock](https://micheleg.github.io/dash-to-dock/) |
| Search Light | 101 | `search-light@icedman.github.com` | my GNOME 51 port of [icedman/search-light](https://github.com/icedman/search-light), kept in [`local-extensions/`](local-extensions/search-light@icedman.github.com) — extensions.gnome.org stops at v42 for GNOME 49 |
| Vitals | 86 | `Vitals@CoreCoding.com` | [corecoding/Vitals](https://github.com/corecoding/Vitals) |

### My own

| Extension | UUID | Source | Installed by |
| --- | --- | --- | --- |
| Prayer Times | `prayer-times@gawad-b.github.io` | [Gawad-B/Prayer_TImes](https://github.com/Gawad-B/Prayer_TImes) | clone to `~/Coding`, `make install` |
| Desk Widgets | `desk-widgets@gawad-b.github.io` | [Gawad-B/Gnome-Widgets](https://github.com/Gawad-B/Gnome-Widgets) | clone to `~/Coding`, `make install` |
| Dynland | `dynland@gawad-b.github.io` | [Gawad-B/Dynland](https://github.com/Gawad-B/Dynland) | clone to `~/Coding`, `make install` |
| Super Key → Search Light | `super-search-light@gawad-b` | [`local-extensions/`](local-extensions/super-search-light@gawad-b) in this repo | copied as-is |

## Installed but disabled

Not restored on a new machine:

- `just-perfection-desktop@just-perfection` (removed from the enabled set in November)
- `apps-menu@gnome-shell-extensions.gcampax.github.com` (disabled in November;
  ships with `gnome-shell-extensions`)
- `background-logo@fedorahosted.org`, `launch-new-instance@…`, `places-menu@…`,
  `window-list@…` — Fedora's bundled extensions

## Restoring on a new machine

`./bootstrap.sh` does all of this as its `gnome` step. To run just this part:

```sh
./gnome/install-extensions.sh
dconf load /org/gnome/shell/extensions/ < gnome/extension-settings.dconf
```

Log out and back in for the shell to load them.

> **Note:** `extension-settings.dconf` has the Prayer Times latitude and longitude
> and the Desk Widgets video path stripped out, since this repository is public.
> The bootstrap sets Prayer Times to locate itself.

## Re-capturing this list

```sh
./gnome/dump-extensions.sh
```

This table is kept by hand — update it when the list changes.
