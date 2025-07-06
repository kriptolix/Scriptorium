# views/write/navigation.py
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
from gi.repository import Adw, Gtk, Gdk, GLib, Gio, GObject
from scriptorium.globals import BASE
from scriptorium.widgets import AnnotationCard
from scriptorium.models import Chapter, Scene

import logging

logger = logging.getLogger(__name__)


class TreeWidget(Gtk.Box):
    def __init__(self):
        super().__init__(
            spacing=6,
            margin_start=6,
            margin_end=6,
            margin_top=6,
            margin_bottom=6
        )

        self.expander = Gtk.TreeExpander.new()
        self.expander.set_indent_for_depth(True)

        self.label = Gtk.Label(halign=Gtk.Align.START)

        self.append(self.expander)
        self.append(self.label)


@Gtk.Template(resource_path=f"{BASE}/views/write/navigation.ui")
class WriteNavigation(Gtk.Box):
    __gtype_name__ = "WriteNavigation"

    factory = Gtk.Template.Child()
    list_view = Gtk.Template.Child()

    def __init__(self):
        """Create an instance of the editor."""
        super().__init__()


    @Gtk.Template.Callback()
    def on_list_item_setup(self, _, list_item):
        list_item.set_child(TreeWidget())

    @Gtk.Template.Callback()
    def on_list_item_bind(self, _, list_item):
        """Bind an item to the navigation widget."""
        # The list row
        list_row = list_item.get_item()

        # The model item associated to the row
        item = list_row.get_item()

        # The widget used to display this row
        widget = list_item.get_child()

        # Only scenes can be activated and selected
        list_item.set_activatable(isinstance(item, Scene))
        list_item.set_selectable(isinstance(item, Scene))

        # Set the content of the expander
        widget.expander.set_list_row(list_row)

        # Set the label
        widget.label.set_label(item.title)


    def connect_to(self, project):
        """Connect the navigation to the project."""
        tree_list_model = Gtk.TreeListModel.new(
            project.manuscript.content, False, True,
            lambda item: item.scenes if isinstance(item, Chapter) else None
        )
        tree_list_model.set_autoexpand(False)
        selection_model = Gtk.SingleSelection(model=tree_list_model)
        selection_model.set_autoselect(False)
        selection_model.set_can_unselect(True)
        selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
        self.list_view.set_model(selection_model)

