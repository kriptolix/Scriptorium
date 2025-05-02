# models/library.py
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
"""A Library is a collection of manuscripts."""

from pathlib import Path
from gi.repository import GObject, Gio
import logging
import uuid
import shutil

from .manuscript import Manuscript

logger = logging.getLogger(__name__)


class Library(GObject.Object):
    """The library is the collection of manuscripts."""

    def __init__(self, base_directory: str):
        """Create an instance of the library for the target folder."""
        # Keep track of attributes
        self._base_directory = Path(base_directory)

        # List of manuscripts
        self._manuscripts = Gio.ListStore.new(item_type=Manuscript)

        # Create one manuscript entry per directory
        logger.info(f"Scanning content of {self._base_directory}")
        for directory in self._base_directory.iterdir():
            logger.info(f"Adding manuscript {directory.name}")
            manuscript = Manuscript(self, directory)
            self.manuscripts.append(manuscript)

    @GObject.Property(type=Gio.ListStore)
    def manuscripts(self) -> Gio.ListStore:
        """List of manuscripts."""
        return self._manuscripts

    @property
    def base_directory(self) -> Path:
        """The base directory where all the manuscripts are located."""
        return self._base_directory

    def create_manuscript(self, title: str, synopsis: str = None):
        """Create a new manuscript."""
        logger.info("Create manuscript")

        # Create a new identifier, we use a UUID so that several manuscripts
        # may share the same name
        identifier = str(uuid.uuid4())

        # Create the manuscript
        path = self.base_directory / Path(identifier)
        manuscript = Manuscript(self, path)
        manuscript.title = title
        manuscript.synopsis = synopsis
        manuscript.init()

        # Add it to the list
        self.manuscripts.append(manuscript)

    def delete_manuscript(self, manuscript):
        """Delete the manuscript from disk."""

        found, position = self.manuscripts.find(manuscript)
        if found:
            # Remove from the library
            self.manuscripts.remove(position)

            # Delete all the content on disk
            path = self.base_directory / Path(manuscript.identifier)
            shutil.rmtree(path)
