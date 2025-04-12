# window.py
#
# Copyright 2025 Christophe Gueret
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

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib


import scriptorium.library
import scriptorium.editor

import logging
logger = logging.getLogger(__name__)

# Default status: show the gallery of books, a plus button on top left
# and the title "Scriptorium"
# People click on one of the book to switch mode. Using + opens a simple
# dialog to ask for the name and create a new book

# In editor mode the + is replaced by a X to close the book and return select
# a different one from the gallery

from pathlib import Path





@Gtk.Template(resource_path='/com/github/cgueret/Scriptorium/ui/window.ui')
class ScriptoriumWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ScriptoriumWindow'

    navigation = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load custom CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(Gio.File.new_for_uri("resource://com/github/cgueret/Scriptorium/ui/style.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Load the settings up
        self.settings = Gio.Settings(schema_id="com.github.cgueret.Scriptorium")

        # Bind the settings related to the window
        self.settings.bind("window-width", self, "default-width",
            Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height",
            Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-maximized", self, "maximized",
            Gio.SettingsBindFlags.DEFAULT)

        # TODO Implement the setting for data folder

        # Connect to save the name of the last edited project
        self.connect("close-request", self.on_close_request)

        self._open_library()

    def on_close_request(self, event):
        logger.info("Window close requested")
        # TODO Remember the name of the project currently open in library


    # TODO Turn that into a call back for when the data folder is changed
    def _open_library(self):
        # Get a reference to the library panel
        library_panel = self.navigation.find_page('library')

        # Set the data folder
        manuscript_path = Path(GLib.get_user_data_dir()) / Path('manuscripts')
        if not manuscript_path.exists():
            manuscript_path.mkdir()
        logger.info(f'Data location: {manuscript_path}')
        library_panel.set_property('manuscripts_base_path', manuscript_path.resolve())

        if self.settings.get_boolean("open-last-project"):
            manuscripts_model = library_panel.manuscripts_grid.get_model()
            manuscripts_model.select_item(0, True)

