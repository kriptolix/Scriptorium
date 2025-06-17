# writer_popover.py
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

# Code inspired from Eloquent:
# https://github.com/sonnyp/Eloquent/blob/main/src/widgets/SuggestionPopover.js

from gi.repository import Adw, Gtk, GObject, GLib
from scriptorium.globals import BASE

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/widgets/writer_popover.ui")
class WriterPopover(Gtk.Popover):
    __gtype_name__ = "WriterPopover"

    category = GObject.Property(type=str)
    description = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

