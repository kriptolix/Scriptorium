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

from pathlib import Path
from gi.repository import GObject, Gio
import yaml
import logging
import uuid
import git
from .chapter import Chapter
from .scene import Scene
from .entity import Entity

logger = logging.getLogger(__name__)


class Manuscript(GObject.Object):
    """A manuscript is a collection of scenes and chapters."""

    # Properties of the manuscript
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)
    cover = GObject.Property(type=str)

    # The base directory of the manuscript
    _base_directory = None
    _base_directory_img = None
    _base_directory_scenes = None

    # The scenes contained in the manuscript
    scenes: Gio.ListStore

    def __init__(self, library, manuscript_path, **kwargs):
        """Create a new manuscript."""
        super().__init__(**kwargs)

        # Keep track of the attributes
        self._library = library
        self._base_directory = manuscript_path
        self._base_directory_images = manuscript_path / Path("images")
        self._base_directory_scenes = manuscript_path / Path("scenes")

        # Create the containers for all the main concepts
        self._entities = Gio.ListStore.new(item_type=Entity)
        self._chapters = Gio.ListStore.new(item_type=Chapter)
        self.scenes = Gio.ListStore.new(item_type=Scene)

        # If the manuscript has been initialised, load the content
        if self._base_directory.exists():
            # Initialise the interface for tracking versions of the manuscript
            self._repo = git.Repo(self._base_directory)

            # Load the description file from disk
            self.load_from_disk()

    @property
    def repo(self):
        """Return a pointer to the Git repository of the manuscript."""
        return self._repo

    @GObject.Property(type=str)
    def identifier(self):
        """The unique identifier of the manuscript."""
        return self._base_directory.name

    @GObject.Property(type=Gio.ListStore)
    def entities(self):
        """The entities of the manuscript."""
        return self._entities

    @GObject.Property(type=Gio.ListStore)
    def chapters(self):
        """The chapters contained in the manuscript."""
        return self._chapters

    @property
    def library(self):
        """The library associated to this manuscript."""
        return self._library

    def init(self):
        """Initialise a freshly created manuscript."""
        if self._base_directory.exists():
            raise Exception("The directory is already initialised.")

        # Create the directories and init the repo
        self._base_directory.mkdir()
        self._repo = git.Repo.init(self._base_directory)
        self._base_directory_images.mkdir()
        self._base_directory_scenes.mkdir()

        # Save the empty project
        yaml_file_path = self.save_to_disk()

        # Create a commit
        self.repo.index.add(yaml_file_path)
        self.repo.index.add(self._base_directory_images)
        self.repo.index.add(self._base_directory_scenes)
        self.repo.index.commit(f"Created manuscript \"{self.title}\"")

    def get_cover_path(self):
        if self.cover is None or self.cover == '':
            return None

        img_path = self._base_directory_images / Path(self.cover)
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

        return yaml_file.resolve()

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
        for scene in data["scenes"]:
            logger.debug(f"Loading scene: {scene['title']}")
            scene_entry = Scene(manuscript=self,
                                identifier=scene["identifier"],
                                base_path=self._base_directory_scenes)
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
        """Return one of the scene of the manuscript."""
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
        # Create the scene and add it to the list
        identifier = str(uuid.uuid4())
        new_scene = Scene(self, identifier,
                          self._base_directory / Path("scenes"))
        new_scene.title = title
        new_scene.synopsis = synopsis
        self.scenes.append(new_scene)

        # Finish the creation of the scene
        new_scene.init()

    def create_chapter(self, title: str, synopsis: str = ""):
        """Create a new chapter."""
        # Create the chapter and add it to the list
        new_chapter = Chapter(self)
        new_chapter.title = title
        new_chapter.synopsis = synopsis
        self.chapters.append(new_chapter)

    def splice_chapters(self, source_chapter, target_chapter):
        """Move the source chapter to the position target chapter is at."""
        # Start by finding the positions of each chapter
        found_source, source_position = self.chapters.find(source_chapter)
        found_target, target_position = self.chapters.find(target_chapter)
        if not found_source or not found_target:
            raise KeyError("Could not find the chapters to swap")

        # Now move the source where the target used to be located
        self.chapters.remove(source_position)
        self.chapters.insert(target_position, source_chapter)

