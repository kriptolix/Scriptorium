# views/write/navigation_item.py
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
from gi.repository import Gtk, GObject, Gdk, Adw, Gio, GLib
from scriptorium.globals import BASE
from scriptorium.models import Chapter, Scene, Resource, Manuscript
import enum

import logging

logger = logging.getLogger(__name__)

DRAGGING_OPACITY = 0.4
BASE_MARGIN = 12

class State(enum.IntEnum):
    NEUTRAL = 0
    PUSHED = 1


@Gtk.Template(resource_path=f"{BASE}/views/write/navigation_item.ui")
class NavigationItem(Adw.Bin):
    __gtype_name__ = "NavigationItem"

    resource = GObject.Property(type=Resource)
    parent_model = GObject.Property(type=Gio.ListStore)
    is_dragged = GObject.Property(type=bool, default=False)
    is_animated = GObject.Property(type=bool, default=False)
    push_state = GObject.Property(type=int, default=State.NEUTRAL)
    is_visited = GObject.Property(type=bool, default=False)

    content = Gtk.Template.Child()
    expander = Gtk.Template.Child()
    label = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.label_binding = None

        self.content.set_margin_top(BASE_MARGIN)
        self.content.set_margin_bottom(BASE_MARGIN)

        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare)
        drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-end", self.on_drag_end)
        self.add_controller(drag_source)

        drop_target = Gtk.DropTarget()
        drop_target.set_gtypes([NavigationItem])
        drop_target.set_actions(Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        drop_target.connect("enter", self.on_enter)
        drop_target.connect("leave", self.on_leave)
        drop_target.connect("motion", self.on_motion)
        self.add_controller(drop_target)

    def on_drag_prepare(self, _source, _x, _y):
        """Prepare for a DnD event by attaching the element being grabbed."""
        # We cannot drag root nodes
        if isinstance(self.resource, Manuscript):
            return None

        # Attache ourselves to the drag event
        value = GObject.Value(value_type=NavigationItem, py_value=self)
        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin(self, source, drag):
        """Attach a widget to the drag icon."""
        # Take a snaphot of ourselves and set that as the icon
        widget = Gtk.ListBox()
        widget.add_css_class("navigation-sidebar")
        entry = Gtk.Label(label=self.label.get_label())
        widget.append(entry)
        widget.select_row(widget.get_row_at_index(0))

        #widget = Gtk.Label(label="Move")
        #widget.show()
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(widget)
        #drag.set_hotspot(-20, 0)

        self.is_dragged = True
        self.set_opacity(DRAGGING_OPACITY)

    def on_drag_end(self, source, drag, _):
        self.is_dragged = False
        self.set_opacity(1)

    def on_drop(self, _drop, item, _x, _y):
        logger.info(f"Drop {item} {_x} {_y}")

    def on_accept(self, _src, drop):
        return True

        # We accept a drag of the same type of ourselves
        if drop.get_formats().contain_gtype(type(self.resource)):
            return True

        # If we are a Chapter we accept Scene
        if isinstance(self.resource, Chapter):
            if drop.get_formats().contain_gtype(Scene):
                return True

        # If we are a Manuscript we accept Scene and Chapter
        if isinstance(self.resource, Manuscript):
            if drop.get_formats().contain_gtype(Scene):
                return True
            if drop.get_formats().contain_gtype(Chapter):
                return True

        # Reject all other cases
        return False

    def on_enter(self, drop_target, enter_x, enter_y):
        # Ignore the entry if we are the line dragged
        if self.is_dragged:
            return Gdk.DragAction.MOVE

        # Don't do anything while moving
        if self.is_animated:
            return Gdk.DragAction.MOVE

        self._set_margins(drop_target, enter_y)
        return Gdk.DragAction.MOVE

    def get_children(self):
        return self.expander.get_list_row().get_children()

    def on_leave(self, _source):
        logger.info("Leave")
        self._animate(State.NEUTRAL, BASE_MARGIN)
        #self.content.set_margin_top(BASE_MARGIN)
        #self.content.set_margin_bottom(BASE_MARGIN)
        #self.push_state = State.NEUTRAL

    def on_motion(self, drop_target, motion_x, motion_y):
        # Ignore the entry if we are the line dragged
        if self.is_dragged:
            return Gdk.DragAction.MOVE

        # Don't do anything while moving
        if self.is_animated:
            return Gdk.DragAction.MOVE

        self._set_margins(drop_target, motion_y)
        return Gdk.DragAction.MOVE

    def _set_margins(self, drop_target, y):
        drag = drop_target.get_current_drop().get_drag()
        icon = Gtk.DragIcon.get_for_drag(drag)
        value = icon.get_child()
        _got_bounds, _x, _y, _width, visitor_height = value.get_bounds()
        _got_bounds, _x, own_y, _width, own_height = self.get_bounds()

        if y > (own_y + own_height / 2) and self.push_state != State.PUSHED:
            next_sibling = self.get_parent().get_next_sibling()
            if next_sibling is not None:
                if not next_sibling.get_first_child().is_dragged:
                    self._animate(State.PUSHED, visitor_height)

    def on_animate_step(self, value, target_state, offset):
        box = self.content

        if target_state == State.PUSHED:
            box.set_margin_bottom(int(value))
        elif target_state == State.NEUTRAL:
            if self.push_state == State.PUSHED:
                box.set_margin_bottom(BASE_MARGIN + offset - int(value))

    def on_animation_done(self, _animation, target_state, offset):
        box = self.content

        if target_state == State.NEUTRAL:
            box.set_margin_top(BASE_MARGIN)
            box.set_margin_bottom(BASE_MARGIN)
        elif target_state == State.PUSHED:
            box.set_margin_top(BASE_MARGIN)
            box.set_margin_bottom(offset)

        self.push_state = target_state
        self.is_animated = False

    def _animate(self, target_state, offset):
        # Depending on target_state move up or down until offset
        # Connect "done" to set the target status
        # Set to status = moving when starting animation
        logger.info(f"Start {self.push_state} => {target_state}")

        animation_target = Adw.CallbackAnimationTarget.new(
            self.on_animate_step,
            target_state, offset
        )
        animation = Adw.TimedAnimation.new(
            self.content,
            BASE_MARGIN, offset,
            250,
            animation_target
            )
        self.is_animated = True
        animation.play()
        animation.connect("done", self.on_animation_done, target_state, offset)


    def set_label(self, item):
        """Use the property title of the item to set the label of the row."""
        if self.label_binding is not None:
            self.label_binding.unbind()

        self.label_binding = item.bind_property(
            "title",
            self.label,
            "label",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

