/* extension.js
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 */

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as DND from 'resource:///org/gnome/shell/ui/dnd.js';
import Atk from 'gi://Atk';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Clutter from 'gi://Clutter';
import St from 'gi://St';
import Graphene from 'gi://Graphene';

import { Timer } from './timer.js';
import { Style } from './style.js';

import { TintEffect } from './effects/tint_effect.js';
import { MonochromeEffect } from './effects/monochrome_effect.js';
import { BlurEffect } from './effects/blur_effect.js';

import { schemaId, SettingsKeys } from './preferences/keys.js';
import { KeyboardShortcuts } from './keybinding.js';
import { AppsView } from './appsView.js';

import {
  Extension,
  gettext as _,
} from 'resource:///org/gnome/shell/extensions/extension.js';

// Frosted background (blur-background): while the panel is shown, what lies
// behind it (windows and wallpaper) is blurred live by a Shell.BlurEffect in
// BACKGROUND mode on an actor under the panel's content, with a tint on top
// dark (or, for the light variant, light) enough to keep the labels readable
// over a bright, busy window.
//
// The blur reads the panel's whole box from the frame being drawn, but Mutter
// redraws only the damaged part of the screen; outside that part the
// framebuffer still holds last frame's already blurred, tinted panel, so a
// partial redraw shows lighter patches with hard seams (hovering a tile,
// typing, scrolling, a window behind the panel updating). Clutter queues a
// redraw of every clone of an actor when anything inside it is damaged, and
// redraws a clone whole, in the same frame. Two invisible clones (opacity 0,
// never painted, not reactive) therefore put the panel's whole box into any
// redraw that touches it: one of the panel itself, laid over the panel, and
// one of the window group (windows and wallpaper), scaled down onto the
// panel's box. Nothing runs while nothing changes.
//
// Known limits: Shell.BlurEffect has no rounded corners, so with a border
// radius the frost stays square while the tint is rounded; something drawn
// above the panel that is not in it (a notification banner sliding over it)
// is not covered by the clones.
const FROST_NAME = 'searchLightFrost';
// Shell.BlurEffect took a radius instead of a sigma in GNOME 46; the radius
// is twice the sigma (as GNOME's own lock screen and Blur my Shell convert).
const SIGMA_TO_RADIUS = 2;
// Largest background value (sRGB, 0..1) left behind light labels: white
// labels stay at 4.5:1 or better even on a focused tile (+20 % white) over a
// white window. Smallest one behind dark labels (light variant): black labels
// stay at 4.5:1 on a pressed tile (12 % black) over a black window.
const FROST_MAX_DARK_BG = 0.33;
const FROST_MIN_LIGHT_BG = 0.53;
const FROST_MAX_TINT_ALPHA = 0.9;

var SearchLight = GObject.registerClass(
  {},
  class SearchLight extends St.Widget {
    _init() {
      super._init();
      this.name = 'searchLight';
      this.offscreen_redirect = Clutter.OffscreenRedirect.ALWAYS;
      this.layout_manager = new Clutter.BinLayout();
    }
  },
);

