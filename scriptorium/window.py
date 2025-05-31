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

import logging
from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from pathlib import Path
from scriptorium.views import ScrptEditorView, ScrptLibraryView

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path='/com/github/cgueret/Scriptorium/window.ui')
class ScrptWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ScrptWindow'

    navigation = Gtk.Template.Child()
    #library = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load custom CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(Gio.File.new_for_uri("resource://com/github/cgueret/Scriptorium/style.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Load custom icons
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        theme.add_resource_path("/com/github/cgueret/Scriptorium/icons")

        # Load the settings up
        self.settings = Gio.Settings(schema_id="io.github.cgueret.Scriptorium")

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

    def _open_library(self):
        # Get a reference to the library panel
        self._library_panel = ScrptLibraryView()
        self.navigation.replace([self._library_panel])
        self._library_panel.connect('notify::selected-project',
            self.on_selected_project_changed)

        # Set the data folder
        manuscript_path = Path(GLib.get_user_data_dir()) / Path('manuscripts')
        if not manuscript_path.exists():
            manuscript_path.mkdir()
        logger.info(f'Data location: {manuscript_path}')
        self._library_panel.set_property('manuscripts_base_path',
                                    manuscript_path.resolve())

        #last_opened = self.settings.get_string("last-manuscript-name")
        #logger.info(f"Trigger selection for last opened: {last_opened}")

        #manuscripts_model = self._library_panel.manuscripts_grid.get_model()
        #if self.settings.get_boolean("open-last-project"):
        #    if len(manuscripts_model) > 0:
        #        index = 0
        #        for i in range(len(manuscripts_model)):
        #            if manuscripts_model[i].identifier == last_opened:
        #                index = i
        #        manuscripts_model.select_item(index, True)

    def on_selected_project_changed(self, _navigation, _other):
        project = self._library_panel.selected_project
        logger.info(f"Create and open editor for {project.manuscript.title}")

        editor_view = ScrptEditorView(self, project)
        self.navigation.push(editor_view)

    def close_editor(self, editor_view):
        self.navigation.pop()
