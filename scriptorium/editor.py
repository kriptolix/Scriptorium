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

class CustomModel(Gtk.StringList, Gtk.SectionModel):
    # A chapter is defined as the start and end index of the scenes
    _chapters = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_content(self, manuscript_path):
        self._base_directory = manuscript_path
        logger.info(f'Loading content from {self._base_directory}')

        data_file = self._base_directory / pathlib.Path('manuscript.json')
        self.data = json.loads(data_file.read_text())

        for chapter in self.data['chapters']:
            for scene in chapter['scenes']:
                self.append(scene)

    def get_scene_title(self, scene_identifier):
        return self.data['scenes'][scene_identifier]['title']

    def get_scene_synopsis(self, scene_identifier):
        return self.data['scenes'][scene_identifier]['synopsis']

    def do_get_section(self, position):
        start = position
        end = start + 4
        return (start, end)

    def get_header_label(self, thing):
        print (thing.get_string())

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/editor.ui")
class EditorNavigationPage(Adw.NavigationPage):
    __gtype_name__ = "EditorNavigationPage"

    # The base path of the manuscript behing edited
    manuscript_path = GObject.Property(type=str)

    # The custom data model representing the Manuscript
    custom_model = CustomModel()

    # Instances of all the facets for the manuscript
    writing = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect('showing', self.on_showing)

    def on_showing(self, _window):
        """Called when the Editor is displayed"""

        self.custom_model.load_content(self.manuscript_path)

        # Load the book content for the writing tab
        self.writing.connect_to_model(self.custom_model)


