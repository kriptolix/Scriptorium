# widgets/cards_list.py
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
"""Widget to display a list of cards."""

from gi.repository import Gtk, GObject, Gdk, Gio
from typing import Callable, Any
from scriptorium.globals import BASE
import logging

logger = logging.getLogger(__name__)


class Card(Gtk.Box):
    __gtype_name__ = "Card"

    def __init__(self, parent, create_widget_func, entry):
        """Create an instance of the card."""
        super().__init__()
        self._parent = parent
        self._create_widget_func = create_widget_func
        self._entry = entry
        self._widget = create_widget_func(entry)

        self._moved_x = None
        self._moved_y = None

        self.set_hexpand(True)
        self.add_css_class("card")
        self.add_css_class("activatable")
        self.append(self._widget)

        # Configure it as a drag source
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare)
        drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-cancel", self.on_drag_cancel)
        self.add_controller(drag_source)

    @GObject.Property(type=Gtk.Widget)
    def widget(self):
        return self._widget

    def on_drag_prepare(self, _source, x, y):
        logger.info(f"Prepare {x} {y}")
        value = GObject.Value()
        value.init(type(self._entry))
        value.set_object(self._entry)
        self._moved_x = x
        self._moved_y = y

        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin(self, _source, drag):
        # Create a new widget of the same size
        _got_bounds, _x, _y, width, height = self.get_bounds()
        box = Gtk.Box(hexpand=True)
        box.add_css_class("card")
        box.set_size_request(width, height)
        box.append(self._create_widget_func(self._entry))
        box.set_opacity(0.8)
        box.last_parent_list = self._parent

        # Set it as the icon
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(box)

        # Set the hotspot to be where we grabbed the card
        drag.set_hotspot(self._moved_x, self._moved_y)

        # Replace the widget with a placeholder at the parent
        self._parent.emit("picked", self._entry, self)

        return True

    def on_drag_cancel(self, _source, drag, _reason):
        self._parent.emit("cancelled", self._entry)
        return True

