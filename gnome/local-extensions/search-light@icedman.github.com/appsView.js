/* appsView.js
 *
 * Local addition: a Spotlight-style "Applications" view shown under the
 * search entry while the query is empty. Category chips filter the grid, and
 * the grid lists every visible app A-Z.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

import Clutter from 'gi://Clutter';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Pango from 'gi://Pango';
import Shell from 'gi://Shell';
import St from 'gi://St';

import { ensureActorVisibleInScrollView } from 'resource:///org/gnome/shell/misc/animationUtils.js';
import { gettext as _ } from 'resource:///org/gnome/shell/extensions/extension.js';

const COLUMNS = 5;
const ICON_SIZE = 48;
// Keep in sync with the left + right padding of .sl-apps in stylesheet.css.
const SIDE_PADDING = 32;

// Chip order as shown.
const CHIPS = [
  ['productivity', () => _('Productivity & Finance')],
  ['utilities', () => _('Utilities')],
  ['social', () => _('Social')],
  ['creativity', () => _('Creativity')],
  ['entertainment', () => _('Entertainment')],
  ['developer', () => _('Developer Tools')],
  ['other', () => _('Other')],
];

// Matching priority: the first rule with a matching freedesktop category
// wins, so a terminal lands in Developer Tools, not Utilities.
const RULES = [
  ['developer', ['Development', 'IDE', 'Building', 'Debugger', 'RevisionControl', 'TerminalEmulator']],
  ['productivity', ['Office', 'Finance', 'Calendar', 'ProjectManagement', 'ContactManagement', 'Dictionary']],
  ['social', ['Network', 'Chat', 'Email', 'InstantMessaging', 'WebBrowser', 'Feed', 'News']],
  ['creativity', ['Graphics', '2DGraphics', '3DGraphics', 'Photography', 'AudioVideoEditing', 'Publishing', 'Recorder']],
  ['entertainment', ['Game', 'AudioVideo', 'Video', 'Audio', 'Player', 'Music', 'TV']],
  ['utilities', ['Utility', 'System', 'Settings', 'FileManager', 'Accessibility', 'Archiving', 'Monitor', 'Security']],
];

export function categorize(categoriesString) {
  const cats = new Set((categoriesString || '').split(';').filter((c) => c));
  for (const [key, names] of RULES) {
    if (names.some((n) => cats.has(n))) return key;
  }
  return 'other';
}

function appCategory(app) {
  try {
    const info = app.get_app_info();
    return categorize(info?.get_categories?.());
  } catch (err) {
    return 'other';
  }
}

export const AppsView = GObject.registerClass(
  {},
  class AppsView extends St.BoxLayout {
    /**
     * @param {object} params
     * @param {function(Shell.App)} params.onLaunch - an app tile was activated
     * @param {function()} params.onFocusEntry - focus should go back to the entry
     * @param {function(string)} params.onType - text typed while a tile had focus
     */
    _init(params) {
      super._init({
        name: 'searchLightApps',
        style_class: 'sl-apps',
        orientation: Clutter.Orientation.VERTICAL,
        x_expand: true,
        y_expand: true,
      });
      this._onLaunch = params.onLaunch;
      this._onFocusEntry = params.onFocusEntry;
      this._onType = params.onType;

      this._filter = null;
      this._tileWidth = 100;
      this._apps = [];
      this._gridTilesAll = [];
      this._gridTiles = [];
      this._dirty = true;
      this._collator = new Intl.Collator(undefined, {
        sensitivity: 'base',
        numeric: true,
      });

      this._chipsBox = new St.BoxLayout({
        style_class: 'sl-apps-chips',
        x_align: Clutter.ActorAlign.CENTER,
      });
      this.add_child(this._chipsBox);
      this._chips = new Map();
      for (const [key, label] of CHIPS) {
        const chip = new St.Button({
          style_class: 'sl-apps-chip',
          can_focus: false,
          track_hover: true,
          child: new St.Label({
            style_class: 'sl-apps-chip-label',
            text: label(),
            y_align: Clutter.ActorAlign.CENTER,
          }),
        });
        chip.connect('clicked', () => this._onChipClicked(key));
        this._chipsBox.add_child(chip);
        this._chips.set(key, chip);
      }

      this._gridBox = new St.BoxLayout({
        style_class: 'sl-apps-grid',
        orientation: Clutter.Orientation.VERTICAL,
        x_expand: true,
      });
      this._scroll = new St.ScrollView({
        style_class: 'sl-apps-scroll vfade',
        hscrollbar_policy: St.PolicyType.NEVER,
        vscrollbar_policy: St.PolicyType.AUTOMATIC,
        overlay_scrollbars: true,
        x_expand: true,
        y_expand: true,
      });
      this._scroll.set_child(this._gridBox);
      this.add_child(this._scroll);

      Shell.AppSystem.get_default().connectObject(
        'installed-changed',
        () => {
          this._dirty = true;
        },
        this,
      );
      this.connect('destroy', () => this._onDestroy());
    }

    /**
     * Rebuilds what is needed before the view is shown. Resets the chip
     * filter and the scroll position.
     *
     * @param {number} panelWidth - width of the Search Light panel
     */
    prepare(panelWidth) {
      const tileWidth = Math.max(
        64,
        Math.floor((panelWidth - SIDE_PADDING) / COLUMNS),
      );
      if (tileWidth !== this._tileWidth) {
        this._tileWidth = tileWidth;
        this._dirty = true;
      }
      if (this._dirty) this._rebuildApps();
      this._filter = null;
      this._applyFilter();
      this._scroll.vadjustment.value = 0;
    }

    _rebuildApps() {
      this._dirty = false;
      this._gridTilesAll.forEach((t) => t.destroy());
      this._gridTilesAll = [];

      const appSystem = Shell.AppSystem.get_default();
      const seen = new Set();
      const apps = [];
      for (const info of appSystem.get_installed()) {
        let id;
        try {
          if (!info.should_show()) continue;
          id = info.get_id();
        } catch (err) {
          continue; // invalid file encodings
        }
        if (!id || seen.has(id)) continue;
        const app = appSystem.lookup_app(id);
        if (!app) continue;
        seen.add(id);
        apps.push({ app, name: app.get_name() || id, category: appCategory(app) });
      }
      apps.sort((a, b) => this._collator.compare(a.name, b.name));
      this._apps = apps;

      for (const entry of apps) {
        const tile = this._createTile(entry.app);
        tile._slCategory = entry.category;
        this._gridTilesAll.push(tile);
      }

      for (const [key, chip] of this._chips) {
        chip.visible = apps.some((a) => a.category === key);
      }
    }

    _createTile(app) {
      const icon = app.create_icon_texture(ICON_SIZE);
      icon.add_style_class_name('sl-app-tile-icon');
      icon.x_align = Clutter.ActorAlign.CENTER;

      const label = new St.Label({
        style_class: 'sl-app-tile-label',
        text: app.get_name() || '',
        x_align: Clutter.ActorAlign.CENTER,
        x_expand: true,
      });
      label.clutter_text.ellipsize = Pango.EllipsizeMode.END;

      const box = new St.BoxLayout({
        style_class: 'sl-app-tile-box',
        orientation: Clutter.Orientation.VERTICAL,
        x_expand: true,
      });
      box.add_child(icon);
      box.add_child(label);

      const tile = new St.Button({
        style_class: 'sl-app-tile',
        child: box,
        can_focus: true,
        reactive: true,
        track_hover: true,
        width: this._tileWidth,
        x_align: Clutter.ActorAlign.START,
        accessible_name: app.get_name() || '',
      });
      tile._slApp = app;
      tile._slIndex = 0;
      tile.connect('clicked', () => this._onLaunch(app));
      tile.connect('key-press-event', (actor, event) =>
        this._onTileKeyPress(tile, event),
      );
      tile.connect('key-focus-in', () => {
        try {
          ensureActorVisibleInScrollView(this._scroll, tile);
        } catch (err) {
          // not allocated yet
        }
      });
      return tile;
    }

    _onChipClicked(key) {
      // Chip clicks arrive from a click gesture; rebuilding the grid while it
      // is still dispatching is what GNOME 50+ aborts on, so do it from idle.
      this._filter = this._filter === key ? null : key;
      if (this._chipIdle) return;
      this._chipIdle = GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
        this._chipIdle = 0;
        this._applyFilter();
        this._scroll.vadjustment.value = 0;
        return GLib.SOURCE_REMOVE;
      });
    }

    _applyFilter() {
      // A focused tile that gets unparented would drop key focus to the
      // stage, which closes Search Light; hand focus to the entry first.
      const focus = global.stage.get_key_focus();
      if (focus && this.contains(focus)) this._onFocusEntry();

      for (const [key, chip] of this._chips) {
        if (key === this._filter) chip.add_style_pseudo_class('checked');
        else chip.remove_style_pseudo_class('checked');
      }

      // detach tiles from the old rows without destroying them
      for (const row of this._gridBox.get_children()) {
        for (const tile of row.get_children()) row.remove_child(tile);
        row.destroy();
      }

      this._gridTiles = this._gridTilesAll.filter(
        (t) => this._filter === null || t._slCategory === this._filter,
      );
      let row = null;
      this._gridTiles.forEach((tile, i) => {
        tile._slIndex = i;
        if (i % COLUMNS === 0) {
          row = new St.BoxLayout({ style_class: 'sl-apps-row' });
          this._gridBox.add_child(row);
        }
        row.add_child(tile);
      });
    }

    get hasTiles() {
      return this._gridTiles.length > 0;
    }

    /** Moves key focus to the first tile (Down from the entry). */
    focusFirst() {
      const first = this._gridTiles[0];
      if (!first) return false;
      first.grab_key_focus();
      return true;
    }

    _onTileKeyPress(tile, event) {
      const symbol = event.get_key_symbol();
      const i = tile._slIndex;
      const grid = this._gridTiles;
      let target = null;

      switch (symbol) {
        case Clutter.KEY_Left:
          target = grid[i - 1] ?? null;
          break;
        case Clutter.KEY_Right:
          target = grid[i + 1] ?? null;
          break;
        case Clutter.KEY_Up:
          if (i - COLUMNS >= 0) {
            target = grid[i - COLUMNS];
          } else {
            this._onFocusEntry();
          }
          break;
        case Clutter.KEY_Down:
          if (i + COLUMNS < grid.length) {
            target = grid[i + COLUMNS];
          } else if (
            Math.floor((grid.length - 1) / COLUMNS) > Math.floor(i / COLUMNS)
          ) {
            target = grid[grid.length - 1];
          }
          break;
        case Clutter.KEY_BackSpace:
          this._onFocusEntry();
          break;
        case Clutter.KEY_Return:
        case Clutter.KEY_KP_Enter:
        case Clutter.KEY_ISO_Enter:
          this._onLaunch(tile._slApp);
          break;
        case Clutter.KEY_Escape:
        case Clutter.KEY_Tab:
        case Clutter.KEY_ISO_Left_Tab:
          return Clutter.EVENT_PROPAGATE;
        default: {
          const mods = event.get_state();
          if (
            mods &
            (Clutter.ModifierType.CONTROL_MASK |
              Clutter.ModifierType.MOD1_MASK |
              Clutter.ModifierType.SUPER_MASK)
          )
            return Clutter.EVENT_PROPAGATE;
          const ch = event.get_key_unicode();
          if (ch && ch !== '\0' && ch !== ' ' && GLib.unichar_isprint(ch)) {
            this._onType(ch);
            return Clutter.EVENT_STOP;
          }
          return Clutter.EVENT_PROPAGATE;
        }
      }
      if (target) target.grab_key_focus();
      return Clutter.EVENT_STOP;
    }

    _onDestroy() {
      // _gridTilesAll may hold tiles that are not parented right now
      this._gridTilesAll.forEach((t) => t.destroy());
      this._gridTilesAll = [];
      if (this._chipIdle) {
        GLib.source_remove(this._chipIdle);
        this._chipIdle = 0;
      }
    }
  },
);
