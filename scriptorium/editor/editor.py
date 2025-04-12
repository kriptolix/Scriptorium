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

from .writing import EditorWritingView
from .plotting import EditorPlottingView
from .formatting import EditorFormattingView

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/editor/editor.ui")
class EditorNavigationPage(Adw.NavigationPage):
    __gtype_name__ = "EditorNavigationPage"

    # The manuscript the editor is connected to
    manuscript = GObject.Property(type=Manuscript)

    # Instances of all the facets for the manuscript
    plotting = Gtk.Template.Child()
    writing = Gtk.Template.Child()
    formatting = Gtk.Template.Child()

    # The stack controlling them
    stack = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Keep an eye for changes to the manuscript base path
        self.connect('notify::manuscript', self.on_manuscript_changed)

    def on_manuscript_changed(self, _manuscript, _other):
        """
        Called when the editor is connected to a new manuscript
        """

        # Load the book content for the writing tab
        self.writing.bind_to_manuscript(self.manuscript)
        self.plotting.bind_to_manuscript(self.manuscript)
        self.formatting.bind_to_manuscript(self.manuscript)

        # Open the plotting tab by default
        self.stack.set_visible_child_name('plotting')
