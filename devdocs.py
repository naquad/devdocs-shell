#!/usr/bin/env python

from gi.repository import Gtk, WebKit2, GLib, Gdk, Gio
import json
import os

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

class Search(Gtk.HBox):
    "Search bar implementation."

    CSS = """
    GtkSearchEntry#search_failed {
        background: #ff6666;
        color: #111;
    }
    """.encode('UTF-8')

    def __init__(self, controller):
        Gtk.HBox.__init__(self, False)
        self.controller = controller
        self.setup_ui()
        self.setup_css()

        self.controller.connect('failed-to-find-text', self.on_fail)
        self.controller.connect('found-text', self.on_found)

    def setup_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(self.CSS)
        self.get_style_context().\
            add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def setup_ui(self):
        self.entry = Gtk.SearchEntry()
        self.entry.connect('key-press-event', self.on_keypress)
        self.entry.connect_after('notify::text', self.on_search)
        self.entry.show()
        self.pack_start(self.entry, False, False, 0)

        btn = Gtk.Button.new_from_icon_name(Gtk.STOCK_GO_DOWN, Gtk.IconSize.BUTTON)
        btn.connect('clicked', self.on_next)
        btn.show()
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name(Gtk.STOCK_GO_UP, Gtk.IconSize.BUTTON)
        btn.connect('clicked', self.on_prev)
        btn.show()
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name(Gtk.STOCK_CLOSE, Gtk.IconSize.BUTTON)
        btn.show()
        self.pack_start(btn, False, False, 0)

    def toggle(self):
        "show/hide search bar"

        if self.is_visible():
            self.controller.search_finish()
            self.hide()
        else:
            self.show()
            self.entry.select_region(0, -1)
            self.entry.grab_focus()
            self.on_search()

    def on_search(self, *unused):
        text = self.entry.get_text()
        if text:
            self.search_text(text)

    def on_keypress(self, entry, evt):
        if evt.keyval == Gdk.KEY_Escape:
            if evt.state == 0:
                self.toggle()
        elif evt.keyval == Gdk.KEY_Return or evt.keyval == Gdk.KEY_KP_Enter:
            if evt.state == 0:
                self.controller.search_next()
            elif evt.state & Gdk.ModifierType.SHIFT_MASK:
                self.controller.search_previous()

    def search_text(self, text):
        self.controller.search(text, WebKit2.FindOptions.CASE_INSENSITIVE | WebKit2.FindOptions.WRAP_AROUND, GLib.MAXINT32)

    def on_found(self, ctrl, cnt):
        self.entry.set_name('search')

    def on_fail(self, finder):
        self.entry.set_name('search_failed')

    def on_next(self, btn):
        self.controller.search_next()

    def on_prev(self, btn):
        self.controller.search_previous()