export default class SearchLightExt extends Extension {
  enable() {
    Main.overview.graphene = Graphene;
    
    this._style = new Style();

    this._hiTimer = new Timer('hi-res timer');
    this._hiTimer.initialize(15);

    // for deferred or debounced runs
    this._loTimer = new Timer('lo-res timer');
    this._loTimer.initialize(750);

    this._settings = this.getSettings(schemaId);
    this._settingsKeys = SettingsKeys();

    this._settingsKeys.connectSettings(this._settings, (name, value) => {
      let n = name.replace(/-/g, '_');
      this[n] = value;
      switch (name) {
        case 'show-panel-icon':
          if (this._indicator) {
            this._indicator.visible = value;
          }
          break;
        case 'background-color':
        case 'panel-icon-color':
          this._updateCss();
          break;
        case 'blur-background':
          this._updateCss();
          this._syncFrost();
          break;
        case 'blur-sigma':
        case 'blur-brightness':
          this._updateFrostEffect();
          this._updateCss();
          break;
        case 'use-animations':
          this._useAnimations = value;
          break;
        case 'animation-speed':
          this._animationSpeed = value;
          break;
        case 'border-radius':
          break;
        case 'shortcut-search':
          this._updateShortcut();
          break;
        case 'secondary-shortcut-search':
          this._updateShortcut2();
          break;
        case 'window-effect': {
          this._updateWindowEffect();
          break;
        }
        case 'window-effect-color': {
          if (this.windowEffect) {
            this.windowEffect.color = this.window_effect_color;
          }
          break;
        }
      }
    });
    Object.keys(this._settingsKeys._keys).forEach((k) => {
      let key = this._settingsKeys.getKey(k);
      let name = k.replace(/-/g, '_');
      this[name] = key.value;
      if (key.options) {
        this[`${name}_options`] = key.options;
      }
      // console.log(`${name} ${key.value}`);
    });

    this.mainContainer = new SearchLight();
    this.mainContainer._delegate = this;
    this.container = new St.BoxLayout({
      name: 'searchLightBox',
      orientation: Clutter.Orientation.VERTICAL,
      reactive: true,
      track_hover: true,
      can_focus: true,
    });

    this.hide();
    this.container._delegate = this;

    Main.layoutManager.addChrome(this.mainContainer, {
      affectsStruts: false,
      trackFullscreen: false,
    });

    this.mainContainer.add_child(this.container);

    // Applications view shown under the entry while the query is empty.
    // Added to the container by _acquire_ui(), after the entry and results.
    this._appsView = new AppsView({
      onLaunch: (app) => this._launchApp(app),
      onFocusEntry: () => this._entry?.grab_key_focus(),
      onType: (text) => this._typeIntoEntry(text),
    });

    // Down from the entry moves into the Applications view. This runs in the
    // capture phase on the panel, ahead of the search controller's own
    // capture handler on the entry, which (with the search still marked
    // active after a cleared query) would steer Down into the hidden results.
    this._appsKeyController = new Clutter.KeyController();
    this._appsKeyController.connect('key-press', () => {
      const [, symbol] = this._appsKeyController.get_key();
      if (
        symbol === Clutter.KEY_Down &&
        this._entry &&
        this._appsView?.visible &&
        global.stage.get_key_focus() === this._entry.clutter_text &&
        this._appsView.focusFirst()
      ) {
        return Clutter.EVENT_STOP;
      }
      return Clutter.EVENT_PROPAGATE;
    });
    this.container.add_action_full(
      'search-light-apps-keys',
      Clutter.EventPhase.CAPTURE,
      this._appsKeyController,
    );

    this.accel = new KeyboardShortcuts();
    this.accel.enable();
    this.accel2 = new KeyboardShortcuts();
    this.accel2.enable();

    this._updateShortcut();
    this._updateShortcut2();
    this._updateCss();

    this._useAnimations = this._settings.get_boolean('use-animations');
    this._animationSpeed = this._settings.get_double('animation-speed');

    Main.overview.connectObject(
      'overview-showing',
      this._onOverviewShowing.bind(this),
      'overview-hidden',
      this._onOverviewHidden.bind(this),
      this,
    );

    Shell.AppSystem.get_default().connectObject(
      'app-state-changed',
      this._onAppStateChanged.bind(this),
      this,
    );

    global.display.connectObject(
      'window-created',
      (display, win) => {
        if (this._visible) {
          this.mainContainer.opacity = 0;
        }
      },
      this,
    );

    this._loTimer.runOnce(() => {
      // this.show();
    }, 500);

    Main.overview.searchLight = this;

    let appInfo = Gio.DesktopAppInfo.new_from_filename(
      `${this.path}/apps/org.gnome.Calculator.desktop`,
    );

    let _providers = [];

    // deferred startup for providers
    let idx = 0;
    _providers.forEach((p) => {
      this._loTimer.runOnce(() => {
        p.initialize();
      }, idx * 5000);
    });

    this._loTimer.runOnce(() => {
      this._createIndicator();
    }, 1500);
    this._updateProviders();
    this._updateWindowEffect();
  }

  disable() {
    // Disabled while shown: give the overview its search entry back and drop
    // the stage/display handlers, which would otherwise queue a hide after
    // disable() has run.
    if (this._entry) {
      this._release_ui();
      global.compositor.enable_unredirect();
    }
    this._remove_events();
    this._cancelDeferred();
    this._hiTimer?.shutdown();
    this._loTimer?.shutdown();
    this._hiTimer = null;
    this._loTimer = null;

    if (this._indicator) {
      this._indicator.disconnectObject(this);
      if (this._indicator.get_parent()) {
        this._indicator.get_parent().remove_child(this._indicator);
      }
      this._indicator = null;
    }

    this._style.unloadAll();
    this._style = null;

    this._settingsKeys.disconnectSettings();
    this._settings = null;

    if (this.accel) {
      this.accel.disable();
      delete this.accel;
      this.accel = null;
    }
    if (this.accel2) {
      this.accel2.disable();
      delete this.accel2;
      this.accel2 = null;
    }

    this._removeProviders();
    this._providers = null;

    if (this._appsKeyController) {
      this.container.remove_action(this._appsKeyController);
      this._appsKeyController = null;
    }
    if (this._appsView) {
      this._appsView.destroy();
      this._appsView = null;
    }

    this._destroyFrost();

    Main.layoutManager.removeChrome(this.mainContainer);
    this.mainContainer = null;
  }

