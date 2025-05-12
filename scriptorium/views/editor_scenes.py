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

from gi.repository import Adw, Gtk, GObject, Gdk

from scriptorium.globals import BASE
from scriptorium.widgets import SceneCard, CardsList
from scriptorium.dialogs import Writer, ScrptAddDialog
from .editor_scenes_details import ScrptWritingDetailsPanel

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_scenes.ui")
class ScrptWritingPanel(Adw.NavigationPage):
    """Panel to list all the scenes and edit their content."""

    __gtype_name__ = "ScrptWritingPanel"
    __title__ = "Scenes"
    __icon_name__ = "edit-symbolic"
    __description__ = "Edit the content of the scenes"

    scenes_list = Gtk.Template.Child()
    navigation: Adw.NavigationView = Gtk.Template.Child()
    show_sidebar_button = Gtk.Template.Child()
    # wrap_box = Gtk.Template.Child()
    box = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        self._manuscript = editor.manuscript
        self.scenes_list.bind_model(editor.manuscript.scenes, self.bind_card)

        # Create an instance of the writer dialog
        self.writer_dialog = Writer()

        # Let users switch to edit mode when clicking anywhere on the scene
        self.scenes_list.connect("row-activated", self.on_row_activated)

        self._moved = None
        self._moved_x = None
        self._moved_y = None

        # cards_list = CardsList()
        # cards_list.bind_model(editor.manuscript.scenes, SceneCard)
        # self.box.prepend(cards_list)

        # for scene in editor.manuscript.scenes:
        #    box = Gtk.Box()
        #    box.set_hexpand(True)
        #    box.add_css_class("card")
        #    box.add_css_class("activatable")
        #    card = SceneCard(scene)
        #    box.append(card)
        #    box.card = card

        # Configure it as a drag source
        #    drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        #    drag_source.connect("prepare", self.on_drag_prepare, box)
        #    drag_source.connect("drag-begin", self.on_drag_begin, box)
        #    drag_source.connect("drag-end", self.on_drag_end, box)
        #    box.add_controller(drag_source)

        # Configure it as a drop target
        #    drop_target = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        #    drop_target.connect("drop", self.on_drop, box)
        #    drop_target.connect("motion", self.on_drag_motion, box)
        #    box.add_controller(drop_target)

        #    self.wrap_box.append(box)

    def on_drop(self, _target, value, _x, _y, box):
        logger.info(f"Drop {value} {_y}")

    def on_drag_prepare(self, _source, x, y, box):
        value = GObject.Value()
        value.init(SceneCard)
        value.set_object(box.card)
        self._moved_x = x
        self._moved_y = y

        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin(self, _source, drag, box):
        _got_bounds, _x, _y, width, height = box.get_bounds()

        # Prepare the row
        drag_row = Gtk.ListBoxRow()
        temp_card = SceneCard(box.card.scene)
        temp_card.hide_suffix()
        drag_row.set_child(temp_card)

        # Prepare the widget
        drag_widget = Gtk.ListBox()
        drag_widget.set_size_request(width, height)
        drag_widget.add_css_class("boxed-list")
        drag_widget.append(drag_row)
        drag_widget.drag_highlight_row(drag_row)

        # Configure the icon
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(drag_widget)

        drag.set_hotspot(self._moved_x, self._moved_y)
        self._moved = box

    def on_drag_end(self, _source, _drag, _x, box):
        logger.info("end")
        self._moved = None

    def on_drag_motion(self, _source, _x, y, box):
        _got_bounds, _x, _y, width, height = box.get_bounds()
        prev_box = box if y > height / 2 else box.get_prev_sibling()
        self.wrap_box.reorder_child_after(self._moved, prev_box)
        return Gdk.DragAction.MOVE

    def bind_side_bar_button(self, split_view):
        """Connect the button to collapse the sidebar."""
        split_view.bind_property(
            "show_sidebar",
            self.show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

    def bind_card(self, scene):
        """Bind a scene card to a scene."""
        scene_card = SceneCard(scene)

        # Connect the button to switching to the editor view
        scene_card.edit_button.connect("clicked", self.on_edit_scene, scene)

        return scene_card

    def on_edit_scene(self, _button, scene):
        """Switch to editing the scene that has been selected."""
        logger.info(f"Open editor for {scene.title}")

        writing_details = ScrptWritingDetailsPanel(scene)
        self.navigation.push(writing_details)

    def on_row_activated(self, _list_box, row):
        """Switch to the editing mode if a row is clicked."""
        scene = row.get_child().scene
        logger.info(f"Open editor for {scene.title}")

        writing_details = ScrptWritingDetailsPanel(scene)
        self.navigation.push(writing_details)

    def on_add_scene(self, dialog, _task):
        response = dialog.choose_finish(_task)
        if response == "add":
            logger.info(f"Add scene {dialog.title}: {dialog.synopsis}")
            self._manuscript.create_scene(dialog.title, dialog.synopsis)

    @Gtk.Template.Callback()
    def on_add_scene_clicked(self, _button):
        logger.info("Open dialog to add scene")
        dialog = ScrptAddDialog("scene")
        response = dialog.choose(self, None, self.on_add_scene)
        logger.info(response)

