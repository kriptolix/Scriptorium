# editor_plotting.py
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

from gi.repository import Adw, Gtk, GObject, Gio, Gdk
from .scene import SceneCard
from .chapter_column import ChapterColumn

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/editor_plotting.ui")
class EditorPlottingView(Adw.Bin):
    __gtype_name__ = "EditorPlottingView"

    chapter_columns = Gtk.Template.Child()
    chapter_column_factory = Gtk.Template.Child()

    def bind_to_manuscript(self, manuscript):
        logger.info(f'Connect to manuscript {manuscript}')
        self.manuscript = manuscript

        self.chapter_column_factory.connect("setup", self.on_setup_item)
        self.chapter_column_factory.connect("bind", self.on_bind_item)

        selection_model = Gtk.NoSelection(model=manuscript.chapters)
        self.chapter_columns.set_model(selection_model)

    def on_setup_item(self, _, list_item):
        list_item.set_child(ChapterColumn())

    def on_bind_item(self, _, list_item):
        chapter = list_item.get_item()
        chapter_column = list_item.get_child()
        chapter_column.connect_to_chapter(chapter)