  _createIndicator() {
    if (this._indicator) return;
    this._indicator = new St.Button({
      style_class: 'panel-status-indicators-box',
    });
    let icon = new St.Icon({
      style_class: 'panel-status-indicator-icon',
      gicon: new Gio.ThemedIcon({ name: 'search-symbolic' }),
    });
    icon.style = 'margin-top: 6px !important; margin-bottom: 6px !important;';
    this._indicator.set_child(icon);
    this._indicator.connectObject(
      'button-press-event',
      this._queueToggle.bind(this),
      this,
    );
    try {
      Main.panel._rightBox.insert_child_at_index(this._indicator, 0);
      this._indicator.visible = this.show_panel_icon;
    } catch (err) {
      console.log(err);
    }
  }

  _createEffect(idx) {
    let effect = null;
    switch (idx) {
      case 1: {
        effect = new TintEffect({
          name: 'color',
          color: this.window_effect_color,
        });
        effect.preload(this.path);
        break;
      }
      case 2: {
        effect = new MonochromeEffect({
          name: 'color',
          color: this.window_effect_color,
        });
        effect.preload(this.path);
        break;
      }
      case 3: {
        effect = new BlurEffect({
          name: 'color',
          color: this.window_effect_color,
        });
        effect.preload(this.path);
        break;
      }
    }
    return effect;
  }

  // Shows the frosted background while the panel is shown and the
  // blur-background setting is on, removes it otherwise.
  _syncFrost() {
    if (this.blur_background && this._visible && this._entry) {
      this._createFrost();
    } else {
      this._destroyFrost();
    }
  }

  _createFrost() {
    if (this._frost) return;

    this._frostBlur = new Shell.BlurEffect({
      mode: Shell.BlurMode.BACKGROUND,
    });
    this._frost = new St.Widget({
      name: FROST_NAME,
      x_expand: true,
      y_expand: true,
      reactive: false,
      accessible_role: Atk.Role.REDUNDANT_OBJECT,
    });
    this._frost.add_effect_with_name('blur', this._frostBlur);
    this._updateFrostEffect();
    this._frost.style = this._frostStyle || '';
    // Under the panel's content. The BACKGROUND blur reads the framebuffer
    // it is drawn into: with the panel redirected offscreen that would be the
    // panel's own (empty) buffer, so the panel is drawn straight to the
    // screen while the frost is up.
    this.mainContainer.offscreen_redirect = 0;
    this.mainContainer.insert_child_at_index(this._frost, 0);

    // The two damage clones (see the comment at the top of this file).
    const uiGroup = this.mainContainer.get_parent();
    this._frostClones = [this.mainContainer, global.window_group].map(
      (source) => {
        const clone = new Clutter.Clone({
          source,
          opacity: 0,
          reactive: false,
          // Exposed for technical reasons only: screen readers skip it.
          accessible_role: Atk.Role.REDUNDANT_OBJECT,
        });
        clone.add_constraint(
          new Clutter.BindConstraint({
            source: this.mainContainer,
            coordinate: Clutter.BindCoordinate.ALL,
          }),
        );
        uiGroup.insert_child_below(clone, this.mainContainer);
        return clone;
      },
    );
  }

  _destroyFrost() {
    for (const clone of this._frostClones || []) {
      clone.destroy();
    }
    this._frostClones = null;
    if (this._frost) {
      this._frost.destroy();
      this._frost = null;
    }
    this._frostBlur = null;
    if (this.mainContainer) {
      this.mainContainer.offscreen_redirect = Clutter.OffscreenRedirect.ALWAYS;
    }
  }

  _updateFrostEffect() {
    if (!this._frostBlur) return;
    const sigma = Math.max(0, this.blur_sigma ?? 30);
    this._frostBlur.radius = Math.round(sigma * SIGMA_TO_RADIUS);
    this._frostBlur.brightness = this._frostBrightness();
  }

  _frostBrightness() {
    return Math.min(1, Math.max(0, this.blur_brightness ?? 0.6));
  }

