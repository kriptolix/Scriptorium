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

from gi.repository import Adw, Gtk, Pango

from .globals import BASE
from .scene import SceneCard

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/editor/editor_writing.ui")
class ScrptChaptersPanel(Adw.Bin):
    """Panel to list all the scenes and edit their content."""

    __gtype_name__ = "ScrptChaptersPanel"

    scenes_list = Gtk.Template.Child()
    navigation = Gtk.Template.Child()
    text_view = Gtk.Template.Child()
    label_words = Gtk.Template.Child()
    edit_scene = Gtk.Template.Child()

    def __init__(self, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)
        text_buffer = self.text_view.get_buffer()

        # Create the tags for the buffer
        text_buffer.create_tag("em", style=Pango.Style.ITALIC)

        # Connect a signal to refresh the word count
        text_buffer.connect("changed", self.on_buffer_changed)

        # Let users switch to edit mode when clicking anywhere on the scene
        self.scenes_list.connect("row-activated", self.on_row_activated)

        # Detect when the editor is getting closed
        self.edit_scene.connect("hiding", self.on_editor_closing)

    def metadata(self):
        """Return the metadata for this panel."""
        return {
            "icon_name": "edit-symbolic",
            "title": "Scenes",
            "description": "Edit the content of the scenes",
        }

    def bind_to_manuscript(self, manuscript):
        """Connect the panel to the manuscript."""
        self._manuscript = manuscript
        self.scenes_list.bind_model(manuscript.scenes,
                                    self.on_add_scene_to_list)

    def on_add_scene_to_list(self, scene):
        """Add the new scene to the list."""
        scene_card = SceneCard(scene)

        # Connect the button to switching to the editor view
        scene_card.edit_button.connect("clicked", self.on_edit_scene, scene)

        return scene_card

    def on_edit_scene(self, _button, scene):
        """Switch to editing the scene that has been selected."""
        logger.info(f"Open editor for {scene.title}")

        # Set the editor title to the title of the scene
        self.edit_scene.set_title(scene.title)

        # Get the text buffer
        text_buffer = self.text_view.get_buffer()

        # Assign the scene to it
        text_buffer.scene = scene

        # We don't want undo to span across scenes
        text_buffer.begin_irreversible_action()

        # Delete previous content
        start_iter, end_iter = text_buffer.get_bounds()
        text_buffer.delete(start_iter, end_iter)

        # Load the scene
        scene.load_into_buffer(text_buffer)

        # Finish
        text_buffer.end_irreversible_action()

        self.navigation.push_by_tag("edit_scene")

    def on_buffer_changed(self, text_buffer):
        """Keep an eye on modifications of the buffer."""
        start_iter, end_iter = text_buffer.get_bounds()
        content = text_buffer.get_text(start_iter, end_iter, False)
        words = len(content.split())
        self.label_words.set_label(str(words))

    def on_row_activated(self, _selected_row, scene_card):
        """Switch to the editing mode if a row is clicked."""
        scene_card.edit_button.emit("clicked")

    def on_editor_closing(self, _page):
        """Perform any action needed when closing the editor."""
        text_buffer = self.text_view.get_buffer()
        logger.info(f"Save content of {text_buffer.scene.title}")
        text_buffer.scene.save_from_buffer(text_buffer)
