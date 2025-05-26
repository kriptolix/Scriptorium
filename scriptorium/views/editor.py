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

from gi.repository import Adw, Gtk, GObject, Gio, GLib

from scriptorium.globals import BASE
from scriptorium.dialogs import ScrptAddDialog
from scriptorium.widgets import ThemeSelector
from scriptorium.models import Manuscript, Project

from .editor_scenes import ScrptWritingPanel
from .editor_entities import ScrptEntityPanel
from .editor_overview import ScrptOverviewPanel
from .editor_manuscript import ScrptManuscriptPanel
from .editor_chapters import ScrptChaptersPanel
from .editor_formatting import ScrptFormattingPanel

import logging

logger = logging.getLogger(__name__)

PANELS = [
    ("header", "Plan"),
    ("manuscript", ScrptManuscriptPanel),
    # TODO: Research
    # TODO: Goals
    ("header", "Plot"),
    ("overview", ScrptOverviewPanel),
    # TODO: Timeline
    ("entities", ScrptEntityPanel),
    ("chapters", ScrptChaptersPanel),
    # TODO: Plot lines
    ("header", "Write"),
    ("scenes", ScrptWritingPanel),
    # TODO: Special pages
    ("header", "Edit"),
    ("formatting", ScrptFormattingPanel),
    # TODO: Export
]

DEFAULT = "manuscript"


@Gtk.Template(resource_path=f"{BASE}/views/editor.ui")
class ScrptEditorView(Adw.NavigationPage):
    """The editor is the main view to modify a manuscript."""

    __gtype_name__ = "ScrptEditorView"

    project = GObject.Property(type=Project)

    panels_navigation = Gtk.Template.Child()
    panels = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    panels_sidebar = Gtk.Template.Child()
    win_menu = Gtk.Template.Child()


    def __init__(self, window, project:Project):
        """Create a new instance of the editor."""
        super().__init__()

        # We're a view not a stand alone window so we get the pointer to the
        # actual window to create the actions
        self._window = window

        # Keep track of the manuscript the editor is associated to
        self.project = project

        # Connect an instance of the theme button to the menu
        popover = self.win_menu.get_popover()
        theme_selector = ThemeSelector()
        theme_selector.action_name = "app.style-variant"
        popover.add_child(theme_selector, "theme")

        # Setup all the panels
        self.initialise_panels()

        # Open the default panel
        row = None
        for index in range(len(PANELS)):
            if PANELS[index][0] == DEFAULT:
                row = self.panels_navigation.get_row_at_index(index)
                self.panels_navigation.select_row(row)

    def create_action(self, window, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        logger.info("Create action")
        action = Gio.SimpleAction.new(name=name, parameter_type=GLib.VariantType("s"))
        action.connect("activate", callback)
        window.add_action(action)
        if shortcuts:
            application = window.get_application()
            application.set_accels_for_action(f"win.{name}('1')", shortcuts)

    def initialise_panels(self):
        """Add all the panels to the menu."""
        self.panels_sidebar.set_title(self.project.manuscript.title)

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

            self.panels_navigation.append(box)

            # Add the id and title to the box for easy retrieval later
            box.panel_id = panel_id

        # Deactivate all the headers
        index = 0
        row = self.panels_navigation.get_row_at_index(index)
        while row is not None:
            if row.get_child().panel_id == "header":
                row.set_activatable(False)
                row.set_selectable(False)
            index += 1
            row = self.panels_navigation.get_row_at_index(index)

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

    def find_header_bars(self, root):
        header_bars = []
        child = root.get_first_child()
        while child:
            if isinstance(child, Adw.HeaderBar):
                header_bars.append(child)
            # Correct: merge returned lists into the parent list
            header_bars.extend(self.find_header_bars(child))
            child = child.get_next_sibling()
        return header_bars

    def add_close_sidebar_widget(self, header_bar):
        show_sidebar_button = Gtk.ToggleButton(icon_name="sidebar-show-symbolic")
        header_bar.pack_start(show_sidebar_button)

        self.split_view.bind_property(
            "show_sidebar",
            show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

    @Gtk.Template.Callback()
    def on_editorview_closed(self, _editorview):
        """Handle a request to close the editor."""
        if self.project is not None:
            logger.info("Editor is closed, saving the manuscript")
            self.project.save_to_disk()

    def close_on_delete(self):
        self.project = None
        self._window.close_editor(self)

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

