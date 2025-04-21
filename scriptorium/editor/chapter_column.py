# chapter_column.py
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
from gi.repository import Adw, Gtk, GObject, Gdk

from .model import Chapter
from .scene import SceneCard

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/chapter_column.ui")
class ChapterColumn(Adw.Bin):
    __gtype_name__ = "ChapterColumn"

    scenes_list = Gtk.Template.Child()
    column = Gtk.Template.Child()
    _chapter = None

    # Work around to avoid dragging a column when a scene is picked
    drag_scene = False

    def __init__(self, **kwargs):
        """Create a new instance of the class."""
        super().__init__(**kwargs)

        # We also configure a chapter as a drop source to move them
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_prepare_chapter)
        drag_source.connect("drag-begin", self.on_drag_begin_chapter)
        self.column.add_controller(drag_source)

        # Configure a chapter as drop target for a scene
        drop_target = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop_scene_into_chapter)
        self.column.add_controller(drop_target)

        # Configure the scene list as drop target for insertion into chapters
        drop_target = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop_scene_into_scene)
        self.scenes_list.add_controller(drop_target)

        # Then configure a chapter as drop target for a chapter as well
        drop_target = Gtk.DropTarget.new(Chapter, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop_chapter_into_chapter)
        self.column.add_controller(drop_target)

    def connect_to_chapter(self, chapter: Chapter):
        """Connect the column to a chapter."""
        self._chapter = chapter

        # Set the title of the column
        self.column.set_title(chapter.title)

        # Set the column header text
        text = chapter.synopsis
        if len(chapter.synopsis) > 128:
            text = chapter.synopsis[:128] + "..."
        self.column.set_description(text)

        # Connect the model for the scenes
        self.scenes_list.bind_model(chapter.scenes, self.bind_card)

        drop_controller = Gtk.DropControllerMotion()
        drop_controller.connect("enter", self.on_over_scene_list_row)
        drop_controller.connect("motion", self.on_over_scene_list_row)
        drop_controller.connect("leave", self.on_leave_scene_list_row)
        self.scenes_list.add_controller(drop_controller)

    def on_over_scene_list_row(self, _target, _x, _y):
        """Highlight the row currently being moved over."""
        row = self.scenes_list.get_row_at_y(_y)
        self.scenes_list.drag_highlight_row(row)
        return True

    def on_leave_scene_list_row(self, _target):
        """Remove the highlight."""
        self.scenes_list.drag_unhighlight_row()
        return True

    def bind_card(self, scene):
        """Bind a scene card to a scene."""
        scene_card = SceneCard(scene)
        scene_card.hide_suffix()

        # Enable drag and drop for a scene
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_prepare_scene, scene_card)
        drag_source.connect("drag-begin", self.on_drag_begin_scene, scene_card)
        drag_source.connect("drag-end", self.on_drag_end_scene)
        scene_card.add_controller(drag_source)

        return scene_card

    def on_prepare_chapter(self, _source, _x, _y):
        """Prepare for a DnD by attaching the scene card to the event."""
        if self.drag_scene:
            logger.debug('Blocked')
            return None
        logger.debug("Prepare chapter")
        # Set our chapter as the data being moved
        value = GObject.Value()
        value.init(Chapter)
        value.set_object(self._chapter)
        return Gdk.ContentProvider.new_for_value(value)

    def on_prepare_scene(self, _source, _x, _y, scene_card):
        """Prepare for a DnD by attaching the scene card to the event."""
        logger.debug("Prepare scene")
        # Set it as the value
        value = GObject.Value()
        value.init(SceneCard)
        value.set_object(scene_card)
        self.drag_scene = True
        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin_chapter(self, _source, drag):
        """Handle the chapter starts being dragged around."""
        logger.debug("Drag chapter")
        # Take a snaphot of the card and set it as icon
        snapshot = Gtk.WidgetPaintable.new(self)
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(Gtk.Picture.new_for_paintable(snapshot))

    def on_drag_begin_scene(self, drag_source, drag, scene_card):
        """Handle the scene starts being dragged around."""
        logger.debug("Drag scene")
        # Take a snaphot of the card and set it as icon
        snapshot = Gtk.WidgetPaintable.new(scene_card)
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(Gtk.Picture.new_for_paintable(snapshot))

    def on_drag_end_scene(self, drag_source, drag, _x):
        """Handle the scene starts being dragged around."""
        logger.debug("Drag scene end")
        self.drag_scene = False

    def on_drop_scene_into_scene(self, _drop, scene_card, _x, y):
        """Insert a scene into a chapter at an indicated location."""
        # Get the scene and target position
        scene = scene_card.get_scene()
        row = self.scenes_list.get_row_at_y(y)
        target_position = row.get_index()

        # Move the scene card
        logger.info(f"Insert {scene} in {self._chapter} at {target_position}")
        scene.move_to_chapter(self._chapter, target_position)

    def on_drop_scene_into_chapter(self, _drop, scene_card, _x, _y):
        """Drop a scene into a chapter."""
        # Get the scene
        scene = scene_card.get_scene()

        # Move the scene card
        logger.info(f"Drop {scene} into {self._chapter}")
        scene.move_to_chapter(self._chapter, -1)

    def on_drop_chapter_into_chapter(self, _drop, chapter, _x, _y):
        """Drop a chapter where another chapter is located."""
        # Move the chapter
        logger.info(f"Move {chapter.title} where {self._chapter.title} is")
        chapter.manuscript.splice_chapters(chapter, self._chapter)

