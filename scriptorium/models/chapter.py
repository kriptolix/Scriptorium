# models/chapter.py
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
import uuid
from pathlib import Path

import git
import yaml
from gi.repository import Gio, GObject, Gtk
from .resource import Resource
from .commit_message import CommitMessage
from .scene import Scene

logger = logging.getLogger(__name__)


class Chapter(Resource):
    """A chapter is a list of scenes."""
    __gtype_name__ = "Chapter"

    scenes = GObject.Property(type=Gio.ListStore)

    def __init__(self, project, identifier):
        """Create a new instance of Chapter."""
        super().__init__(project, identifier)
        self.scenes = Gio.ListStore.new(item_type=Scene)

    def remove_scene(self, scene: Scene):
        """Remove a scene from the chapter."""
        found, position = self.scenes.find(scene)
        if found:
            self.scenes.remove(position)
        else:
            logger.warning(f"Could not find {scene}")

    def add_scene(self, scene: Scene, position: int = None):
        """Add an existing scene to the chapter."""
        if position is not None and position >= 0:
            self.scenes.insert(position, scene)
        else:
            self.scenes.append(scene)

    def to_html(self):
        """Return the HTML payload for the chapter."""
        content = []
        for scene in self.scenes:
            content.append(scene.to_html())
        return "\n".join(content)

