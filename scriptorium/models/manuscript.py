# models/manuscript.py
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
"""Model for storing information about manuscripts and their content."""

import logging

from pathlib import Path
from gi.repository import GObject, Gio, Gtk
from .chapter import Chapter
from .scene import Scene
from .resource import Resource

logger = logging.getLogger(__name__)


class Manuscript(Resource):
    """A manuscript is a collection of scenes and chapters."""
    __gtype_name__ = "Manuscript"

    # Properties of the manuscript
    content = GObject.Property(type=Gio.ListStore)

    # The identifier of the cover for the manuscript
    cover = GObject.Property(type=str)

    def __init__(self, project, identifier):
        """Create a new manuscript."""
        super().__init__(project, identifier)

        # Create the containers for all the content of the manuscript
        self.content = Gio.ListStore(item_type=Resource)

    def get_cover_path(self):
        if self.cover is None or self.cover == '':
            return None

        img_path = self._base_directory / Path("images") / Path(self.cover)
        return img_path.resolve()

    def add_resource(self, resource: Resource, position: int = None) -> bool:
        """Add an existing resource to the manuscript."""
        # We can only accept either a Chapter or a Scene
        if not isinstance(resource, (Chapter, Scene)):
            return False

        if position is not None and position >= 0:
            self.content.insert(position, resource)
        else:
            self.content.append(resource)

        return True

    def splice_chapters(self, source_chapter, target_chapter):
        """Move the source chapter to the position target chapter is at."""
        # Start by finding the positions of each chapter
        found_source, source_position = self.content.find(source_chapter)
        found_target, target_position = self.content.find(target_chapter)
        if not found_source or not found_target:
            raise KeyError("Could not find the chapters to swap")

        # Now move the source where the target used to be located
        self.content.remove(source_position)
        self.content.insert(target_position, source_chapter)

    def get_content(self) -> list:
        """Return the content of the manuscript as a list of HTML chapters."""

        # Prepare the output
        output = []

        # Create a tree model to iterate over the content
        model = Gtk.TreeListModel.new(
            self.content, False, True,
            lambda item:
            item.content if isinstance(item, (Manuscript, Chapter)) else None
        )

        # Iterate on each row
        previous_resource = None
        previous_depth = None
        chapter_index = 1
        for idx in range(0, model.get_n_items()):
            # See what we have on that row
            row = model.get_row(idx)
            resource = row.get_item()
            depth = row.get_depth()

            # We start something new
            if row.get_depth() == 0:
                if isinstance(resource, Chapter):
                    output.append([f"Chapter {chapter_index}", ""])
                elif isinstance(resource, Scene):
                    # We stitch together the scenes at root level as long as
                    # they come in a sequence
                    logger.info(f"{resource.title} has prev {previous_resource.title}")
                    if not isinstance(previous_resource, Scene) or previous_depth != depth:
                        output.append([f"Chapter {chapter_index}", ""])
                chapter_index += 1

            # Now add the content to the last part of the output
            if isinstance(resource, Scene):
                # If the previous thing was a scene we add a scene separator
                if isinstance(previous_resource, Scene) and previous_depth == depth:
                    output[-1][1] += "<span>...</span>"
                # Add the content of the scene
                output[-1][1] += resource.to_html()
            elif isinstance(resource, Chapter):
                d = row.get_depth()
                output[-1][1] += f"<h{d+1}>{resource.title}</h{d+1}>"

            # Set the previous item as the current one
            previous_resource = resource
            previous_depth = depth

        return output

