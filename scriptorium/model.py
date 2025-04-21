# model.py
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
from .utils import html_to_buffer, buffer_to_html
import logging
import uuid

logger = logging.getLogger(__name__)


class Scene(GObject.Object):
    """A scene is a basic building block of manuscripts."""

    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    _chapter = None

    _scene_path = None

    def __init__(self, manuscript, identifier: str, base_path: Path):
        """Create a scene."""
        super().__init__()
        self._identifier = identifier
        self._manuscript = manuscript

        # The content of the scene
        scene_path = base_path / Path(f"{self.identifier}.html")
        self._scene_path = scene_path.resolve()

        # If the content file does not exist we create it
        if not self._scene_path.exists():
            self._scene_path.touch()

    @GObject.Property(type=GObject.Object)
    def manuscript(self):
        """Return the manuscript the scene is associated to."""
        return self._manuscript

    @GObject.Property(type=str)
    def identifier(self):
        """Return the identifier of the scene."""
        return self._identifier

    def delete(self):
        """Delete the scene."""
        found, position = self.manuscript.scenes.find(self)
        if not found:
            raise ValueError("The scene is already deleted")

        # Remove the scene from the list of scenes
        self.manuscript.scenes.remove(position)

        # Remove all references in chapters
        for chapter in self.manuscript.chapters:
            in_chapter, chapter_position = chapter.scenes.find(self)
            if in_chapter:
                chapter.scenes.remove(chapter_position)

        # Delete the file on disk
        if self._scene_path.exists():
            self._scene_path.unlink()

    def set_chapter(self, chapter):
        self._chapter = chapter

    def get_chapter(self):
        return self._chapter

    def move_to_chapter(self, chapter, position: int = 0):
        # Remove the scene from its current chapter
        current_chapter = self.get_chapter()
        current_chapter.remove_scene(self)

        # Insert into the new chapter
        chapter.add_scene(self, position)

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

    def to_html(self):
        """Return the HTML payload for the scene."""
        logger.info(f"Loading raw HTML from {self._scene_path}")

        # Check if we can do that
        if not Path(self._scene_path).exists():
            raise FileNotFoundError(f"Could not open {self._scene_path}")

        html_content = Path(self._scene_path).read_text()
        return html_content


class Chapter(GObject.Object):
    """A chapter is a list of scenes."""

    # Properties of the chapter
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    def __init__(self, manuscript, **kwargs):
        """Create a new instance of Chapter."""
        super().__init__(**kwargs)
        self._manuscript = manuscript
        self._scenes = Gio.ListStore.new(item_type=Scene)

    @GObject.Property(type=GObject.Object)
    def manuscript(self):
        """Return the manuscript the scene is associated to."""
        return self._manuscript

    @GObject.Property(type=Gio.ListStore)
    def scenes(self):
        """Return the list of scenes."""
        return self._scenes

    def remove_scene(self, scene: Scene):
        """Remove a scene from the chapter."""
        found, position = self.scenes.find(scene)
        if found:
            self._scenes.remove(position)
            scene.set_chapter(None)
        else:
            logger.warning(f"Could not find {scene}")

    def add_scene(self, scene: Scene, position: int = None):
        """Add an existing scene to the chapter."""
        if position is not None and position >= 0:
            self._scenes.insert(position, scene)
        else:
            self._scenes.append(scene)
        scene.set_chapter(self)

    def to_html(self):
        """Return the HTML payload for the chapter."""
        content = []
        for scene in self.scenes:
            content.append(scene.to_html())
        return "\n".join(content)


