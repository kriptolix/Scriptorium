# window.py
#
# Copyright 2025 Christophe Guéret
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
from gi.repository import Gtk, Adw, GObject, Gdk, Gio, GLib
from pathlib import Path

# It seems Builder won't find the widgets unless we import them?
from scriptorium.views import ScrptEditorView

from scriptorium.models import Project
from scriptorium.globals import BASE

logger = logging.getLogger(__name__)

# Design choice: we create and add the navigation panels for the editor as
# they are activated and push. Later on we will be able to easily spawn them
# as separate window instead if this is what the user would prefer

@Gtk.Template(resource_path=f'{BASE}/window.ui')
class ScrptWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ScrptWindow'

    navigation = Gtk.Template.Child()
    library_panel = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    # This is a pointer to the currently open project, defaults to None
    project = GObject.Property(type=Project, default=None)

    # The base path of all the manuscripts
    projects_base_path = GObject.Property(type=str)

    # This is the identifier of the manuscript that was last opened
    last_manuscript_name = GObject.Property(type=str, default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load custom CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(
            Gio.File.new_for_uri(f"resource:/{BASE}/style.css")
        )
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Load custom icons
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        theme.add_resource_path(f"{BASE}/icons")

        # Load the settings up
        self.settings = Gio.Settings(schema_id="io.github.cgueret.Scriptorium")

        # Bind the settings related to the window
        self.settings.bind("window-width", self, "default-width",
            Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind("window-height", self, "default-height",
            Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind("window-maximized", self, "maximized",
            Gio.SettingsBindFlags.DEFAULT
        )

        self.settings.bind("last-manuscript-name", self, "last-manuscript-name",
            Gio.SettingsBindFlags.DEFAULT
        )

        # Used to make screenshots
        #self.set_requested_width(800)

        # Create a property for last open project and connect that to a setting
        # Notify for changes here; check if correct version before pushing
        # if all fine push to editor
        # If notify indicate the current project is None push library view

        # When editor is closed it sets the open project to None

        # When an item is clicked in the library the project is set to the value

        # self._open_library()

        # The library is where a project is selected by the user. We keep an
        # eye on actions there
        self.connect(
            'notify::project',
            self.on_project_changed
        )

        # Connect a callback in the library to keep an eye on projects base path
        self.connect(
            'notify::projects-base-path',
            self.library_panel.on_projects_base_path_changed
        )

        # Open the default data directory
        # (TODO Implement the setting for data folder)
        projects_path = Path(GLib.get_user_data_dir()) / Path('manuscripts')
        if not projects_path.exists():
            projects_path.mkdir()
        self.projects_base_path = projects_path.resolve()

    @Gtk.Template.Callback()
    def on_close_request(self, event):
        logger.info("Window close requested")
        # Save the name of the last edited project

    def _open_library(self):
        # Get a reference to the library panel
        self.library_panel.connect('notify::selected-project',
            self.on_selected_project_changed)

        # Set the data folder
        manuscript_path = Path(GLib.get_user_data_dir()) / Path('manuscripts')
        if not manuscript_path.exists():
            manuscript_path.mkdir()
        logger.info(f'Data location: {manuscript_path}')
        self.library_panel.set_property('manuscripts_base_path',
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

    def on_project_changed(self, _navigation, _other):
        """Handle a change in the selected project."""
        logger.info(f"Change currently edited project to {self.project}")

        # If we did select something, open the editor
        if self.project is not None:
            logger.info(f"\"{self.project.title}\": create and open editor")

            # Create an editor navigation page and push it to the stack
            editor_page = ScrptEditorView()
            if not self.project.is_opened:
                self.project.open()
            editor_page.connect_to_project(self.project)
            self.navigation.push(editor_page)

        # Keep track of the last manuscript selected
        settings = Gio.Settings(schema_id="io.github.cgueret.Scriptorium")
        settings.set_string(
            "last-manuscript-name",
            self.project.identifier if self.project is not None else ""
        )

    def close_editor(self, editor_view):
        self.navigation.pop()

    def inform(self, message: str):
        toast = Adw.Toast.new(title=message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
