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
from scriptorium.widgets import ChapterCard, CardsList, SceneCard
from scriptorium.dialogs import ScrptAddDialog

from .editor_chapters_details import ScrptChaptersDetailsPanel

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
    box = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)
        self._manuscript = editor.manuscript

        self.chapters_list.bind_model(editor.manuscript.chapters,
                                    self.on_add_chapter_to_list)

        cards_list = CardsList()
        cards_list.bind_model(editor.manuscript.chapters[0].scenes, SceneCard)
        self.box.append(cards_list)

        cards_list = CardsList()
        cards_list.bind_model(editor.manuscript.chapters[1].scenes, SceneCard)
        self.box.append(cards_list)

    @Gtk.Template.Callback()
    def on_listbox_row_activated(self, _widget, selected_row):
        chapter = selected_row.get_child().chapter
        logger.info(f"Clicked on chapter \"{chapter.title}\"")
        chapter_details_panel = ScrptChaptersDetailsPanel(chapter)
        self.navigation.push(chapter_details_panel)

    @Gtk.Template.Callback()
    def on_add_chapter_clicked(self, _button):
        logger.info("Open dialog to add a new chapter")
        dialog = ScrptAddDialog("chapter")
        dialog.choose(self, None, self.on_add_chapter)

    def on_add_chapter(self, dialog, _task):
        response = dialog.choose_finish(_task)
        if response == "add":
            logger.info(f"Add chapter {dialog.title}: {dialog.synopsis}")
            self._manuscript.create_chapter(dialog.title, dialog.synopsis)

    def bind_side_bar_button(self, split_view):
        """Connect the button to collapse the sidebar."""
        split_view.bind_property(
            "show_sidebar",
            self.show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE
        )

    def on_add_chapter_to_list(self, chapter):
        """Add the new chapter to the list."""
        card = ChapterCard(chapter)
        return card