  // The tint over the blur: the panel's background colour, at least as
  // opaque as needed to keep the labels readable whatever lies behind (the
  // worst case: a white window behind light labels, a black one behind dark
  // labels).
  _frostTint(bg, light) {
    let [r, g, b, a] = bg;
    let need = 0;
    if (light) {
      const c = Math.min(r, g, b);
      need = c > 0 ? FROST_MIN_LIGHT_BG / c : FROST_MAX_TINT_ALPHA;
    } else {
      const c = Math.max(r, g, b);
      const brightest = this._frostBrightness();
      if (brightest > FROST_MAX_DARK_BG) {
        need =
          c < FROST_MAX_DARK_BG
            ? (brightest - FROST_MAX_DARK_BG) / (brightest - c)
            : FROST_MAX_TINT_ALPHA;
      }
    }
    a = Math.min(FROST_MAX_TINT_ALPHA, Math.max(a, need));
    return [r, g, b, a];
  }

  _updateWindowEffect() {
    // this.window_effect = 2;
    // this.window_effect_color = [1, 0, 0, 0.5];
    this.container.remove_effect_by_name('window-effect');
    let effect = this._createEffect(this.window_effect);
    if (effect) {
      this.container.add_effect_with_name('window-effect', effect);
    }
    this.windowEffect = effect;
  }

  _updatePanelIcon(disable) {}

  _updateProviders() {
    this._removeProviders();
    this._providers = [];

    let _search = Main.overview.searchController;
    if (!_search) return;

    // add providers here

    if (_search.addProvider) {
      this._providers.forEach((p) => {
        _search.addProvider(p);
      });
    }
  }

  _removeProviders() {
    if (!this._providers) {
      return;
    }

    let _search = Main.overview.searchController;
    if (!_search) return;

    if (_search.removeProvider) {
      this._providers.forEach((p) => {
        _search.removeProvider(p);
      });
    }

    this._providers = null;
  }

  show() {
    if (Main.overview.visible) return;

    if (this._animSeq) {
      this._hiTimer.cancel(this._animSeq);
      this._animSeq = null;
    }
    this._acquire_ui();

    this._updateCss();
    this._layout();
    this._appsView.prepare(this.width);
    this._syncAppsView();
    this._syncFrost();

    global.compositor.disable_unredirect();

    this.mainContainer.show();
    this.container.show();
    this._add_events();

    // fixes the background size relative to text - after adjusting font size
    this._animSeq = this._hiTimer.runOnce(() => {
      this._animSeq = null;
      this._layout();
      // animate after adjust so width+height are correct
      if (this._useAnimations) {
        this.mainContainer.opacity = 0;
        this.mainContainer.scale_x = 0.9;
        this.mainContainer.scale_y = 0.9;
        this.mainContainer.translation_x = (this.width * 0.1) / 2;
        this.mainContainer.translation_y = (this.height * 0.1) / 2;
        this.mainContainer.ease({
          opacity: 255,
          scale_x: 1.0,
          scale_y: 1.0,
          translation_x: 0,
          translation_y: 0,
          duration: this._animationSpeed,
          mode: Clutter.AnimationMode.EASE_OUT,
        });
      } else {
        this.mainContainer.scale_x = 1.0;
        this.mainContainer.scale_y = 1.0;
        this.mainContainer.opacity = 255;
      }
    }, 100);
  }

  hide() {
    if (this._isDraggingIcon()) {
      return;
    }

    this._release_ui();
    this._remove_events();

    if (this._useAnimations) {
      this.mainContainer.ease({
        opacity: 0,
        scale_x: 0.9,
        scale_y: 0.9,
        translation_x: (this.width * 0.1) / 2,
        translation_y: (this.height * 0.1) / 2,
        duration: this._animationSpeed,
        mode: Clutter.AnimationMode.EASE_OUT,
        onComplete: () => {
          this._visible = false;
          this.mainContainer.hide();
          global.compositor.enable_unredirect();
          this._syncFrost();
        },
      });
    } else {
      this.mainContainer.opacity = 0;
      this._visible = false;
      this.mainContainer.hide();
      this._syncFrost();
      global.compositor.enable_unredirect();
    }
    // this._hidePopups();
  }

