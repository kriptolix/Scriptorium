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

from gi.repository import Adw, Gtk, GObject

from .globals import BASE
from .scene import SceneCard
from .writer import Writer
from .editor_writing_details import ScrptWritingDetailsPanel
from .dialog_add_scene import ScrptAddSceneDialog

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/editor/editor_writing.ui")
class ScrptWritingPanel(Adw.NavigationPage):
    """Panel to list all the scenes and edit their content."""

    __gtype_name__ = "ScrptWritingPanel"

    scenes_list = Gtk.Template.Child()
    navigation: Adw.NavigationView = Gtk.Template.Child()
    show_sidebar_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        # Create an instance of the writer dialog
        self.writer_dialog = Writer()

        # Let users switch to edit mode when clicking anywhere on the scene
        self.scenes_list.connect("row-activated", self.on_row_activated)

    @GObject.Property
    def icon_name(self):
        """Return the name of the icon for this panel."""
        return "edit-symbolic"

    @GObject.Property
    def description(self):
        """Return the description for this panel."""
        return "Edit the content of the scenes"

    def bind_side_bar_button(self, split_view):
        """Connect the button to collapse the sidebar."""
        split_view.bind_property(
            "show_sidebar",
            self.show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE
        )

    def bind_to_manuscript(self, manuscript):
        """Connect the panel to the manuscript."""
        self._manuscript = manuscript
        self.scenes_list.bind_model(manuscript.scenes, self.bind_card)

    def bind_card(self, scene):
        """Bind a scene card to a scene."""
        scene_card = SceneCard(scene)

        # Connect the button to switching to the editor view
        scene_card.edit_button.connect("clicked", self.on_edit_scene, scene)

        return scene_card

    def on_edit_scene(self, _button, scene):
        """Switch to editing the scene that has been selected."""
        logger.info(f"Open editor for {scene.title}")

        writing_details = ScrptWritingDetailsPanel(scene)
        self.navigation.push(writing_details)

    def on_row_activated(self, _selected_row, scene_card):
        """Switch to the editing mode if a row is clicked."""
        scene_card.edit_button.emit("clicked")

    def on_add_scene(self, dialog, _task):
        response = dialog.choose_finish(_task)
        if response == "add":
            logger.info(f"Add scene {dialog.title}: {dialog.synopsis}")
            self._manuscript.create_scene(dialog.title, dialog.synopsis)

    @Gtk.Template.Callback()
    def on_add_scene_clicked(self, _button):
        logger.info("Open dialog to add scene")
        dialog = ScrptAddSceneDialog()
        response = dialog.choose(self, None, self.on_add_scene)
        logger.info(response)
