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
from scriptorium.globals import BASE

# The editor interface is using the model for a manuscript
from scriptorium.models import Manuscript
from .editor_scenes import ScrptWritingPanel
from .editor_entities import ScrptEntityPanel
from .editor_overview import ScrptOverviewPanel
from .editor_manuscript import ScrptManuscriptPanel
from .editor_chapters import ScrptChaptersPanel
from .editor_formatting import ScrptFormattingPanel

import logging

logger = logging.getLogger(__name__)

PANELS = [
    ("header", "Manuscript"),
    ("manuscript", ScrptManuscriptPanel),
    ("formatting", ScrptFormattingPanel),
    ("overview", ScrptOverviewPanel),
    # Targets
    ("header", "Plot"),
    ("entities", ScrptEntityPanel),
    # Plot lines
    # Characters
    ("header", "Write"),
    ("scenes", ScrptWritingPanel),
    ("header", "Organize"),
    ("chapters", ScrptChaptersPanel),
]

DEFAULT = "manuscript"


@Gtk.Template(resource_path=f"{BASE}/views/editor.ui")
class ScrptEditorView(Adw.NavigationPage):
    """The editor is the main view to modify a manuscript."""

    __gtype_name__ = "ScrptEditorView"

    panels_navigation = Gtk.Template.Child()
    panels = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    panels_sidebar = Gtk.Template.Child()

    @GObject.Property(type=Manuscript)
    def manuscript(self):
        """The manuscript the editor is connected to."""
        return self._manuscript

    def __init__(self, manuscript: Manuscript, **kwargs):
        """Create a new instance of the editor."""
        super().__init__(**kwargs)

        # Keep track of the manuscript the editor is associated to
        self._manuscript = manuscript

        # Setup all the panels
        self.initialise_panels()

        # Connect the signal for navigation
        self.panels_navigation.connect("row-selected", self.on_selected_item)

        # Open the default panel
        row = None
        for index in range(len(PANELS)):
            if PANELS[index][0] == DEFAULT:
                row = self.panels_navigation.get_row_at_index(index)
                self.panels_navigation.select_row(row)

    def initialise_panels(self):
        """Add all the panels to the menu."""
        self.panels_sidebar.set_title(self.manuscript.title)

        for panel_id, panel in PANELS:
            # Create a menu entry
            box = Gtk.Box.new(spacing=12, orientation=Gtk.Orientation.HORIZONTAL)
            box.set_margin_start(6)
            box.set_margin_end(6)

            if panel_id == "header":
                label = Gtk.Label(label=panel)
                label.add_css_class("dim-label")
                box.append(label)
                box.set_margin_top(12)
                box.set_margin_bottom(6)
            else:
                box.set_margin_top(12)
                box.set_margin_bottom(12)
                image = Gtk.Image.new_from_icon_name(icon_name=panel.__icon_name__)
                box.append(image)
                label = Gtk.Label.new(panel.__title__)
                box.append(label)

            self.panels_navigation.append(box)

            # Add the id and title to the box for easy retrieval later
            box.panel_id = panel_id

        # Deactivate all the headers
        index = 0
        row = self.panels_navigation.get_row_at_index(index)
        while row is not None:
            if row.get_child().panel_id == 'header':
                row.set_activatable(False)
                row.set_selectable(False)
            index += 1
            row = self.panels_navigation.get_row_at_index(index)

    def on_selected_item(self, _list_box, _selected_item):
        """Change the panel currently displayed."""
        selection = _selected_item.get_child()
        logger.info(f"Switching to panel {selection.panel_id}")
        p = None
        for panel_id, panel in PANELS:
            if panel_id == selection.panel_id:
                p = panel(self)
                p.bind_side_bar_button(self.split_view)
        self.panels.replace([p])

    def close_on_delete(self):
        self._manuscript = None
        self.get_parent().pop()

    @Gtk.Template.Callback()
    def on_editorview_closed(self, _editorview):
        """Handle a request to close the editor."""
        logger.info("Editor is closed, saving the manuscript")
        if self.manuscript is not None:
            self.manuscript.save_to_disk()