class MainWindow(Gtk.Window):
    BASE_URL = 'http://devdocs.io'
    DEFAULT_TITLE = 'DevDocs'

    def __init__(self, app):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.settings = app
        self.setup_ui()

    def navigate(self, term=None):
        url = self.BASE_URL

        if term is not None:
            url = '%s#q=%s' % (url, quote(term))

        self.web_view.load_uri(url)

    def setup_ui(self):
        self.set_title(self.DEFAULT_TITLE)

        # WebKit2 WebView setup.
        # TODO: after https://bugs.webkit.org/show_bug.cgi?id=127410
        # make database to be stored in app config dir

        self.web_view = WebKit2.WebView()
        self.web_view.get_context().\
            get_cookie_manager().\
            set_persistent_storage(
                self.settings.cookie_path,
                WebKit2.CookiePersistentStorage.SQLITE
            )
        self.web_view.show()

        layout = Gtk.VBox()

        toolbar = Gtk.Toolbar()

        button = Gtk.ToolButton(Gtk.STOCK_HOME)
        button.connect('clicked', self.on_home)
        tool_item = Gtk.ToolItem()
        tool_item.add(button)
        toolbar.insert(tool_item, -1)

        button = Gtk.ToolButton(Gtk.STOCK_COPY)
        button.connect('clicked', self.on_copy)
        tool_item = Gtk.ToolItem()
        tool_item.add(button)
        toolbar.insert(tool_item, -1)

        self.address = Gtk.Entry()
        self.address.set_editable(False)
        tool_item = Gtk.ToolItem()
        tool_item.set_expand(True)
        tool_item.add(self.address)

        toolbar.insert(tool_item, -1)

        self.back = Gtk.ToolButton(Gtk.STOCK_GO_BACK)
        self.back.connect('clicked', self.on_back)
        self.back.set_sensitive(False)
        tool_item = Gtk.ToolItem()
        tool_item.add(self.back)
        toolbar.insert(tool_item, -1)

        self.forward = Gtk.ToolButton(Gtk.STOCK_GO_FORWARD)
        self.forward.connect('clicked', self.on_forward)
        self.forward.set_sensitive(False)
        tool_item = Gtk.ToolItem()
        tool_item.add(self.forward)
        toolbar.insert(tool_item, -1)

        button = Gtk.ToolButton(Gtk.STOCK_REFRESH)
        button.connect('clicked', self.on_refresh)
        tool_item = Gtk.ToolItem()
        tool_item.add(button)
        toolbar.insert(tool_item, -1)

        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)

        button = Gtk.ToolButton(Gtk.STOCK_FIND)
        button.connect('clicked', self.on_search)

        key, mod = Gtk.accelerator_parse("<control>f")
        button.add_accelerator('clicked', accel, key, mod, Gtk.AccelFlags.VISIBLE)

        tool_item = Gtk.ToolItem()
        tool_item.add(button)
        toolbar.insert(tool_item, -1)

        toolbar.show_all()

        layout.pack_start(toolbar, False, True, 0)

        overlay = Gtk.Overlay()
        overlay.add(self.web_view)

        self.link_address = Gtk.Label()
        self.link_address.set_halign(Gtk.Align.START)
        self.link_address.set_valign(Gtk.Align.END)
        self.link_address.show()
        overlay.add_overlay(self.link_address)

        self.search = Search(self.web_view.get_find_controller())
        self.search.set_halign(Gtk.Align.END)
        self.search.set_valign(Gtk.Align.START)
        self.search.set_margin_right(50)
        overlay.add_overlay(self.search)
        overlay.show()

        layout.pack_start(overlay, True, True, 0)
        layout.show()

        self.add(layout)

        self.set_default_size(self.settings.width, self.settings.height)
        self.move(self.settings.left, self.settings.top)

        if self.settings.maximized:
            self.maximize()

        if self.settings.fullscreen:
            self.fullscreen()

        self.show()

        self.connect('delete-event', self.on_exit)
        self.web_view.connect('decide-policy', self.on_navigate, False)
        self.web_view.connect('create', self.on_create)
        self.web_view.connect('mouse-target-changed', self.on_link_url)

        self.web_view.connect_after('notify::title', self.on_title)
        self.web_view.connect_after('notify::uri', self.on_uri)

    def open_in_browser(self, url):
        Gtk.show_uri(None, url, Gdk.CURRENT_TIME)

    def on_search(self, btn):
        self.search.toggle()

    def on_link_url(self, view, hit, modifiers):
        link = hit.get_link_uri()

        if link:
            self.link_address.set_text(link)
            self.link_address.show()
        else:
            self.link_address.hide()

    def on_home(self, btn):
        self.web_view.load_uri(self.BASE_URL)

    def on_copy(self, btn):
        text = self.address.get_text()
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, len(text))

    def on_back(self, btn):
        self.web_view.go_back()

    def on_forward(self, btn):
        self.web_view.go_forward()

    def on_refresh(self, btn):
        self.web_view.reload()

    def on_title(self, view, title):
        self.set_title(view.get_property('title') or self.DEFAULT_TITLE)

    def on_uri(self, view, url):
        self.address.set_text(view.get_uri())
        self.back.set_sensitive(view.can_go_back())
        self.forward.set_sensitive(view.can_go_forward())

    def on_create(self, view):
        view = WebKit2.WebView()
        view.connect('decide-policy', self.on_navigate, True)
        return view

    def on_navigate(self, view, decision, dtype, always):
        if dtype == WebKit2.PolicyDecisionType.RESPONSE:
            return False

        url = decision.get_request().get_uri()
        navtype = decision.get_property('navigation-type')

        if always or dtype == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION or \
                (navtype != WebKit2.NavigationType.OTHER and not url.startswith(self.BASE_URL)):
            self.open_in_browser(url)
            decision.ignore()
            return True

        return False

    def on_exit(self, window, evt):
        window_state = self.get_window().get_state()
        width, height = self.get_size()
        left, top = self.get_position()

        self.settings.save_state({
            'width': width,
            'height': height,
            'top': top,
            'left': left,
            'maximized': bool(window_state & Gdk.WindowState.MAXIMIZED),
            'fullscreen': bool(window_state & Gdk.WindowState.FULLSCREEN)
        })

class Application(Gtk.Application):
    APP_NAME = 'devdocs'
    APP_ID = 'me.naquad.%s' % APP_NAME

    DEFAULT_SETTINGS = {
        'width': 800,
        'height': 600,
        'top': 0,
        'left': 0,
        'maximized': False,
        'fullscreen': False
    }

    def __init__(self):
        Gtk.Application.__init__(self, application_id=self.APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        self.base_path = os.path.join(GLib.get_user_config_dir(), self.APP_NAME)
        self.cookie_path = os.path.join(self.base_path, 'cookies.db')
        self.db_path = os.path.join(self.base_path, 'storage.db')
        self.config_path = os.path.join(self.base_path, 'state.json')
        self.config = self.DEFAULT_SETTINGS.copy()

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                self.config.update(json.load(f))

        self.connect('activate', self.on_activate)
        self.connect('command-line', self.on_command_line)

    def navigate(self, term=None):
        self.get_active_window().navigate(term)

    def on_activate(self, app=None):
        window = MainWindow(self)
        window.navigate()
        self.add_window(window)

    def on_command_line(self, app, cmd):
        if not self.get_active_window() and not self.get_is_remote():
            self.activate()
        else:
            self.get_active_window().present()

        args = cmd.get_arguments()
        term = args[1] if len(args) > 1 else None
        self.navigate(term)

        return 0

    def save_state(self, state):
        self.config.update(state)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f)

    def __getattr__(self, name):
        if name in self.DEFAULT_SETTINGS:
            return self.config[name]

        raise AttributeError('no property %s' % (name,))


if __name__ == '__main__':
    import sys
    app = Application()
    app.register(None)
    sys.exit(app.run(sys.argv))