  _isDraggingIcon() {
    // cancel all drag
    let result = false;
    try {
      if (this._searchResults) {
        let grid =
          this._searchResults._content.first_child.first_child.child.child;
        if (grid.style_class == 'grid-search-results') {
          grid.get_children().forEach((c) => {
            // console.log(`${c._name} ${c._draggable._dragState}`);
            if (
              c._draggable &&
              c._draggable._dragState == 1 /* DragState.DRAGGING */
            ) {
              result = true;
            }
          });
        }
      }
    } catch (err) {
      console.log(err);
    }
    return result;
  }

  _layout() {
    this._queryDisplay();
    if (!this.monitor) return;

    // container size
    this.width =
      600 + ((this.sw * this.scaleFactor) / 2) * (this.scale_width || 0);
    this.height =
      400 + ((this.sh * this.scaleFactor) / 2) * (this.scale_height || 0);

    // initial height
    let font_size = 14;
    if (this.font_size) {
      font_size = this.font_size_options[this.font_size];
    }
    if (this.entry_font_size) {
      font_size = this.entry_font_size_options[this.entry_font_size];
    }

    // let padding = {
    //   14: 14 * 2.5,
    //   16: 16 * 2.4,
    //   18: 18 * 2.2,
    //   20: 20 * 2.0,
    //   22: 22 * 1.8,
    //   24: 24 * 1.6,
    // };
    // this.initial_height = padding[font_size] * this.scaleFactor;
    // this.initial_height += font_size * 2 * this.scaleFactor;
    // console.log(`${this.initial_height} ${this._entry.height}`);

    this.initial_height = this._entry.height + 4 * this.scaleFactor;

    // position
    let x = this.monitor.x + this.sw / 2 - this.width / 2;
    let y = this.monitor.y + this.sh / 2 - this.height / 2;
    this._visible = true;

    // The Applications view fills the panel from the start, so the panel no
    // longer opens at entry height and grows on the first keystroke.
    let height = this._appsView ? this.height : this.initial_height;
    this.container.set_size(this.width, height);
    this.mainContainer.set_size(this.width, height);
    this.mainContainer.set_position(x, y);
  }

  _updateShortcut(disable) {
    this.accel.unlisten();

    let shortcut = '';
    try {
      shortcut = (this.shortcut_search || []).join('');
    } catch (err) {
      //
    }
    if (shortcut == '') {
      shortcut = '<Control><Super>Space';
    }

    if (!disable) {
      this.accel.listenFor(shortcut, this._queueToggle.bind(this));
    }
  }

  _updateShortcut2(disable) {
    this.accel2.unlisten();

    let shortcut = '';
    try {
      shortcut = (this.secondary_shortcut_search || []).join('');
    } catch (err) {
      //
    }
    if (shortcut == '') {
      shortcut = '<Control><Super>Space';
    }

    if (!disable) {
      this.accel2.listenFor(shortcut, this._queueToggle.bind(this));
    }
  }

  _queryDisplay() {
    let idx = this.preferred_monitor || 0;
    if (idx == 0) {
      idx = Main.layoutManager.primaryIndex;
    } else if (idx == Main.layoutManager.primaryIndex) {
      idx = 0;
    }
    this.monitor =
      Main.layoutManager.monitors[idx] || Main.layoutManager.primaryMonitor;

    if (this.popup_at_cursor_monitor) {
      let pointer = global.get_pointer();
      Main.layoutManager.monitors.forEach((m) => {
        if (
          pointer[0] >= m.x &&
          pointer[0] <= m.x + m.width &&
          pointer[1] >= m.y &&
          pointer[1] <= m.y + m.height
        ) {
          this.monitor = m;
        }
      });
    }

    this.sw = this.monitor.width;
    this.sh = this.monitor.height;

    if (this._last_monitor_count != Main.layoutManager.monitors.length) {
      this._settings.set_int(
        'monitor-count',
        Main.layoutManager.monitors.length,
      );
      this._last_monitor_count = Main.layoutManager.monitors.length;
    }
  }

