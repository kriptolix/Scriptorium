# editor_chapter.py
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
"""Editor panel to select and work on the chapters."""

import logging

from gi.repository import Adw, Gtk

from scriptorium.globals import BASE
from scriptorium.widgets import ChapterCard
from scriptorium.dialogs import ScrptAddDialog
from scriptorium.models import Chapter

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

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)
        self.editor = editor

        self.chapters_list.bind_model(
            editor.project.manuscript.chapters,
            lambda chapter: ChapterCard(chapter)
        )

    @Gtk.Template.Callback()
    def on_listbox_row_activated(self, _widget, selected_row):
        chapter = selected_row.get_child().chapter
        logger.info(f'Clicked on chapter "{chapter.title}"')
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
            chapter = self.editor.project.create_resource(
                Chapter,
                dialog.title,
                dialog.synopsis
            )
            self.editor.project.manuscript.add_chapter(chapter)

