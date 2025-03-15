# editor.py
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
import pathlib
import json

# The editor interface is using the model for a manuscript
from .model import Manuscript

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/editor.ui")
class EditorNavigationPage(Adw.NavigationPage):
    __gtype_name__ = "EditorNavigationPage"

    # The base path of the manuscript behing edited
    manuscript_path = GObject.Property(type=str)

    # The custom data model representing the Manuscript
    manuscript = None

    # Instances of all the facets for the manuscript
    plotting = Gtk.Template.Child()
    writing = Gtk.Template.Child()
    formatting = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect('showing', self.on_showing)

    def on_showing(self, _window):
        """Called when the Editor is displayed"""

        # Load the book content for the writing tab
        if self.manuscript is None:
            self.manuscript = Manuscript(self.manuscript_path)
            self.writing.bind_to_manuscript(self.manuscript)
            self.plotting.bind_to_manuscript(self.manuscript)