  _acquire_ui() {
    if (this._entry) return;

    if (!Main.overview._toggle) {
      Main.overview._toggle = Main.overview.toggle;
    }
    Main.overview.toggle = () => {
      if (this._search && this._search.visible) {
        this._search._text.get_parent().grab_key_focus();
      }
    };
    if (!Main.overview._hide) {
      Main.overview._hide = Main.overview.hide;
    }
    Main.overview.hide = () => {
      this.mainContainer.opacity = 0;
      Main.overview._hide();
    };

    this._queryDisplay();

    this.scaleFactor = St.ThemeContext.get_for_stage(global.stage).scale_factor;

    this._entry = Main.overview.searchEntry;
    this._entryParent = this._entry.get_parent();
    this._entry.add_style_class_name('slc');

    this._search = Main.overview.searchController;

    this._search.hide();
    this._searchResults = this._search._searchResults;
    this._searchParent = this._search.get_parent();

    if (!this._searchResults._activateDefault) {
      this._searchResults._activateDefault =
        this._searchResults.activateDefault;
    }
    this._searchResults.activateDefault = () => {
      // Enter on an empty query: nothing to activate, keep the panel visible
      if (this._appsView?.visible) return;
      // hide window immediately when activated
      this.mainContainer.opacity = 0;
      this._searchResults._activateDefault();
    };

    if (this._entry.get_parent()) {
      this._entry.get_parent().remove_child(this._entry);
    }
    this.container.add_child(this._entry);
    if (this._search.get_parent()) {
      this._search.get_parent().remove_child(this._search);
    }
    this.container.add_child(this._search);
    if (this._appsView.get_parent()) {
      this._appsView.get_parent().remove_child(this._appsView);
    }
    this.container.add_child(this._appsView);
    if (!this._search.__searchCancelled) {
      this._search.__searchCancelled = this._search._searchCancelled;
      this._search._searchCancelled = () => {};
    }
    // The search controller resets the (empty) search when a click lands
    // outside the entry, which drops key focus and closes Search Light; let
    // clicks on the Applications view (chips, tiles) through.
    if (!this._search.__maybeCancelSearch) {
      this._search.__maybeCancelSearch = this._search._maybeCancelSearch;
      const search = this._search;
      const appsView = this._appsView;
      this._search._maybeCancelSearch = function () {
        try {
          const event = this._clickGesture.get_point_event(0);
          const target = global.stage.get_event_actor(event);
          if (target && appsView.contains(target)) return false;
        } catch (err) {
          console.log(err);
        }
        return search.__maybeCancelSearch.call(this);
      };
    }
    this._savedHintText = this._entry.hint_text;
    let primaryIcon = this._entry.get_primary_icon();
    this._savedPrimaryIconName =
      primaryIcon instanceof St.Icon ? primaryIcon.icon_name : null;
    this._search._text.get_parent().grab_key_focus();
    this._textChangedEventId = this._search._text.connect(
      'text-changed',
      () => {
        this.container.set_size(this.width, this.height);
        this.mainContainer.set_size(this.width, this.height);
        if (this._corners) {
          this._corners[2].y = this.height - this._corners[1].height;
          this._corners[3].y = this.height - this._corners[1].height;
          this._edges[3].y = this.height - 2;
        }
        this._syncAppsView();
      },
    );

    this._search._text.get_parent().grab_key_focus();
  }

  _release_ui() {
    if (this._appsView && this._appsView.get_parent()) {
      this._appsView.get_parent().remove_child(this._appsView);
    }
    if (this._search) {
      this._searchResults.visible = true;
      this._search.y_expand = true;
    }
    this._restoreEntryLook();

    if (this._entry) {
      if (this._entry.get_parent()) {
        this._entry.get_parent().remove_child(this._entry);
      }
      this._entryParent.add_child(this._entry);
      this._entry = null;
    }

    if (this._search) {
      this._removeProviders();
      this._search.hide();
      if (this._search.get_parent()) {
        this._search.get_parent().remove_child(this._search);
      }
      this._searchParent.add_child(this._search);
      if (this._textChangedEventId) {
        this._search._text.disconnect(this._textChangedEventId);
        this._textChangedEventId = null;
      }
      if (this._search.__maybeCancelSearch) {
        this._search._maybeCancelSearch = this._search.__maybeCancelSearch;
        this._search.__maybeCancelSearch = null;
      }
      if (this._search.__searchCancelled) {
        this._search._searchCancelled = this._search.__searchCancelled;
        this._search.__searchCancelled = null;
      }
      this._search = null;

      if (this._searchResults._activateDefault) {
        this._searchResults.activateDefault =
          this._searchResults._activateDefault;
        this._searchResults._activateDefault = null;
      }
    }

    if (Main.overview._toggle) {
      Main.overview.toggle = Main.overview._toggle;
      Main.overview._toggle = null;
    }
    if (Main.overview._hide) {
      Main.overview.hide = Main.overview._hide;
      Main.overview._hide = null;
    }
  }

