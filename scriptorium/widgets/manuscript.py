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
import logging
from gi.repository import Gtk
from gi.repository import GObject

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/widgets/manuscript.ui")
class ManuscriptItem(Gtk.Box):
    __gtype_name__ = "ManuscriptItem"

    cover_picture = Gtk.Template.Child()
    cover_label = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    cover = GObject.Property(type=str)
    title = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect('notify::cover', self.on_cover_changed)

    def on_cover_changed(self, _cover, _other):
        logger.info(self.cover)
        if self.cover is not None:
            # Load the image
            self.cover_picture.set_filename(self.cover)
            self.stack.set_visible_child_name('cover')
        else:
            # Add a place holder
            self.cover_label.set_label(self.title)
            self.stack.set_visible_child_name('label')

