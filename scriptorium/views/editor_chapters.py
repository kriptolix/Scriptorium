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

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_chapters.ui")
class ScrptChaptersPanel(Adw.NavigationPage):
    """Panel to list all the scenes and edit their content."""

    __gtype_name__ = "ScrptChaptersPanel"
    __title__ = "Chapters"
    __icon_name__ = "edit-symbolic"
    __description__ = "Edit the content of the chapters"

    navigation = Gtk.Template.Child()
    chapters_list = Gtk.Template.Child()
    show_sidebar_button = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)
        self._manuscript = editor.manuscript

        self.chapters_list.bind_model(editor.manuscript.chapters,
                                    self.on_add_scene_to_list)

    @Gtk.Template.Callback()
    def on_listbox_row_activated(self, _selected_row, scene_card):
        logger.info("Click")

    @Gtk.Template.Callback()
    def on_add_chapter_clicked(self, _button):
        logger.info("Add chapter")

    def bind_side_bar_button(self, split_view):
        """Connect the button to collapse the sidebar."""
        split_view.bind_property(
            "show_sidebar",
            self.show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE
        )

    def on_add_scene_to_list(self, scene):
        """Add the new scene to the list."""
        scene_card = SceneCard(scene)
        return scene_card

