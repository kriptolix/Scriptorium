# views/plan/page.py
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

from gi.repository import Adw, Gtk, GObject, Gio, GLib

from scriptorium.globals import BASE
from scriptorium.models import Project
from .editor_entities import ScrptEntityPanel

import logging

logger = logging.getLogger(__name__)

PANELS = [
    ("header", "Manuscript"),
    # ("manuscript", ScrptManuscriptPanel),
    # Background research
    # Writting goals
    ("header", "Story line"),
    ("entities", ScrptEntityPanel),
    #("overview", ScrptOverviewPanel),
    # Timeline
    #("chapters", ScrptChaptersPanel),
    # Plot lines
    ("header", "Additional resources"),
    #("scenes", ScrptWritingPanel),
    # Special pages
    # Image gallery
    # Export
]

DEFAULT = "manuscript"


@Gtk.Template(resource_path=f"{BASE}/views/plan/page.ui")
class PlanPage(Adw.Bin):
    __gtype_name__ = "PlanPage"

    panels_list = Gtk.Template.Child()
    panels = Gtk.Template.Child()

    def __init__(self):
        """Create a new instance of the planning page."""
        super().__init__()

        # Setup all the panels
        self.initialise_panels()

        # Open the default panel
        row = None
        #for index in range(len(PANELS)):
            #if PANELS[index][0] == DEFAULT:
                #row = self.panels_navigation.get_row_at_index(index)
                #self.panels_navigation.select_row(row)

    def initialise_panels(self):
        """Add all the panels to the menu."""

        for panel_id, panel in PANELS:
            # Create a menu entry
            box = Gtk.Box.new(spacing=12, orientation=Gtk.Orientation.HORIZONTAL)
            box.set_margin_start(6)
            box.set_margin_end(6)
            box.set_margin_top(12)

            if panel_id == "header":
                box.set_margin_bottom(6)
                label = Gtk.Label(label=panel)
                label.add_css_class("dim-label")
            else:
                box.set_margin_bottom(12)
                image = Gtk.Image.new_from_icon_name(icon_name=panel.__icon_name__)
                box.append(image)
                label = Gtk.Label.new(panel.__title__)

            box.append(label)

            self.panels_list.append(box)

            # Add the id and title to the box for easy retrieval later
            box.panel_id = panel_id

        # Deactivate all the headers
        index = 0
        row = self.panels_list.get_row_at_index(index)
        while row is not None:
            if row.get_child().panel_id == "header":
                row.set_activatable(False)
                row.set_selectable(False)
            index += 1
            row = self.panels_list.get_row_at_index(index)

    @Gtk.Template.Callback()
    def on_listbox_row_selected(self, _list_box, _selected_item):
        """Change the panel currently displayed."""
        selection = _selected_item.get_child()
        logger.info(f"Switching to panel {selection.panel_id}")

        p = None
        for panel_id, panel in PANELS:
            if panel_id == selection.panel_id:
                # Instantiate the panel
                p = panel(self)

                # Add a button to close the side bar
                header_bars = self.find_header_bars(p)
                self.add_close_sidebar_widget(header_bars[0])

        self.panels.replace([p])

    @Gtk.Template.Callback()
    def on_editorview_closed(self, _editorview):
        """Handle a request to close the editor."""
        if self.project is not None:
            logger.info("Editor is closed, saving the manuscript")
            self.project.save_to_disk()

    def close_on_delete(self):
        self.project = None
        self.window.close_editor(self)

    def on_add_entity(self, _action, entity_type):
        target_type = entity_type.get_string()
        logger.info(f"Add {target_type}")
        dialog = ScrptAddDialog(target_type)

        def handle_response(dialog, task):
            if dialog.choose_finish(task) == "add":
                logger.info(f"Add entity {dialog.title}: {dialog.synopsis}")
                self.manuscript.create_entity(
                    target_type, dialog.title, dialog.synopsis
                )

        dialog.choose(self, None, handle_response)

