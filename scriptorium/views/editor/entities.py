# editor_entity.py
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


from gi.repository import Adw, Gtk, GObject

import logging
logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/editor_entity.ui")
class ScrptEntityPanel(Adw.Bin):
    __gtype_name__ = "ScrptEntityPanel"

    @GObject.Property
    def icon_name(self):
        """Return the name of the icon for this panel."""
        return "system-users-symbolic"

    @GObject.Property
    def title(self):
        """Return the title for this panel."""
        return "People"

    @GObject.Property
    def description(self):
        """Return the description for this panel."""
        return ""

    def bind_to_manuscript(self, manuscript):
        self._manuscript = manuscript