@Gtk.Template(resource_path=f"{BASE}/widgets/cards_list.ui")
class CardsList(Gtk.Box):
    """Widget to display a list of cards"""

    __gtype_name__ = "CardsList"

    __gsignals__ = {
        "picked": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (GObject.Object, Gtk.Widget, )
        ),
        "cancelled": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (GObject.Object, )
        ),
    }

    def __init__(self):
        super().__init__()

        # Set basic layout options
        self.set_spacing(12)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        # Add the placeholder to the list of items
        self._placeholder = Gtk.Label()
        self._placeholder.set_label("")
        self._placeholder.set_size_request(1, 1)
        self._placeholder.add_css_class("osd")
        self._placeholder.hide()
        self._placeholder.set_opacity(0.4)
        self.append(self._placeholder)

        self.connect("picked", self.on_picked)
        self.connect("cancelled", self.on_cancelled)

    @Gtk.Template.Callback()
    def on_state_flags_changed(self, widget, previous_flags):
        # Get the style context for this widget
        sc = widget.get_style_context()
        # Compute new state with DROP_ACTIVE bit cleared
        current = sc.get_state()
        cleaned = current & ~Gtk.StateFlags.DROP_ACTIVE
        # Write it back so GTK will not draw the drop highlight
        if cleaned != current:
            sc.set_state(cleaned)

    def bind_model(self, model: Gio.ListModel = None,
        create_widget_func: Callable[[GObject.Object, Any], Gtk.Widget] = None,
        user_data: Any = None) -> None:
        """Connect the widget to a model."""

        self._model = model
        self._create_widget_func = create_widget_func
        self._user_data = user_data

        # Configure ourselves as a drop target
        drop_target = Gtk.DropTarget.new(self._model.get_item_type(), Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        drop_target.connect("enter", self.on_enter)
        drop_target.connect("motion", self.on_motion)
        drop_target.connect("leave", self.on_leave)
        self.add_controller(drop_target)

        for entry in self._model:
            card = Card(self, self._create_widget_func, entry)
            self.append(card)

    @GObject.Property(type=Gio.ListStore)
    def model(self):
        return self._model

    def replace_placeholder_with(self, widget):
        self.insert_child_after(widget, self._placeholder)
        self._placeholder.hide()

    def on_drop(self, _target, entry, _x, _y):
        logger.info(f"Drop {_target} {entry}")

        # Find the index of the place holder
        index = 0
        child = self.get_first_child()
        while child is not None and child != self._placeholder:
            child = child.get_next_sibling()
            index += 1

        # Insert the entry at the index
        self.model.insert(index, entry)

        # Update the rendering
        card = Card(self, self._create_widget_func, entry)
        self.replace_placeholder_with(card)

        return True

    def move_place_holder(self, target):
        if self._placeholder is not None:
            # Move the current placeholder
            self.reorder_child_after(self._placeholder, target)

    def remove_placeholder(self):
        self._placeholder.hide()

    def get_widget_at_y(self, target_y):
        child = self.get_first_child()
        while child is not None:
            _got_bounds, x, y, width, height = child.get_bounds()
            if target_y > y and target_y < y + height:
                return child
            child = child.get_next_sibling()
        return None

    def is_on_first_half_y(self, target_y, widget):
        _got_bounds, _x, y, _width, height = widget.get_bounds()
        return y + (height / 2) > target_y

    def on_picked(self, _source, entry, widget: Gtk.Widget):
        logger.info(f"Picked {widget} for {entry}")

        # Adjust the size of the placeholder
        _got_bounds, _x, _y, width, height = widget.get_bounds()
        self._placeholder.set_size_request(width, height)
        self._placeholder.show()

        # Remove from the model
        found, index = self.model.find(entry)
        if found:
            self._picked_from_index = index
            self.model.remove(index)

        # Remove the widget
        self.remove(widget)

    def on_cancelled(self, _source, entry):
        logger.info(f"Cancelled for {entry}, return at position {self._picked_from_index}")

        # Hide placeholder and place it at the end
        self.reorder_child_after(self._placeholder, self.get_last_child())
        self._placeholder.hide()

        # Insert back a widget at the correct location
        index = 0
        sibling_widget = None
        while index != self._picked_from_index:
            if sibling_widget is None:
                sibling_widget = self.get_first_child()
            else:
                sibling_widget = sibling_widget.get_next_sibling()
            index += 1
        card = Card(self, self._create_widget_func, entry)
        self.insert_child_after(card, sibling_widget)

        # Insert back into the model
        self.model.insert(self._picked_from_index, entry)

        return True

    def on_enter(self, source, enter_x, enter_y):
        logger.info(f"Enter {enter_x} {enter_y} {self._placeholder}")

        # Get the widget we are currently dragging
        drag = source.get_current_drop().get_drag()
        icon = Gtk.DragIcon.get_for_drag(drag)
        value = icon.get_child()

        # Use that to adjust the placeholder size
        _got_bounds, _x, _y, width, height = value.get_bounds()
        self._placeholder.set_size_request(width, height)

        # If we entered on an empty area, move the place holder at the end
        widget = self.get_widget_at_y(enter_y)
        if widget is None:
            self.reorder_child_after(self._placeholder, self.get_last_child())

        # Show the placeholder
        self._placeholder.show()

        # Recall that we are here now
        value.last_parent_list = self

        return Gdk.DragAction.MOVE

    def on_motion(self, _source, motion_x, motion_y):
        widget = self.get_widget_at_y(motion_y)

        # Move a widget only if we are on one
        if widget is not None:
            if self.is_on_first_half_y(motion_y, widget):
                widget = widget.get_prev_sibling()
            self.reorder_child_after(self._placeholder, widget)

        return Gdk.DragAction.MOVE

    def on_leave(self, _source):
        logger.info(f"Leave")
        self._placeholder.hide()

