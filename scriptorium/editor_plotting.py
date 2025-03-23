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

    def on_setup_item_other(self, _, list_item):
        card = SceneCard()
        list_item.set_child(card)

        # Drag and drop
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_prepare, list_item)
        drag_source.connect("drag-begin", self.on_drag_begin, list_item)
        card.add_controller(drag_source)

        # Configure them as drop target
        drop_target = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop, list_item)
        card.add_controller(drop_target)

    def on_bind_item_other(self, _, list_item):
        scene = list_item.get_item()
        scene_card = list_item.get_child()
        scene_card.set_property('scene_title', scene.title)
        scene_card.set_property('scene_synopsis', scene.synopsis)

    def on_prepare(self, _source, x, y, list_item):
        scene_card = list_item.get_child()

        value = GObject.Value()
        value.init(SceneCard)
        value.set_object(scene_card)

        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin(self, drag_source, drag, list_item):
        scene_card = list_item.get_child()
        snapshot = Gtk.WidgetPaintable.new(list_item.get_child())

        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(Gtk.Picture.new_for_paintable(snapshot))

    def on_drop(self, drop, value, x, y, list_item):
        #target_row = list_view.get_row_at_y(y)
        #target_index = target_row.get_index()
        logger.info(f'Drop {drop}, {value}, {list_item}')

