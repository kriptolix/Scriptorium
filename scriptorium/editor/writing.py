# writing.py
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

from gi.repository import Gtk, GObject, Pango
from gi.repository import Adw
from .model import Chapter
from .scene import SceneCard

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/writing.ui")
class EditorWritingView(Adw.Bin):
    __gtype_name__ = "EditorWritingView"

    # The manuscript
    manuscript = None

    # The scene that was previously displayed, used to trigger a save when switching
    previous_scene = None

    list_view = Gtk.Template.Child()
    item_factory = Gtk.Template.Child()
    text_view = Gtk.Template.Child()
    label_words = Gtk.Template.Child()
    chapters_drop_down = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        buffer = self.text_view.get_buffer()

        # Create the tags for the buffer
        buffer.create_tag('em', style=Pango.Style.ITALIC)

        # Connect a signal to refresh the word count
        buffer.connect("changed", self.on_buffer_changed)

        self.chapters_drop_down.connect("notify::selected-item", self.on_selected_item)
        self.item_factory.connect("setup", self.on_setup_item)
        self.item_factory.connect("bind", self.on_bind_item)

    def bind_to_manuscript(self, manuscript):
        self.manuscript = manuscript

        list_store_expression = Gtk.PropertyExpression.new(
            Chapter,
            None,
            "title",
        )
        self.chapters_drop_down.set_expression(list_store_expression)
        self.chapters_drop_down.set_model(manuscript.chapters)

    def on_selected_item(self, _drop_down, _selected_item):
        selected_chapter = _drop_down.get_selected_item()
        logger.info(f"Chapter selected: {selected_chapter.title}")

        # Connect the new list of scenes
        selection_model = Gtk.SingleSelection(model=selected_chapter.scenes)
        selection_model.connect("selection-changed", self.on_selection_changed)
        self.list_view.set_model(selection_model)

        # Select the first one by default
        selection_model.emit("selection-changed", 0, 1)

    def on_setup_item(self, _, list_item):
        list_item.set_child(SceneCard())

    def on_bind_item(self, _, list_item):
        scene = list_item.get_item()
        scene_card = list_item.get_child()
        scene_card.set_property('scene_title', scene.title)
        scene_card.set_property('scene_synopsis', scene.synopsis)

    def on_selection_changed(self, selection, position, n_items):
        buffer = self.text_view.get_buffer()
        selected_scene = selection.get_selected_item()
        logger.info(f"Scene selected: {selected_scene.title}")

        # We don't want undo to span across scenes
        buffer.begin_irreversible_action()

        # If there was a scene displayed, save it first!
        if self.previous_scene:
            self.previous_scene.save_from_buffer(buffer)

        # Delete previous content
        start_iter, end_iter = buffer.get_bounds()
        buffer.delete(start_iter, end_iter)

        # Load the scene
        selected_scene.load_into_buffer(buffer)

        # Finish
        buffer.end_irreversible_action()

        # This will be our new previous scene
        self.previous_scene = selected_scene


    def on_buffer_changed(self, buffer):
        start_iter, end_iter = buffer.get_bounds()
        content = buffer.get_text(start_iter, end_iter, False)
        words = len(content.split())
        self.label_words.set_label(str(words))
