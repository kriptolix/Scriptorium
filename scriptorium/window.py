# window.py
#
# Copyright 2025 Unknown
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

# Default status: show the gallery of books, a plus button on top left
# and the title "Scriptorium"
# People click on one of the book to switch mode. Using + opens a simple
# dialog to ask for the name and create a new book

# In editor mode the + is replaced by a X to close the book and return select
# a different one from the gallery

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/library.ui")
class Library(Adw.NavigationPage):
    __gtype_name__ = "Library"

    flowbox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.flowbox.connect('child-activated', self.on_manuscript_activated)

        for i in range(10):
            manuscript = Manuscript()
            self.flowbox.append(manuscript)

    def on_manuscript_activated(self, _flowbox, manuscript):
        self.get_parent().push_by_tag('page-2')

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/page2.ui")
class PageSecond(Adw.NavigationPage):
    __gtype_name__ = "PageSecond"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/page2_tab1.ui")
class PageSecondFirstTab(Adw.Bin):
    __gtype_name__ = "PageSecondFirstTab"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/manuscript.ui")
class Manuscript(Gtk.FlowBoxChild):
    __gtype_name__ = "Manuscript"

    cover = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cover.set_resource("/com/github/cgueret/Scriptorium/cover.png")

@Gtk.Template(resource_path='/com/github/cgueret/Scriptorium/ui/window.ui')
class ScriptoriumWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ScriptoriumWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

