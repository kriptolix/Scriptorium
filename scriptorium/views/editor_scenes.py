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

from gi.repository import Adw, Gtk

from scriptorium.globals import BASE
from scriptorium.widgets import SceneCard
from scriptorium.dialogs import ScrptAddDialog
from .editor_scenes_details import ScrptWritingDetailsPanel
from scriptorium.models import Scene

from scriptorium.dialogs import Writer

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

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        self.editor = editor

        self.scenes_list.bind_model(
            self.editor.project.scenes,
            lambda scene: SceneCard(scene=scene, can_activate=True)
        )

        self.connect("map", self.on_map)

    def on_map(self, _widget):
        test_scene_id = "9ede0795-6ee2-486d-8b94-4c95cef254c1"
        writer = Writer(self.editor.project.get_resource(test_scene_id))
        #writer.load_scene(self.editor.project.get_resource(test_scene_id))
        writer.present(self)

    @Gtk.Template.Callback()
    def on_listbox_row_activated(self, _list_box, row):
        """Switch to the editing mode if a row is clicked."""
        scene = row.get_child().scene
        logger.info(f"Open editor for {scene.title}")

        writing_details = ScrptWritingDetailsPanel(scene)
        self.navigation.push(writing_details)

    @Gtk.Template.Callback()
    def on_add_scene_clicked(self, _button):
        logger.info("Open dialog to add scene")

        def handle_response(dialog, task):
            response = dialog.choose_finish(task)
            if response == "add":
                logger.info(f"Add scene {dialog.title}: {dialog.synopsis}")
                self.editor.project.create_resource(Scene, dialog.title, dialog.synopsis)

        dialog = ScrptAddDialog("scene")
        dialog.choose(self, None, handle_response)
