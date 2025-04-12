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

from gi.repository import Adw, GObject
from gi.repository import Gtk
from .model import Library
from .manuscript import ManuscriptItem

import logging
logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/library/library.ui")
class LibraryNavigationPage(Adw.NavigationPage):
    __gtype_name__ = "LibraryNavigationPage"

    # The library
    library: Library

    # The base path of all the manuscripts
    manuscripts_base_path = GObject.Property(type=str)

    # Objects of the templace
    manuscripts_grid = Gtk.Template.Child()
    item_factory = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Keep an eye for changes to the manuscript base path
        self.connect('notify::manuscripts-base-path', self.on_base_path_changed)

        self.item_factory.connect("setup", self.on_setup_item)
        self.item_factory.connect("bind", self.on_bind_item)

    def on_setup_item(self, _, list_item):
        list_item.set_child(ManuscriptItem())

    def on_bind_item(self, _, list_item):
        manuscript = list_item.get_item()
        manuscript_item = list_item.get_child()
        manuscript_item.set_property('title', manuscript.title)

        # Set the path of the cover image
        manuscript_item.set_property('cover', manuscript.get_cover_path())

    def on_base_path_changed(self, _base_path, _other):
        """
        Called when the property of the base path is changed
        """
        logger.info(f'Loading library from {self.manuscripts_base_path}')

        # Load up an instance of the library
        self.library = Library(self.manuscripts_base_path)

        # Connect the model to the grid, don't select anything by default
        selection_model = Gtk.SingleSelection(model = self.library.manuscripts)
        selection_model.set_autoselect(False)
        selection_model.set_can_unselect(True)
        selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
        selection_model.connect("selection-changed", self.on_selection_changed)
        self.manuscripts_grid.set_model(selection_model)

    def on_selection_changed(self, selection, position, n_items):
        """
        Called when a manuscript is selected
        """
        # Get the select manuscript and unselect it
        selected_manuscript = selection.get_selected_item()
        if selected_manuscript is not None:
            logger.info(f'Selected manuscript {selected_manuscript.title}')
            selection.set_selected(Gtk.INVALID_LIST_POSITION)

            # Set which Manuscript to load in the editor
            self.get_parent().find_page('editor').set_property('manuscript', selected_manuscript)

            # Switch to the editor navigation page
            self.get_parent().push_by_tag('editor')

