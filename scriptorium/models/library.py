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
"""Model for storing information about manuscripts and their content."""

from pathlib import Path
from gi.repository import Gtk, GObject, Gio
import yaml
from scriptorium.utils import html_to_buffer, buffer_to_html
import logging
import uuid
import git

from .manuscript import Manuscript

logger = logging.getLogger(__name__)


class Library(GObject.Object):
    """The library is the collection of manuscripts."""

    # Map of manuscripts
    manuscripts: Gio.ListStore = Gio.ListStore.new(item_type=Manuscript)

    def __init__(self, base_directory: str):
        """Create an instance of the library for the target folder."""
        # Keep track of attributes
        self._base_directory = Path(base_directory)

        # Create one manuscript entry per directory
        logger.info(f"Scanning content of {self._base_directory}")
        for directory in self._base_directory.iterdir():
            logger.info(f"Adding manuscript {directory.name}")
            manuscript = Manuscript(directory)
            self.manuscripts.append(manuscript)

    @property
    def base_directory(self) -> Path:
        """The base directory where all the manuscripts are located."""
        return self._base_directory

    def create_manuscript(self, title: str, synopsis: str = None):
        logger.info("Create manuscript")

