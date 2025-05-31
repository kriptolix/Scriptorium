# main.py
#
# Copyright 2025 Unknown
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from scriptorium.widgets.multiline_entry_row import MultiLineEntryRow
from gi.repository import Gio, Adw, WebKit, GLib
from .window import ScrptWindow
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(name)-40s: %(levelname)-8s %(message)s'
)
logger = logging.getLogger(__name__)


class ScriptoriumApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.cgueret.Scriptorium',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

        self.settings = Gio.Settings(
            schema_id="io.github.cgueret.Scriptorium"
        )
        style_variant_action = self.settings.create_action("style-variant")
        self.add_action(style_variant_action)

        self.settings.connect(
            "changed::style-variant",
            self.change_color_scheme
        )

        # Get the current color scheme
        current_value = self.settings.get_string("style-variant")
        style_variant_action.activate(GLib.Variant('s', current_value))

        # Force loading WebKit, otherwise it is not recognized in Builder
        dummy = WebKit.WebView()
        del dummy

        # Same for MultiLineEntryRow
        dummy = MultiLineEntryRow()
        del dummy

    def change_color_scheme(self, _settings, value):
        """Handle a change in the select color scheme setting."""
        color_scheme = self.settings.get_string(value)

        style_manager = Adw.StyleManager.get_default()
        if color_scheme == 'dark':
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        elif color_scheme == 'light':
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif color_scheme == 'default':
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = ScrptWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Scriptorium',
                                application_icon='io.github.cgueret.Scriptorium',
                                developer_name='Christophe Guéret',
                                version='0.1.0',
                                website='https://github.com/cgueret/Scriptorium',
                                developers=['Christophe Guéret'],
                                copyright='© 2025 Christophe Guéret')
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        #about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        logger.info('app.preferences action activated')

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = ScriptoriumApplication()
    return app.run(sys.argv)