  // Shows the Applications view while the query is empty, the normal search
  // results otherwise. The entry shows "Applications" and an apps icon while
  // the view is up.
  _syncAppsView() {
    if (!this._entry || !this._search || !this._appsView) return;
    let empty = this._search._text.text === '';
    this._appsView.visible = empty;
    // Hide the results, not the search controller: unmapping the controller
    // resets the search, which drops key focus and closes Search Light.
    this._search.show();
    this._searchResults.visible = !empty;
    this._search.y_expand = !empty;
    if (empty) {
      this._entry.hint_text = _('Applications');
      this._setEntryIconName('view-app-grid-symbolic');
    } else {
      this._restoreEntryLook();
    }
  }

  _setEntryIconName(name) {
    let icon = this._entry?.get_primary_icon();
    if (name && icon instanceof St.Icon) icon.icon_name = name;
  }

  _restoreEntryLook() {
    if (!this._entry) return;
    if (this._savedHintText !== undefined) {
      this._entry.hint_text = this._savedHintText;
    }
    this._setEntryIconName(this._savedPrimaryIconName);
  }

  _launchApp(app) {
    // Clicks arrive from a gesture; reparenting the entry (hide) while it is
    // dispatching aborts GNOME 50+, so launch from idle like show/hide.
    this._defer('launch', () => {
      if (this._entry) {
        this.mainContainer.opacity = 0;
        this.hide();
      }
      app.activate();
    });
  }

  _typeIntoEntry(text) {
    if (!this._entry) return;
    this._entry.grab_key_focus();
    let clutterText = this._entry.clutter_text;
    clutterText.insert_text(text, clutterText.get_cursor_position());
  }

  _updateCss(disable) {
    let bg = this.background_color || [0, 0, 0, 0.5];
    if (this.text_color && this.text_color[3] > 0) {
      this.container.remove_style_class_name('light');
    } else {
      if (0.3 * bg[0] + 0.59 * bg[1] + 0.11 * bg[2] < 0.5) {
        this.container.remove_style_class_name('light');
      } else {
        this.container.add_style_class_name('light');
      }
    }

    // Over the frost the tint goes on the frost; without it the panel draws
    // the background colour itself, as before.
    let frosted = !!this.blur_background;
    let tint = frosted
      ? this._frostTint(bg, this.container.has_style_class_name('light'))
      : bg;

    let styles = [];
    {
      let ss = [];

      if (!frosted) {
        let clr = this._style.rgba(this.background_color);
        ss.push(`\n  background: rgba(${clr});`);
      }

      if (this.border_thickness) {
        let clr = this._style.rgba(this.border_color);
        ss.push(`\n  border: ${this.border_thickness}px solid rgba(${clr});`);
      }

      styles.push(`#searchLight {${ss.join(' ')}}`);
    }

    {
      let r = 0;
      if (this.border_radius !== null) {
        let rads = [0, 16, 18, 20, 22, 24, 28, 32];
        r = rads[Math.floor(this.border_radius)] || 0;
      }
      // Not Style.rgba(): it rounds the alpha to one decimal.
      let [tr, tg, tb] = tint.map((v) => Math.round(255 * v));
      this._frostStyle = frosted
        ? `background-color: rgba(${tr},${tg},${tb},${tint[3].toFixed(3)}); border-radius: ${r}px;`
        : '';
      if (this._frost) this._frost.style = this._frostStyle;
    }

    {
      if (this.border_radius !== null) {
        let rads = [0, 16, 18, 20, 22, 24, 28, 32];
        let r = rads[Math.floor(this.border_radius)];
        if (r) {
          let st = `StBoxLayout.search-section-content { border-radius: ${r}px !important; }`;
          st = '#searchLightBox,\n' + st;
          st = '#searchLight,\n' + st;
          styles.push(st);
        }
      }
    }

    if (this.font_size !== null) {
      let f = this.font_size_options[this.font_size];
      if (f) {
        styles.push(`#searchLightBox * { font-size: ${f}pt !important; }`);
      }
      f = this.entry_font_size_options[this.entry_font_size];
      if (f) {
        styles.push(
          `#searchLightBox > StEntry, #searchLightBox > StEntry:focus { font-size: ${f}pt !important; }`,
        );
      }
    }

    let clr = this._style.rgba(this.text_color);
    if ((this.text_color || [1, 1, 1, 1])[3] > 0) {
      styles.push(`#searchLightBox * { color: rgba(${clr}) !important }`);
    } else {
      styles.push('/* empty */');
    }

    // icon color
    {
      let ss = [];
      {
        let clr = this._style.rgba(this.panel_icon_color);
        if (this.panel_icon_color[3] > 0) {
          ss.push(`\n  color: rgba(${clr}) !important;`);
        }
      }
      styles.push(`.panel-status-indicator-icon {${ss.join(' ')}}`);
    }

    // console.log(styles);
    this._style.build('custom-search-light', styles);
  }

