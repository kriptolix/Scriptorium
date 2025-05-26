# views/editor_formatting.py
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

from gi.repository import Adw, Gtk, Gio, GObject
from scriptorium.models import Chapter
from scriptorium.globals import BASE
import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_formatting.ui")
class ScrptFormattingPanel(Adw.NavigationPage):

    __gtype_name__ = "ScrptFormattingPanel"
    __title__ = "Formatting"
    __icon_name__ = "open-book-symbolic"
    __description__ = "Preview and modify the formatting"

    web_view = Gtk.Template.Child()
    button_next = Gtk.Template.Child()
    button_previous = Gtk.Template.Child()
    chapters_drop_down = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        super().__init__(**kwargs)
        self._editor = editor

        self.chapters_drop_down.connect(
            "notify::selected-item",
            self.on_selected_item
        )

        list_store_expression = Gtk.PropertyExpression.new(
            Chapter,
            None,
            "title",
        )
        self.chapters_drop_down.set_expression(list_store_expression)
        self.chapters_drop_down.set_model(editor.project.manuscript.chapters)

        self._position = 0

    def on_selected_item(self, _drop_down, _selected_item):
        selected_chapter = _drop_down.get_selected_item()
        if selected_chapter is None:
            self.button_previous.set_sensitive(False)
            self.button_next.set_sensitive(False)
            return

        logger.info(f"Chapter selected: {selected_chapter.title}")

        # Get all the HTML content from the model
        content = selected_chapter.to_html()

        # Instantiate the template for the rendering
        emulator_html = Gio.File.new_for_uri(
            "resource://com/github/cgueret/Scriptorium/views/editor_formatting.html"
        )
        html_content = emulator_html.load_contents()[1].decode()
        html_content = html_content.replace("{content}", content)

        # Load the content
        self.web_view.load_html(html_content)

        # Find the position of the chapter
        chapters = self._editor.project.manuscript.chapters
        found, self._position = chapters.find(selected_chapter)

        # Enable the buttons
        self.button_previous.set_sensitive(self._position > 0)
        self.button_next.set_sensitive(self._position < chapters.get_n_items() - 1)

    @Gtk.Template.Callback()
    def on_button_next_clicked(self, _button):
        logger.info("Move to next chapter")
        self.chapters_drop_down.set_selected(self._position + 1)

    @Gtk.Template.Callback()
    def on_button_previous_clicked(self, _button):
        logger.info("Move to previous chapter")
        self.chapters_drop_down.set_selected(self._position - 1)

