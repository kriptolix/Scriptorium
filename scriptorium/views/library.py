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

from scriptorium.globals import BASE
from scriptorium.models import Library, Project
from scriptorium.dialogs import ScrptAddDialog
from scriptorium.widgets import ThemeSelector
from .library_item import LibraryItem

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/library.ui")
class ScrptLibraryView(Adw.NavigationPage):
    __gtype_name__ = "ScrptLibraryView"

    # The Library is the data model holding the list of projects
    library: Library = Library()

    selected_project = GObject.Property(type=Project)

    # The base path of all the manuscripts
    manuscripts_base_path = GObject.Property(type=str)

    # Objects of the templace
    projects_grid = Gtk.Template.Child()
    item_factory = Gtk.Template.Child()
    win_menu = Gtk.Template.Child()
    grid_stack = Gtk.Template.Child()
    migrate_dialog = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Connect an instance of the theme button to the menu
        popover = self.win_menu.get_popover()
        popover.add_child(ThemeSelector(), "theme")

        # Connect a signal to the list model to detect when content is available
        self.library.projects.connect("items-changed", self.on_grid_content_changed)

        # Connect the model to the grid, don't select anything by default
        selection_model = Gtk.SingleSelection(model=self.library.projects)
        selection_model.set_autoselect(False)
        selection_model.set_can_unselect(True)
        selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
        selection_model.connect("selection-changed", self.on_selection_changed)
        self.projects_grid.set_model(selection_model)

    @Gtk.Template.Callback()
    def on_scrptlibraryview_shown(self, _src):
        logger.info("Hello there")
        selection_model = self.projects_grid.get_model()
        selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

        window = self.props.root
        if window is not None:
            window.project = None

    @Gtk.Template.Callback()
    def on_add_manuscript_clicked(self, _button):
        """Handle a click on the button to add a manuscript."""
        logger.info("Open dialog to add manuscript")
        dialog = ScrptAddDialog("project")
        dialog.choose(self, None, self.on_add_manuscript)

    def on_add_manuscript(self, dialog, task):
        """Add a new manuscript."""
        response = dialog.choose_finish(task)
        if response == "add":
            logger.info(f"Add project {dialog.title}: {dialog.synopsis}")
            self.library.create_project(dialog.title, dialog.synopsis)

    @Gtk.Template.Callback()
    def on_setup_item(self, _, list_item):
        list_item.set_child(LibraryItem())

    @Gtk.Template.Callback()
    def on_bind_item(self, _, list_item):
        project = list_item.get_item()
        library_item = list_item.get_child()
        library_item.bind(project)

    def on_grid_content_changed(self, list_model, _position, _added, _removed):
        n_items = list_model.get_n_items()
        if n_items > 0:
            self.grid_stack.set_visible_child_name("projects")
        else:
            self.grid_stack.set_visible_child_name("empty_folder")

    def on_selection_changed(self, selection_model, position, n_items):
        """
        Called when a manuscript is selected
        """
        # Get the selected project
        selected_item = selection_model.get_selected_item()
        if selected_item is not None:
            selected_project = selection_model.get_selected_item()
            logger.info(f"Selected project {selected_project.identifier}")
            if not selected_project.can_be_opened:
                self.migrate_dialog.choose(self)
                #selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
            else:
                # Open the project
                window = self.props.root
                window.project = selected_project

    def open_last_project(self):
        """Check if we need to open the last project."""
        settings = Gio.Settings(schema_id="io.github.cgueret.Scriptorium")

        if not settings.get_boolean("open-last-project"):
            # Nope, don't need to open the last project
            return

        last_opened = settings.get_string("last-manuscript-name")

        logger.info(f"Trigger open for last opened: {last_opened}")

        model = self.projects_grid.get_model()

        # Look for the project with the target identifier
        index = None
        for i in range(len(model)):
            if model[i].identifier == last_opened:
                index = i

        # If we found it and if it can be open go for it
        if index is not None:
            if model[index].can_be_opened:
                model.select_item(index, True)

    def on_projects_base_path_changed(self, window, parameter):
        base_path = window.get_property(parameter.name)
        logger.info(f"Opening library at {base_path}")

        # Connect the library to the folder
        self.library.open_folder(base_path)

        self.open_last_project()

    @Gtk.Template.Callback()
    def on_migrate_dialog_response(self, _dialog, response):
        """Handle a response to migrating a project."""

        # The outcome will alter what is selected in the grid
        selection_model = self.projects_grid.get_model()

        if response == "migrate":
            # Get the selected project
            selected_project = selection_model.get_selected_item()

            # Try to migrate the project
            logger.info(f"Try to migrate {selected_project.identifier}")
            worked = selected_project.migrate()
            window = self.props.root

            if worked:
                window.inform("Project successfuly migrated!")

                # Open the project right away
                window.project = selected_project
            else:
                window.inform("Something went wrong. See logs for details")

                # Seems like we won't open that thing...
                selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

        else:
            # Nevermind then
            selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

