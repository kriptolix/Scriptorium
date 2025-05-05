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

from scriptorium.globals import BASE
from scriptorium.widgets import SceneCard
from scriptorium.dialogs import Writer, ScrptAddDialog
from .editor_scenes_details import ScrptWritingDetailsPanel

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_scenes.ui")
class ScrptWritingPanel(Adw.NavigationPage):
    """Panel to list all the scenes and edit their content."""

    __gtype_name__ = "ScrptWritingPanel"
    __title__ = "Scenes"
    __icon_name__ = "edit-symbolic"
    __description__ = "Edit the content of the scenes"

    scenes_list = Gtk.Template.Child()
    navigation: Adw.NavigationView = Gtk.Template.Child()
    show_sidebar_button = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        self._manuscript = editor.manuscript
        self.scenes_list.bind_model(editor.manuscript.scenes, self.bind_card)

        # Create an instance of the writer dialog
        self.writer_dialog = Writer()

        # Let users switch to edit mode when clicking anywhere on the scene
        self.scenes_list.connect("row-activated", self.on_row_activated)

    def bind_side_bar_button(self, split_view):
        """Connect the button to collapse the sidebar."""
        split_view.bind_property(
            "show_sidebar",
            self.show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE
        )

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

    def on_row_activated(self, _list_box, row):
        """Switch to the editing mode if a row is clicked."""
        scene = row.get_child().scene
        logger.info(f"Open editor for {scene.title}")

        writing_details = ScrptWritingDetailsPanel(scene)
        self.navigation.push(writing_details)

    def on_add_scene(self, dialog, _task):
        response = dialog.choose_finish(_task)
        if response == "add":
            logger.info(f"Add scene {dialog.title}: {dialog.synopsis}")
            self._manuscript.create_scene(dialog.title, dialog.synopsis)

    @Gtk.Template.Callback()
    def on_add_scene_clicked(self, _button):
        logger.info("Open dialog to add scene")
        dialog = ScrptAddDialog("scene")
        response = dialog.choose(self, None, self.on_add_scene)
        logger.info(response)
