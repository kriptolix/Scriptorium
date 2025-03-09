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

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/editor_plotting.ui")
class EditorPlottingView(Adw.Bin):
    __gtype_name__ = "EditorPlottingView"

    boxes = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def bind_to_manuscript(self, manuscript):
        logger.info(f'Connect to manuscript {manuscript}')
        self.manuscript = manuscript

        for chapter in manuscript.chapters:
            column = chapter.title
            column_box = self.create_column(chapter)
            self.boxes.append(column_box)


    def create_column(self, chapter):
        logger.info(f'Create {chapter.title}')
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_vexpand(True)

        header = Gtk.Label(label=chapter.title)
        header.set_margin_top(6)
        header.set_margin_bottom(6)
        vbox.append(header)

        # Create Selection Model
        selection_model = Gtk.NoSelection.new(chapter.scenes)

        # Create ListView
        list_view = Gtk.ListView.new(selection_model, Gtk.SignalListItemFactory.new())
        list_view.set_vexpand(True)
        list_view.set_hexpand(True)

        # Set factory for rendering items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_setup_item)
        factory.connect("bind", self.on_bind_item)
        list_view.set_factory(factory)

        vbox.append(list_view)

        return vbox

    def on_setup_item(self, _, list_item):
        list_item.set_child(SceneCard())

    def on_bind_item(self, _, list_item):
        scene = list_item.get_item()
        scene_card = list_item.get_child()
        scene_card.set_property('scene_title', scene.title)
        scene_card.set_property('scene_synopsis', scene.synopsis)


