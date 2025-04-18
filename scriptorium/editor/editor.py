# editor.py
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

from gi.repository import Adw, Gtk, GObject


# The editor interface is using the model for a manuscript
from .model import Manuscript
from .editor_writing import ScrptWritingPanel
from .editor_entity import ScrptEntityPanel
from .editor_overview import ScrptOverviewPanel

import logging

logger = logging.getLogger(__name__)

PANELS = [
    ("scenes", ScrptWritingPanel()),
    # ("people", ScrptEntityPanel()),
    # ('overview', ScrptOverviewPanel()),
]


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/editor.ui")
class ScrptEditorView(Adw.NavigationPage):
    """The editor is the main view to modify a manuscript."""

    __gtype_name__ = "ScrptEditorView"

    panels_navigation = Gtk.Template.Child()
    panels = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    panels_sidebar = Gtk.Template.Child()

    # The manuscript the editor is connected to
    manuscript = GObject.Property(type=Manuscript)

    def __init__(self, **kwargs):
        """Create a new instance of the editor."""
        super().__init__(**kwargs)

        # Setup all the panels
        self.initialise_panels()

        # Connect the signal for navigation
        self.panels_navigation.connect("row-selected", self.on_selected_item)

        # Keep an eye for changes to the manuscript base path
        self.connect("notify::manuscript", self.on_manuscript_changed)

        # Open the first panel by default
        row = self.panels_navigation.get_row_at_index(0)
        self.panels_navigation.emit("row-selected", row)

    def initialise_panels(self):
        """Add all the panels to the menu."""
        for panel_id, panel in PANELS:
            # Create a menu entry
            box = Gtk.Box.new(spacing=12, orientation=Gtk.Orientation.HORIZONTAL)
            image = Gtk.Image.new_from_icon_name(icon_name=panel.icon_name)
            box.append(image)
            label = Gtk.Label.new(panel.get_title())
            box.append(label)
            self.panels_navigation.append(box)

            # Add the id and title to the box for easy retrieval later
            box.panel_id = panel_id

            # Add the panel to the stack
            self.panels.add(panel)

            # Connect the side bar button(s)
            panel.bind_side_bar_button(self.split_view)

    def on_selected_item(self, _list_box, _selected_item):
        """Change the panel currently displayed."""
        selection = _selected_item.get_child()
        logger.info(f"Switching to panel {selection.panel_id}")
        self.panels.replace_with_tags([selection.panel_id])

    def on_manuscript_changed(self, _manuscript, _other):
        """Connect the editor to a manuscript."""
        logger.info(f"Connect editor to {self.manuscript.title}")

        # Set the title of the window
        self.panels_sidebar.set_title(self.manuscript.title)

        # Connect all the panels
        for panel_id, panel in PANELS:
            panel.bind_to_manuscript(self.manuscript)


