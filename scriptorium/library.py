# window.py
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

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/manuscript.ui")
class Manuscript(Gtk.FlowBoxChild):
    __gtype_name__ = "Manuscript"

    cover = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cover.set_resource("/com/github/cgueret/Scriptorium/cover.png")

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/library.ui")
class LibraryNavigationPage(Adw.NavigationPage):
    __gtype_name__ = "LibraryNavigationPage"

    flowbox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.flowbox.connect('child-activated', self.on_manuscript_activated)

        self.connect('showing', self.on_showing)


    def on_showing(self, _window):
        """Called when the library is displayed"""
        print(self.get_parent())

        self.flowbox.remove_all()
        for i in range(5):
            manuscript = Manuscript()
            self.flowbox.append(manuscript)

    def on_manuscript_activated(self, _flowbox, manuscript):
        """Called when a manuscript is selected"""
        self.get_parent().push_by_tag('editor')

