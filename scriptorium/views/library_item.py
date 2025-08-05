# library/manuscript.py
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
from gi.repository import Gtk
from gi.repository import GObject
from scriptorium.globals import BASE

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/library_item.ui")
class LibraryItem(Gtk.Box):
    __gtype_name__ = "LibraryItem"

    cover_picture = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    cover = GObject.Property(type=str)
    title = GObject.Property(type=str)

    _can_be_opened_handler_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def bind(self, project):
        self._project = project

        # Connect a handler to update the icon when the project can be opened
        if self._can_be_opened_handler_id is not None:
            project.disconnect(self._can_be_opened_handler_id)
        self._can_be_opened_handler_id = project.connect(
            "notify::can-be-opened",
            lambda _src, _value: self.refresh_display()
        )

        # Set the icon now and keep an eye on cover changes
        self.refresh_display()

    def refresh_display(self):
        # Update the title of the project
        self.title = self._project.title

        # See if we can display a cover or not (to signal a broken project)
        if not self._project.can_be_opened:
            self.stack.set_visible_child_name("broken")
        else:
            # We need to open the project to be able to see the cover
            if not self._project.is_opened:
                self._project.open()

            # Connect a notification in case the cover is changed
            self._project.manuscript.connect(
                "notify::cover", lambda _src, _val: self.refresh_display()
            )

            cover = self._project.manuscript.cover
            if cover is not None and cover != '':
                cover_image = self._project.get_resource(cover)
                self.cover_picture.set_paintable(cover_image.texture)
                self.stack.set_visible_child_name("cover")
            else:
                self.stack.set_visible_child_name("ok")

        # Finally see if we have a cover to show

    def on_cover_changed(self, _cover, _other):
        if self.cover is not None:
            # Load the image
            self.cover_picture.set_filename(self.cover)
            self.stack.set_visible_child_name("cover")
        else:
            # Add a place holder
            self.cover_label.set_label(self.title)
            self.stack.set_visible_child_name("label")

