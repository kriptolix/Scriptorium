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

from gi.repository import Adw, GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/manuscript.ui")
class Manuscript(Gtk.FlowBoxChild):
    __gtype_name__ = "Manuscript"

    cover = Gtk.Template.Child()

    manuscript_identifier = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cover.set_resource("/com/github/cgueret/Scriptorium/cover.png")

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/library.ui")
class LibraryNavigationPage(Adw.NavigationPage):
    __gtype_name__ = "LibraryNavigationPage"

    # The base path of all the manuscripts
    manuscripts_base_path = GObject.Property(type=str)

    flowbox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.flowbox.connect('child-activated', self.on_child_activated)

        self.connect('showing', self.on_showing)


    def on_showing(self, _window):
        """Called when the library is displayed"""
        self.flowbox.remove_all()
        for i in range(5):
            manuscript = Manuscript()
            manuscript.set_property('manuscript_identifier', 'dating_at_a_convention')
            self.flowbox.append(manuscript)

    def on_child_activated(self, _flowbox, manuscript):
        """Called when a manuscript is selected"""
        manuscript_identifier = manuscript.get_property('manuscript_identifier')
        logger.info(f'Open {manuscript_identifier}')

        # Set which Manuscript to load in the editor
        manuscript_path = Path(self.manuscripts_base_path) / Path(manuscript_identifier)
        self.get_parent().find_page('editor').set_property('manuscript_path', manuscript_path.resolve())

        # Switch to the editor navigation page
        self.get_parent().push_by_tag('editor')

