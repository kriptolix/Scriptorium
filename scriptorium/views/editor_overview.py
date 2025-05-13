# plotting_overview.py
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

from gi.repository import Adw, Gtk, GObject
from scriptorium.widgets import ChapterColumn

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/views/editor_overview.ui")
class ScrptOverviewPanel(Adw.NavigationPage):
    __gtype_name__ = "ScrptOverviewPanel"
    __icon_name__ = "view-columns-symbolic"
    __description__ = "Overview of all the content"
    __title__ = "Outline"

    chapter_columns = Gtk.Template.Child()
    chapter_column_factory = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        self._manuscript = editor.manuscript

        self.chapter_column_factory.connect("setup", self.on_setup_item)
        self.chapter_column_factory.connect("bind", self.on_bind_item)

        selection_model = Gtk.NoSelection(model=editor.manuscript.chapters)
        self.chapter_columns.set_model(selection_model)

    def bind_chapter(self, chapter):
        """Bind a scene card to a scene."""
        chapter_card = ChapterColumn(chapter)

        # Connect the button to switching to the editor view
        # scene_card.edit_button.connect("clicked", self.on_edit_scene, scene)

        return chapter_card

    def on_setup_item(self, _, list_item):
        list_item.set_child(ChapterColumn())

    def on_bind_item(self, _, list_item):
        chapter = list_item.get_item()
        chapter_column = list_item.get_child()
        chapter_column.connect_to_chapter(chapter)

