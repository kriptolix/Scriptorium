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
    ('scenes', ScrptWritingPanel()),
    ('people', ScrptEntityPanel()),
    #('overview', ScrptOverviewPanel()),
]


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/editor.ui")
class ScrptEditorView(Adw.NavigationPage):
    __gtype_name__ = "ScrptEditorView"

    panels_navigation = Gtk.Template.Child()
    panels_content = Gtk.Template.Child()

    # The manuscript the editor is connected to
    manuscript = GObject.Property(type=Manuscript)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Setup all the panels
        self.initialise_panels()

        # Connect the signal for navigation
        self.panels_navigation.connect("row-selected", self.on_selected_item)

        # Keep an eye for changes to the manuscript base path
        self.connect('notify::manuscript', self.on_manuscript_changed)

    def initialise_panels(self):
        """
        Add all the panels to the menu
        """
        for panel_id, panel_content in PANELS:
            # Create a menu entry
            data = panel_content.metadata()
            box = Gtk.Box.new(spacing=12, orientation=Gtk.Orientation.HORIZONTAL)
            image = Gtk.Image.new_from_icon_name(icon_name=data['icon_name'])
            box.append(image)
            label = Gtk.Label.new(data['title'])
            box.append(label)
            box.panel_id = panel_id
            self.panels_navigation.append(box)

            # Add the panel to the stack
            self.panels_content.add_named(panel_content, panel_id)

    def on_selected_item(self, _list_box, _selected_item):
        panel_id = _selected_item.get_child().panel_id
        logger.info(f"Switching to panel {panel_id}")
        self.panels_content.set_visible_child_name(panel_id)

    def on_manuscript_changed(self, _manuscript, _other):
        """
        Called when the editor is connected to a manuscript
        """
        logger.info(f"Connect editor to {self.manuscript.title}")

        # Set the title of the window
        self.set_title(self.manuscript.title)

        # Connect all the panels
        for panel_id, panel_content in PANELS:
            panel_content.bind_to_manuscript(self.manuscript)

        # Open the plotting tab by default
        #self.stack.set_visible_child_name('plotting')