  // Local patch (crash fix, see https://github.com/icedman/search-light/issues/166):
  // GNOME 50 / Clutter 18 aborts the whole shell (e.g. clutter-gesture.c:544
  // set_state assertion) if the actor tree is changed — reparenting the
  // search entry, grabbing key focus — while an input event or gesture is
  // still being dispatched. Everything show()/hide() does from an input
  // handler (panel click, shortcut, Escape, focus loss, fullscreen) therefore
  // runs from an idle callback once dispatch has finished. Each kind of work
  // is queued at most once, and disable() removes anything still pending.
  _defer(name, func) {
    if (!this._deferred) this._deferred = {};
    if (this._deferred[name]) return;
    this._deferred[name] = GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
      delete this._deferred[name];
      func();
      return GLib.SOURCE_REMOVE;
    });
  }

  _cancelDeferred() {
    for (const id of Object.values(this._deferred || {})) {
      GLib.source_remove(id);
    }
    this._deferred = {};
  }

  _queueToggle() {
    this._defer('toggle', () => this._toggle_search_light());
    return Clutter.EVENT_STOP;
  }

  _queueHide() {
    // Nothing to do if an earlier hide() already released the UI.
    this._defer('hide', () => {
      if (this._entry) this.hide();
    });
  }

  _toggle_search_light() {
    if (this._inOverview) return;
    if (!this._visible) {
      this.show();
      if (this._entry) {
        global.stage.set_key_focus(this._entry);
      }
    } else {
      global.stage.set_key_focus(null);
    }
  }

  _add_events() {
    global.stage.connectObject(
      'notify::key-focus',
      this._onKeyFocusChanged.bind(this),
      'key-press-event',
      this._onKeyPressed.bind(this),
      this,
    );

    global.display.connectObject(
      'notify::focus-window',
      this._onFocusWindow.bind(this),
      'in-fullscreen-changed',
      this._onFullScreen.bind(this),
      this,
    );
  }

  _remove_events() {
    global.display.disconnectObject(this);
    global.stage.disconnectObject(this);
    Main.overview.disconnectObject(this);
    Shell.AppSystem.get_default().disconnectObject(this);
  }

  _onOverviewShowing() {
    this._inOverview = true;
  }

  _onOverviewHidden() {
    this._inOverview = false;
  }

  _onAppStateChanged(st) {
    this._lastAppState = st;
    if (this._visible) {
      this.mainContainer.opacity = 0;
    }
  }

  _hidePopups() {
    let popup = this._lastPopup;
    this._lastPopup = null;
    try {
      if (!popup.close && popup._getTopMenu()) {
        popup = popup._getTopMenu();
      }

      // elaborate way of hiding the popup
      popup.opacity = 0;
      this._startupSeq = this._hiTimer.runSequence([
        {
          func: () => {
            popup.opacity = 0;
          },
          delay: 0,
        },
        {
          func: () => {
            popup._delegate.close(false);
          },
          delay: 250,
        },
      ]);
    } catch (err) {
      console.log(err);
    }
  }

  _onFocusWindow(w, e) {}

  _onKeyFocusChanged(previous) {
    if (!this._entry) return;
    let focus = global.stage.get_key_focus();
    let appearFocused =
      focus &&
      (this._entry.contains(focus) ||
        this._searchResults.contains(focus) ||
        this._appsView?.contains(focus));

    if (!appearFocused) {
      // popups are not handled well.. hide immediately
      if (
        focus &&
        focus.style_class &&
        focus.style_class.includes('popup-menu')
      ) {
        this._lastPopup = focus;
        this._hidePopups();
      }

      this._queueHide();
    }

    // hide window immediately when activated
    if (focus && focus.activate) {
      if (!focus._activate) {
        focus._activate = focus.activate;
        focus.activate = () => {
          this.mainContainer.opacity = 0;
          focus._activate();
        };
      }
    }
  }

  _onKeyPressed(obj, evt) {
    if (!this._entry) return;
    let focus = global.stage.get_key_focus();
    if (!focus || !this._entry.contains(focus)) {
      if (evt.get_key_symbol() === Clutter.KEY_Escape) {
        this._queueHide();
        return Clutter.EVENT_STOP;
      }
      this._search._text.get_parent().grab_key_focus();
    }

    return Clutter.EVENT_STOP;
  }

  _onFullScreen() {
    this._queueHide();
  }
}
