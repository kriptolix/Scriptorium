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
from gi.repository import Gtk, Graphene, Gio
from scriptorium.globals import BASE
from scriptorium.models import Chapter, Scene, Manuscript
from .navigation_item import NavigationItem

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/write/navigation.ui")
class WriteNavigation(Gtk.Box):
    __gtype_name__ = "WriteNavigation"

    factory = Gtk.Template.Child()
    list_view = Gtk.Template.Child()

    drag_point = Graphene.Point()
    item_dragged = None
    accented_row = None
    place_holder = None

    @Gtk.Template.Callback()
    def on_list_item_setup(self, _, list_item):
        list_item.set_child(NavigationItem())

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
        widget.set_label(item)

        # Set the resource
        widget.resource = item
        widget.parent_model = list_row.get_parent().get_children() if list_row.get_parent() is not None else None

    def connect_to(self, project):
        """Connect the navigation to the project and its contents."""

        # Turn the content into a tree, instance of Chapter may have children
        roots = Gio.ListStore.new(Manuscript)
        roots.append(project.manuscript)

        tree_list_model = Gtk.TreeListModel.new(
            roots, False, True,
            lambda item: item.content if isinstance(item, (Manuscript, Chapter)) else None
        )
        tree_list_model.set_autoexpand(False)

        # Use this model to define a selection model that let users pick a scene
        # with none being selected by default
        selection_model = Gtk.SingleSelection(model=tree_list_model)
        selection_model.set_autoselect(False)
        selection_model.set_can_unselect(True)
        selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

        # Assign this model to the navigation list view
        self.list_view.set_model(selection_model)