class Manuscript(GObject.Object):
    # Properties of the manuscript
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)
    cover = GObject.Property(type=str)

    # The base directory of the manuscript
    _base_directory = None

    # The chapters contained in the manuscript
    chapters: Gio.ListStore

    # The scenes contained in the manuscript
    scenes: Gio.ListStore

    def __init__(self, manuscript_path, **kwargs):
        super().__init__(**kwargs)

        # Keep track of the attributes
        self._base_directory = manuscript_path

        # Create the list of chapters
        self.chapters = Gio.ListStore.new(item_type=Chapter)

        # Create the list of scenes
        self.scenes = Gio.ListStore.new(item_type=Scene)

        # Load the description file from disk
        self.load_from_disk()

    def get_cover_path(self):
        if self.cover is None:
            return None

        img_path = self._base_directory / Path("img") / Path(self.cover)
        return img_path.resolve()

    def save_to_disk(self):
        """Save the content of the manuscript as a file."""
        # Create the YAML data structure
        data = {
            "manuscript": {
                "title": self.title,
                "synopsis": self.synopsis,
                "cover": self.cover,
            },
            "scenes": [
                {
                    "title": scene.title,
                    "synopsis": scene.synopsis,
                    "identifier": scene.identifier,
                }
                for scene in self.scenes
            ],
            "chapters": [
                {
                    "title": chapter.title,
                    "synopsis": chapter.synopsis,
                    "scenes": [scene.identifier for scene in chapter.scenes],
                }
                for chapter in self.chapters
            ],
        }

        # Save to disk
        yaml_file = self._base_directory / Path("manuscript.yml")
        with yaml_file.open(mode="w") as file:
            yaml.safe_dump(data, file, indent=2, sort_keys=True)

    def load_from_disk(self):
        """Load the content of the manuscript from a file."""
        # Load the YAML data
        yaml_file = self._base_directory / Path("manuscript.yml")
        with yaml_file.open("r") as file:
            data = yaml.safe_load(file)

        # Load basic information
        self.title = data["manuscript"]["title"]
        self.synopsis = data["manuscript"]["synopsis"]
        self.cover = data["manuscript"].get("cover", None)

        # Load all the scenes
        scenes_dir = self._base_directory / Path("scenes")
        for scene in data["scenes"]:
            logger.debug(f"Loading scene: {scene['title']}")
            scene_entry = Scene(manuscript=self,
                                identifier=scene["identifier"],
                                base_path=scenes_dir)
            scene_entry.title = scene["title"]
            scene_entry.synopsis = scene["synopsis"].replace("\n", " ")
            self.add_scene(scene_entry)

        # Load all the chapters
        for chapter in data["chapters"]:
            logger.debug(f"Loading chapter: {chapter['title']}")
            chapter_entry = Chapter(manuscript=self)
            chapter_entry.title = chapter["title"]
            chapter_entry.synopsis = chapter["synopsis"].replace("\n", " ")
            self.add_chapter(chapter_entry)
            for scene_identifier in chapter["scenes"]:
                scene = self.get_scene(scene_identifier)
                chapter_entry.add_scene(scene)

    def get_scene(self, identifier):
        for scene in self.scenes:
            if scene.identifier == identifier:
                return scene
        return None

    def add_chapter(self, chapter: Chapter, position: int = None):
        """Add an existing chapter to the manuscript."""
        if position is not None and position >= 0:
            self.chapters.insert(position, chapter)
        else:
            self.chapters.append(chapter)

    def add_scene(self, scene: Scene, position: int = None):
        """Add an existing scene to the manuscript."""
        if position is not None and position >= 0:
            self.scenes.insert(position, scene)
        else:
            self.scenes.append(scene)

    def create_scene(self, title: str, synopsis: str = ""):
        """Create a new scene."""
        identifier = uuid.uuid4()
        new_scene = Scene(self, identifier,
                          self._base_directory / Path("scenes"))
        new_scene.title = title
        new_scene.synopsis = synopsis
        self.scenes.append(new_scene)

    def splice_chapters(self, source_chapter, target_chapter):
        """Move the source chapter to the position target chapter is at."""
        # Start by finding the positions of each chapter
        found_source, source_position = self.chapters.find(source_chapter)
        found_target, target_position = self.chapters.find(target_chapter)
        if not found_source or not found_target:
            raise KeyError(f"Could not find the chapters to swap")

        # Now move the source where the target used to be located
        self.chapters.remove(source_position)
        self.chapters.insert(target_position, source_chapter)


class Library(GObject.Object):
    """The library is the collection of manuscripts."""

    # The base directory where all the manuscripts are located
    _base_directory: Path = None

    # Map of manuscripts
    manuscripts: Gio.ListStore = Gio.ListStore.new(item_type=Manuscript)

    def __init__(self, base_directory: str):
        # Keep track of attributes
        self._base_directory = Path(base_directory)

        # Perform a scan of the data directory
        self._scan_datadir()

    def _scan_datadir(self):
        logger.info(f"Scanning content of {self._base_directory}")

        # Create one manuscript entry per directory
        for directory in self._base_directory.iterdir():
            logger.info(f"Adding manuscript {directory.name}")
            manuscript = Manuscript(directory)
            self.manuscripts.append(manuscript)

