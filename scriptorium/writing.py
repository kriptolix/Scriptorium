# writing.py
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

from gi.repository import Gtk, GObject
from gi.repository import Adw

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/scene.ui")
class SceneCard(Gtk.Box):
    __gtype_name__ = "SceneCard"

    scene_title = GObject.Property(type=str)
    scene_synopsis = GObject.Property(type=str)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/writing.ui")
class Writing(Adw.Bin):
    __gtype_name__ = "Writing"

    list_view = Gtk.Template.Child()
    item_factory = Gtk.Template.Child()
    header_factory = Gtk.Template.Child()



    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def connect_to_model(self, model):
        print ('Reload')
        self.custom_model = model

        self.item_factory.connect("setup", self.on_setup_item)
        self.item_factory.connect("bind", self.on_bind_item)

        self.header_factory.connect("setup", self.on_setup_header)
        self.header_factory.connect("bind", self.on_bind_header)

        selection_model = Gtk.SingleSelection(model=self.custom_model)
        selection_model.connect("selection-changed", self.on_selection_changed)
        self.list_view.set_model(selection_model)

    def on_setup_item(self, _, list_item):
        list_item.set_child(SceneCard())

    def on_bind_item(self, _, list_item):
        item = list_item.get_item()
        scene_card = list_item.get_child()
        scene_title = self.custom_model.get_scene_title(item.get_string())
        scene_card.set_property('scene_title', scene_title)

        scene_synopsis = self.custom_model.get_scene_synopsis(item.get_string())
        scene_card.set_property('scene_synopsis', scene_synopsis)

    def on_setup_header(self, _, list_item):
        list_item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def on_bind_header(self, _, list_item):
        item = list_item.get_item()
        label = list_item.get_child()
        self.custom_model.get_header_label(item)
        label.set_label("Header " + item.get_string())

    def on_selection_changed(self, selection, position, n_items):
        scene_id = self.custom_model.get_string(selection.get_selected())
        logger.info(f"Scene selected: {scene_id}")



