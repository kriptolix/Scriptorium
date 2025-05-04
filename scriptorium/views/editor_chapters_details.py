# editor_writing.py
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
"""Editor panel to select and work on the scenes."""

import logging

from gi.repository import Adw, Gtk, GObject, Gdk
from scriptorium.widgets import SceneCard
from scriptorium.dialogs import ScrptSelectScenesDialog

from scriptorium.globals import BASE

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_chapters_details.ui")
class ScrptChaptersDetailsPanel(Adw.NavigationPage):
    __gtype_name__ = "ScrptChaptersDetailsPanel"

    edit_title = Gtk.Template.Child()
    edit_synopsis = Gtk.Template.Child()
    scenes_list = Gtk.Template.Child()
    remove_scene = Gtk.Template.Child()
    remove_scene_grp = Gtk.Template.Child()

    def __init__(self, chapter, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        self._chapter = chapter

        self.set_title(chapter.title)

        # Bind the identifier, title and synopsis
        chapter.bind_property(
            "title",
            self.edit_title,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL |
            GObject.BindingFlags.SYNC_CREATE
        )
        chapter.bind_property(
            "synopsis",
            self.edit_synopsis,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL |
            GObject.BindingFlags.SYNC_CREATE
        )

        self.scenes_list.bind_model(chapter.scenes, self.create_scene_entry)

        drop_target_move = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target_move.connect("drop", self.on_drop_move)
        self.scenes_list.add_controller(drop_target_move)

        # Set the entry to remove scene as an additional drop target
        drop_target_remove = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target_remove.connect("drop", self.on_drop_remove)
        self.remove_scene.add_controller(drop_target_remove)

    def create_scene_entry(self, scene):
        """Bind a scene card to a scene."""
        # Create the scene card entry
        row = Gtk.ListBoxRow()
        row.scene = scene
        entry = SceneCard(scene)
        entry.hide_suffix()
        row.set_child(entry)

        # Configure it as a drag source
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare, row)
        drag_source.connect("drag-begin", self.on_drag_begin, row)
        drag_source.connect("drag-end", self.on_drag_end, row)
        row.add_controller(drag_source)

        # Update row visuals during DnD operation
        drop_controller = Gtk.DropControllerMotion()
        drop_controller.connect("enter",
            lambda _target, _x, y, row: self.scenes_list.drag_highlight_row(row)
            , row
        )
        drop_controller.connect("leave",
            lambda _target: self.scenes_list.drag_unhighlight_row()
        )
        row.add_controller(drop_controller)

        return row

    def on_drop_move(self, _drop, value, _x, y):
        target_row = self.scenes_list.get_row_at_y(y)
        target_index = target_row.get_index()

        # If value or the target row is null, do not accept the drop
        if not value or not target_row:
            return False

        logger.info(f"Move \"{value.scene.title}\" into \"{self._chapter.title}\" at {target_index}")
        value.scene.move_to_chapter(self._chapter, target_index)

    def on_drop_remove(self, _drop, value, _x, _y):
        # If value is null, do not accept the drop
        if not value:
            return False

        logger.info(f"Remove \"{value.scene.title}\" from \"{self._chapter.title}\"")
        self._chapter.remove_scene(value.scene)

        return True

    def on_drag_prepare(self, _source, x, y, row):
        value = GObject.Value()
        value.init(SceneCard)
        value.set_object(row.get_child())

        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin(self, _source, drag, row):
        _got_bounds, _x, _y, width, height = row.get_bounds()

        # Prepare the row
        drag_row = Gtk.ListBoxRow()
        temp_card = SceneCard(row.scene)
        temp_card.hide_suffix()
        drag_row.set_child(temp_card)

        # Prepare the widget
        drag_widget = Gtk.ListBox()
        drag_widget.set_size_request(width, height)
        drag_widget.add_css_class("boxed-list")
        drag_widget.append(drag_row)
        drag_widget.drag_highlight_row(drag_row)

        # Configure the icon
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(drag_widget)

        self.remove_scene_grp.show()

    def on_drag_end(self, _source, _drag, _x, _y):
        self.remove_scene_grp.hide()

    @Gtk.Template.Callback()
    def on_assign_scene_clicked(self, _button):
        logger.info("Assign")
        dialog = ScrptSelectScenesDialog(self._chapter.manuscript.scenes)
        dialog.choose(self, None, self.on_assign_scene_replied)

    def on_assign_scene_replied(self, dialog, task):
        response = dialog.choose_finish(task)
        if response == 'done':
            scene = dialog.get_selected_scene()
            logger.info(f"Adding {scene.title}")
            self._chapter.add_scene(scene)

    @Gtk.Template.Callback()
    def on_delete_chapter_activated(self, _button):
        """Handle a request to delete the scene."""
        logger.info(f"Delete {self._chapter.title}")
        dialog = Adw.AlertDialog(
            heading="Delete chapter?",
            body=f"This action can not be undone! Are you sure you want to delete the chapter \"{self._chapter.title}\" ? All the scenes associated to it will be left unassigned.",
            close_response="cancel",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.choose(self, None, self.on_delete_response_selected)

    def on_delete_response_selected(self, _dialog, task):
        """Handle the response to the confirmation dialog."""
        response = _dialog.choose_finish(task)
        if response == "delete":
            # Delete the chapter
            self._chapter.delete()

            # Return to listing the chapters
            self.get_parent().pop()

