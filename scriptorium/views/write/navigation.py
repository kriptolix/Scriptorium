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
from gi.repository import Gtk, GObject, Gdk, Graphene, Gio
from scriptorium.globals import BASE
from scriptorium.models import Chapter, Scene, Resource, Manuscript
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

    def __init__(self):
        super().__init__()

        drag_source = Gtk.GestureDrag()
        drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-update", self.on_drag_update)
        drag_source.connect("drag-end", self.on_drag_end)
        #self.list_view.add_controller(drag_source)

    def on_drag_begin(self, _source, x, y):
        self.drag_point.x = int(x)
        self.drag_point.y = int(y)
        self.index_item_dragged = self._find_row_index_for_point(self.drag_point)

        # Reject picking the root
        if self._get_row(self.index_item_dragged).get_parent() is None:
            self.item_dragged = None
            return

        self.item_dragged = self._get_row(self.index_item_dragged).get_item()
        logger.info(f"Picked {self.item_dragged}")
        self.place_holder = type(self.item_dragged)(self.item_dragged.project, "")
        self.place_holder.title = "Place holder"

    def on_drag_update(self, _source, _x, y):
        # Just return if the drag got rejected
        if self.item_dragged is None:
            return

        # See where we are now
        update_point = Graphene.Point()
        update_point.x = self.drag_point.x
        update_point.y = self.drag_point.y + int(y)

        # Small resistance before we start dragging the tab
        if update_point.near(self.drag_point, 2):
            return

        # Find the index of the item we are currently on
        index_item_target = self._find_row_index_for_point(update_point)
        row_target = self._get_row(index_item_target)
        item_target = row_target.get_item()

        if item_target == self.place_holder:
            return

        # If we are on a root don't do anything
        if row_target.get_parent() is None:
            # TODO show the button "+"
            return

        # Return if the parent is a Chapter and we are dragging a chapter
        target_root_item = row_target.get_parent().get_item()
        if isinstance(target_root_item, Chapter):
            if isinstance(self.item_dragged, Chapter):
                return

        if item_target == self.item_dragged:
            return

        anchor = self._find_item_for_point(update_point)
        #anchor.set_margin_bottom(20)
        logger.info(dir(anchor.get_parent()))
        widget = Gtk.Label()
        widget.set_label("Hello")
        widget.insert_after(anchor.get_parent().get_parent(), anchor.get_parent())

        #self._move_place_holder(row_target)

    def _move_place_holder(self, row):
        # Remove place-holder
        selection_model = self.list_view.get_model()
        tree_model = selection_model.get_model()
        found_ph = False
        index_ph = -1
        parent_model = None
        for index in range(0, tree_model.get_n_items()):
            # Check this row
            row = tree_model.get_row(index)
            if row.get_item() == self.place_holder:
                parent_model = row.get_parent().get_children()
                found_ph, index_ph = parent_model.find(self.place_holder)
        if found_ph:
           parent_model.remove(index_ph)

        # Put place-holder
        # row = anchor.get_item()
        target_parent_model = row.get_parent().get_children()
        found_target, index_target = target_parent_model.find(row.get_item())
        if found_target:
            logger.info(f"Insert at {index_target}")
            target_parent_model.splice(index_target, 0, [self.place_holder])

    def _swap(self, row_target, index_item_target):
        # Find the item we are dragging on
        target_parent_model = row_target.get_parent().get_children()
        found_target, index_target = target_parent_model.find(row_target.get_item())

        # Find the item we are dragging
        row_drag = self._get_row(self.index_item_dragged)
        drag_parent_model = row_drag.get_parent().get_children()
        found_drag, index_drag = drag_parent_model.find(row_drag.get_item())

        # Do the swap
        target_parent_model.splice(index_target, 0, [self.item_dragged])
        drag_parent_model.splice(index_drag, 1, [])

        # We are now dragging the item from its new location
        self.index_item_dragged = index_item_target

        #row_item = self._find_item_for_point(update_point)
        #if row_item is not None:
        #    if row_item != self.accented_row:
        #        if self.accented_row is not None:
        #            self.accented_row.remove_css_class("accent")
        #        self.accented_row = row_item
        #        self.accented_row.add_css_class("accent")
        #self._swap(self.item_dragged.resource, row_item.resource)

    def on_drag_end(self, _source, _x, _y):
        self.item_dragged = None

    def _get_row(self, index):
        selection_model = self.list_view.get_model()
        tree_model = selection_model.get_model()
        return tree_model.get_row(index)

    def _swap(self, dragged_resource, target_resource):
        logger.info(f"Swap {dragged_resource} {target_resource}")
        selection_model = self.list_view.get_model()
        tree_model = selection_model.get_model()

        found_drag, model_drag, index_drag = self._find_in_model(
            tree_model, dragged_resource
        )
        logger.info(f"Drag {model_drag.get_n_items()} {index_drag}")
        return

        # Look for the index of the two items to swap
        found_drag, index_drag = tree_model.find(dragged_resource)
        found_target, index_target = tree_model.find(target_resource)
        if not found_drag or not found_target:
            return

        # Remove the second item from the list
        tree_model.splice(index_target, 1, [dragged_resource])
        tree_model.splice(index_drag, 1, [target_resource])

    def _find_in_model(self, tree_model, target_item):
        # Compare all the elements to see if we found the target
        n_items = tree_model.get_n_items()
        for index in range(0, n_items):
            # Check this row
            row = tree_model.get_row(index)
            if row.get_item() == target_item:
                return True, row.get_parent().get_children(), row.get_position()

            # Recursively search children
            #child_model = row.get_children()
            #if child_model is not None:
            #    logger.info("Recusre")
            #    found, depth, index = self._find_in_model(
            #        child_model, target_item
            #    )
            #    if found:
            #        return found, depth, index

        return False, None, None

    def _find_item_for_point(self, point) -> NavigationItem:
        index = 0
        child = self.list_view.get_first_child()
        while child is not None:
            ok, bounds = child.compute_bounds(self.list_view)
            if ok and bounds.contains_point(point):
                return child.get_first_child()
            child = child.get_next_sibling()
            index += 1
        return None

    def _find_row_index_for_point(self, point) -> int:
        index = 0
        child = self.list_view.get_first_child()
        while child is not None:
            ok, bounds = child.compute_bounds(self.list_view)
            if ok and bounds.contains_point(point):
                return index
            child = child.get_next_sibling()
            index += 1
        return None

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
