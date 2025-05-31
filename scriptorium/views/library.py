# library/library.py
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

from gi.repository import Adw, GObject, Gio, Gtk

from scriptorium.models import Library, Project
from scriptorium.widgets import ManuscriptItem
from scriptorium.dialogs import ScrptAddDialog
from scriptorium.widgets import ThemeSelector

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/views/library.ui")
class ScrptLibraryView(Adw.NavigationPage):
    __gtype_name__ = "ScrptLibraryView"

    # The library
    library: Library

    selected_project = GObject.Property(type=Project)

    # The base path of all the manuscripts
    manuscripts_base_path = GObject.Property(type=str)

    # Objects of the templace
    manuscripts_grid = Gtk.Template.Child()
    item_factory = Gtk.Template.Child()
    win_menu = Gtk.Template.Child()
    grid_stack = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Keep an eye for changes to the manuscript base path
        self.connect("notify::manuscripts-base-path", self.on_base_path_changed)

        self.item_factory.connect("setup", self.on_setup_item)
        self.item_factory.connect("bind", self.on_bind_item)

        # Connect an instance of the theme button to the menu
        popover = self.win_menu.get_popover()
        theme_selector = ThemeSelector()
        theme_selector.action_name = "app.style-variant"
        popover.add_child(theme_selector, "theme")

    @Gtk.Template.Callback()
    def on_add_manuscript_clicked(self, _button):
        """Handle a click on the button to add a manuscript."""
        logger.info("Open dialog to add manuscript")
        dialog = ScrptAddDialog("manuscript")
        dialog.choose(self, None, self.on_add_manuscript)

    def on_add_manuscript(self, dialog, task):
        """Add a new manuscript."""
        response = dialog.choose_finish(task)
        if response == "add":
            logger.info(f"Add manuscript {dialog.title}: {dialog.synopsis}")
            self.library.create_project(dialog.title, dialog.synopsis)

    def on_setup_item(self, _, list_item):
        list_item.set_child(ManuscriptItem())

    def on_bind_item(self, _, list_item):
        project = list_item.get_item()
        manuscript_item = list_item.get_child()
        manuscript_item.set_property("title", project.manuscript.title)

        # Set the path of the cover image
        manuscript_item.set_property("cover", project.manuscript.get_cover_path())

    def on_base_path_changed(self, _base_path, _other):
        """
        Called when the property of the base path is changed
        """
        logger.info(f"Loading library from {self.manuscripts_base_path}")

        # Load up an instance of the library
        self.library = Library(self.manuscripts_base_path)

        # Connect the model to the grid, don't select anything by default
        selection_model = Gtk.SingleSelection(model=self.library.projects)
        selection_model.set_autoselect(False)
        selection_model.set_can_unselect(True)
        selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
        selection_model.connect("selection-changed", self.on_selection_changed)
        self.manuscripts_grid.set_model(selection_model)

        # Connect a signal to the list model to detect when content is available
        self.library.projects.connect("items-changed", self.on_grid_content_changed)

        # Manually trigger it
        self.on_grid_content_changed(self.library.projects, 0, 0, 0)

        # See if we should open the last project
        self.open_last_project()

    def on_grid_content_changed(self, list_model, _position, _added, _removed):
        n_items = list_model.get_n_items()
        if n_items > 0:
            self.grid_stack.set_visible_child_name("manuscripts")
        else:
            self.grid_stack.set_visible_child_name("empty_folder")

    def on_selection_changed(self, selection, position, n_items):
        """
        Called when a manuscript is selected
        """
        # Get the select manuscript and unselect it
        selected_item = selection.get_selected_item()
        if selected_item is not None:
            self.selected_project = selection.get_selected_item()
            manuscript = self.selected_project.manuscript

            logger.info(f"Selected manuscript {manuscript.title}")
            settings = Gio.Settings(schema_id="io.github.cgueret.Scriptorium")
            settings.set_string(
                "last-manuscript-name",
                self.selected_project.identifier
            )
            selection.set_selected(Gtk.INVALID_LIST_POSITION)

    def open_last_project(self):
        """Check if we need to open the last project."""
        settings = Gio.Settings(schema_id="io.github.cgueret.Scriptorium")

        if not settings.get_boolean("open-last-project"):
            # Nope, don't need to open the last project
            return

        last_opened = settings.get_string("last-manuscript-name")

        logger.info(f"Trigger open for last opened: {last_opened}")

        model = self.manuscripts_grid.get_model()
        if len(model) > 0:
            index = 0
            for i in range(len(model)):
                if model[i].identifier == last_opened:
                    index = i
            model.select_item(index, True)

