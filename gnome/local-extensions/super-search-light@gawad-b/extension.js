import GObject from 'gi://GObject';
import Gio from 'gi://Gio';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const SEARCH_LIGHT = 'search-light@icedman.github.com';

export default class SuperSearchLight extends Extension {
    enable() {
        // Make sure mutter emits 'overlay-key' for a bare Super tap.
        this._mutter = new Gio.Settings({schema_id: 'org.gnome.mutter'});
        this._mutter.set_string('overlay-key', 'Super');

        // Mute GNOME Shell's own handler (opens the overview) ...
        GObject.signal_handlers_block_matched(global.display, {signalId: 'overlay-key'});

        // ... and send the key to Search Light instead.
        this._id = global.display.connect('overlay-key', () => {
            const sl = Main.extensionManager.lookup(SEARCH_LIGHT)?.stateObj;
            if (sl?._queueToggle)
                sl._queueToggle();
        });
    }

    disable() {
        if (this._id) {
            global.display.disconnect(this._id);
            this._id = 0;
        }
        GObject.signal_handlers_unblock_matched(global.display, {signalId: 'overlay-key'});
        this._mutter = null;
    }
}
