# views/editor_chapters_details.py
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
from scriptorium.models import Scene

from scriptorium.globals import BASE

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_chapters_details.ui")
class ScrptChaptersDetailsPanel(Adw.NavigationPage):
    __gtype_name__ = "ScrptChaptersDetailsPanel"

    edit_title = Gtk.Template.Child()
    edit_synopsis = Gtk.Template.Child()
    scenes_list = Gtk.Template.Child()
    assign_remove_stack = Gtk.Template.Child()
    remove_scene_button = Gtk.Template.Child()

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
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
        chapter.bind_property(
            "synopsis",
            self.edit_synopsis,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        self.scenes_list.bind_model(
            chapter.scenes,
            lambda scene: SceneCard(scene, can_move=True, can_activate=False)
        )

        self.scenes_list.connect(
            "start-drag",
            lambda x:
                self.assign_remove_stack.set_visible_child_name("remove_scene")
        )
        self.scenes_list.connect(
            "stop-drag",
            lambda x:
                self.assign_remove_stack.set_visible_child_name("assign_scene")
        )

    @Gtk.Template.Callback()
    def on_droptarget_drop(self, _target, _scene, _x, _y):
        # We do not need to do anything special, just accept the drop
        return True

    @Gtk.Template.Callback()
    def on_assign_scene_clicked(self, _button):
        logger.info("Assign")

        def handle_response(dialog, task):
            response = dialog.choose_finish(task)
            if response == "done":
                scene = dialog.get_selected_scene()
                logger.info(f"Adding {scene.title}")
                self._chapter.add_scene(scene)

        dialog = ScrptSelectScenesDialog(self._chapter.project.scenes)
        dialog.choose(self, None, handle_response)

    @Gtk.Template.Callback()
    def on_delete_chapter_activated(self, _button):
        """Handle a request to delete the scene."""
        logger.info(f"Delete {self._chapter.title}")
        dialog = Adw.AlertDialog(
            heading="Delete chapter?",
            body=f'This action can not be undone! Are you sure you want to delete the chapter "{self._chapter.title}" ? All the scenes associated to it will be left unassigned.',
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
            self._chapter.project.delete_resource(self._chapter)

            # Return to listing the chapters
            self.get_parent().pop()

