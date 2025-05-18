# models/scene.py
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
from scriptorium.utils import html_to_buffer, buffer_to_html
from .commit_message import CommitMessage
from .entity import Entity

import logging

logger = logging.getLogger(__name__)


class Scene(GObject.Object):
    """A scene is a basic building block of manuscripts."""
    __gtype_name__ = "Scene"

    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    def __init__(self, manuscript, identifier: str, base_path: Path):
        """Create a scene."""
        super().__init__()
        self._identifier = identifier
        self._manuscript = manuscript
        self._chapter = None
        self._history = Gio.ListStore.new(item_type=CommitMessage)
        self._entities = Gio.ListStore.new(item_type=Entity)

        # The content of the scene
        scene_path = base_path / Path(f"{self.identifier}.html")
        self._scene_path = scene_path.resolve()

        self._refresh_history()

    @property
    def history(self):
        """Return the history of commits about that scene."""
        return self._history

    @GObject.Property(type=Gio.ListStore)
    def entities(self):
        """Return the entities connected to that scene."""
        return self._entities

    @property
    def scene_path(self):
        """Return the full path to the HTML content of the scene."""
        return self._scene_path

    @GObject.Property(type=GObject.Object)
    def manuscript(self):
        """Return the manuscript the scene is associated to."""
        return self._manuscript

    @GObject.Property(type=str)
    def identifier(self):
        """Return the identifier of the scene."""
        return self._identifier

    @GObject.Property(type=GObject.Object)
    def chapter(self):
        """Return the chapter the scene is associated to, if any."""
        for chapter in self._manuscript.chapters:
            found, _ = chapter.scenes.find(self)
            if found:
                return chapter
        return None

    def connect_to(self, entity):
        """Connect this scene to an entity."""
        if entity not in self.entities:
            self.entities.append(entity)

    def disconnect_from(self, entity):
        """Disconnect this scene from an entity."""
        found, position = self.entities.find(entity)
        if found:
            self.entities.remove(position)

    def init(self):
        """Initialise a new scene."""
        if self._scene_path.exists():
            raise ValueError("The scene is already on disk.")

        # Create the content file for the scene
        self._scene_path.touch()

        # Keep track of the creation of this scene in the history
        yaml_file_path = self._manuscript.save_to_disk()
        self._manuscript.repo.index.add(yaml_file_path)
        self._manuscript.repo.index.add(self._scene_path)
        self._manuscript.repo.index.commit(f"Created new scene \"{self.title}\"")

        # Refresh the history of the scene to reflect the change
        self._refresh_history()

    def delete(self):
        """Delete the scene."""
        found, position = self._manuscript.scenes.find(self)
        if not found:
            raise ValueError("The scene is already deleted")

        # Remove the scene from the list of scenes
        self._manuscript.scenes.remove(position)

        # Remove all references in chapters
        # there should be only one but we test them all to be sure
        for chapter in self._manuscript.chapters:
            in_chapter, chapter_position = chapter.scenes.find(self)
            if in_chapter:
                chapter.scenes.remove(chapter_position)

        # Delete the file on disk
        if self._scene_path.exists():
            self._scene_path.unlink()

        # Keep track of the deletion of this scene in the history
        yaml_file_path = self._manuscript.save_to_disk()
        self._manuscript.repo.index.add(yaml_file_path)
        self._manuscript.repo.index.remove(self._scene_path)
        self._manuscript.repo.index.commit(f"Deleted scene \"{self.title}\"")

    def load_into_buffer(self, buffer: Gtk.TextBuffer):
        """Load the content of a text buffer from disk."""
        logger.info(f"Loading info buffer from {self._scene_path}")

        # Load the content of the file and push to the buffer
        html_content = self.to_html()
        html_to_buffer(html_content, buffer)

    def save_from_buffer(self, buffer: Gtk.TextBuffer):
        """Save the content of a text buffer to disk."""
        logger.info(f"Saving buffer to {self._scene_path}")

        # Write the content of the buffer
        html_content = buffer_to_html(buffer)
        Path(self._scene_path).write_text(html_content)

        # Check if the file has been changed
        repo = self._manuscript.repo
        for d in repo.index.diff(None):
            if str(self._scene_path.resolve()).endswith(d.a_path):
                repo.index.add(self._scene_path)
                repo.index.commit(f"Modified scene \"{self._identifier}\"")
                # Trigger a refresh of the commit history
                self._refresh_history()

    def to_html(self):
        """Return the HTML payload for the scene."""
        logger.info(f"Loading raw HTML from {self._scene_path}")

        # Check if we can do that
        if not Path(self._scene_path).exists():
            raise FileNotFoundError(f"Could not open {self._scene_path}")

        html_content = Path(self._scene_path).read_text()
        return html_content

    def _refresh_history(self):
        self._history.remove_all()
        commits = self._manuscript.repo.iter_commits(all=True,
                                                     paths=self._scene_path)
        for commit in commits:
            datetime = commit.committed_datetime
            message_datetime = datetime.strftime("%A %d %B %Y, %H:%M:%S")
            message = commit.message.strip()
            msg = CommitMessage(message_datetime, message)
            self._history.append(msg)


