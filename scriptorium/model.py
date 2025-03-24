import os
import json
from pathlib import Path
from gi.repository import Gtk, GObject, Gio
import yaml

from .utils import html_to_buffer, buffer_to_html

import logging
logger = logging.getLogger(__name__)

class Scene(GObject.Object):
    identifier = GObject.Property(type=str)
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)
    _chapter = None

    _scene_path = None

    def __init__(self, identifier:str, base_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.identifier = identifier

        scene_path = base_path / Path(f'{self.identifier}.html')
        self._scene_path = scene_path.resolve()

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

    def metadata(self):
        """
        Return the metadata as a map
        """
        data = {
            'title': self.title,
            'synopsis': self.synopsis,
            'identifier': self.identifier,
        }
        return data

    def load_into_buffer(self, buffer: Gtk.TextBuffer):
        logger.info(f'Loading info buffer from {self._scene_path}')

        # Load the content of the file and push to the buffer
        html_content = self.to_html()
        html_to_buffer(html_content, buffer)

    def save_from_buffer(self, buffer: Gtk.TextBuffer):
        logger.info(f'Saving buffer to {self._scene_path}')

        # Write the content of the buffer
        html_content = buffer_to_html(buffer)
        Path(self._scene_path).write_text(html_content)

    def to_html(self):
        """
        Get the HTML payload for the scene
        """
        logger.info(f'Loading raw HTML from {self._scene_path}')

        # Check if we can do that
        if not Path(self._scene_path).exists():
            raise FileNotFoundError(f'Could not open {self._scene_path}')

        html_content = Path(self._scene_path).read_text()
        return html_content

class Chapter(GObject.Object):
    # Properties of the chapter
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    # The scenes contained in this chapter
    scenes: Gio.ListStore

    _manuscript = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scenes = Gio.ListStore.new(item_type=Scene)

    def remove_scene(self, scene):
        """
        Remove a scene from the chapter
        """
        found, position = self.scenes.find(scene)
        if found:
            self.scenes.remove(position)
            scene.set_chapter(None)
        else:
            logger.warning(f'Could not find {scene}')

    def add_scene(self, scene, position: int = 0):
        """
        Add scene to the chapter
        """
        if position >= 0:
            self.scenes.insert(position, scene)
        else:
            self.scenes.append(scene)
        scene.set_chapter(self)

    def to_html(self):
        """
        Get the HTML payload for the chapter
        """
        content = []
        for scene in self.scenes:
            content.append(scene.to_html())
        return '\n'.join(content)

    def metadata(self):
        """
        Return the metadata as a map
        """
        data = {
            'title': self.title,
            'synopsis': self.synopsis,
            'scenes': [s.metadata() for s in self.scenes],
        }
        return data

    def set_manuscript(self, manuscript):
        self._manuscript = manuscript

    def get_manuscript(self):
        return self._manuscript

class Manuscript(GObject.Object):
    # Properties of the manuscript
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)
    cover = GObject.Property(type=str)

    # The base directory of the manuscript
    _base_directory = None

    # The chapters contained in the manuscript
    chapters: Gio.ListStore

    # A special chapter for scenes that are not assigned to any chapter
    unassigned: Chapter

    def __init__(self, manuscript_path, **kwargs):
        super().__init__(**kwargs)

        # Keep track of the attributes
        self._base_directory = manuscript_path

        # Create the list of chapters
        self.chapters = Gio.ListStore.new(item_type=Chapter)

        # Create the chapter
        self.unassigned = Chapter()
        self.unassigned.title = 'Unassigned scenes'

        # Load the description file from disk
        self.load_from_disk()

    def get_cover_path(self):
        if self.cover is None:
            return None

        img_path = self._base_directory / Path('img') / Path(self.cover)
        return img_path.resolve()


    def metadata(self):
        """
        Return the metadata as a map
        """
        data = {
            'title': self.title,
            'synopsis': self.synopsis,
            'chapters': [chapter.metadata() for chapter in self.chapters],
        }

        # If a cover has been set save it
        if self.cover is not None:
            data['cover'] = self.cover

        return data

    def save_to_disk(self):
        """
        Save the content of the manuscript as a file
        """
        data = self.metadata()

        yaml_file = self._base_directory / Path('manuscript.yml')
        with yaml_file.open(mode='w') as file:
            yaml.safe_dump(data, file, width=80, indent=2, sort_keys=True)

    def load_from_disk(self):
        """
        Load the content of the manuscript from a file
        """
        yaml_file = self._base_directory / Path('manuscript.yml')
        with yaml_file.open('r') as file:
            data = yaml.safe_load(file)

        self.title = data['title']
        self.synopsis = data['synopsis']
        self.cover = data.get('cover', None)
        for chapter in data['chapters']:
            logger.debug(f"Adding chapter: {chapter['title']}")
            chapter_entry = Chapter()
            chapter_entry.title = chapter['title']
            chapter_entry.synopsis = chapter['synopsis'].replace('\n', ' ')
            for scene in chapter['scenes']:
                logger.debug(f"Adding scene: {scene['title']}")
                scenes_dir = self._base_directory / Path('scenes')
                scene_entry = Scene(identifier=scene['identifier'], base_path=scenes_dir)
                scene_entry.title = scene['title']
                scene_entry.synopsis = scene['synopsis'].replace('\n', ' ')
                chapter_entry.add_scene(scene_entry)
            self.add_chapter(chapter_entry)

    def add_chapter(self, chapter, position: int = 0):
        """
        Add chapter to the manuscript
        """
        if position >= 0:
            self.chapters.insert(position, chapter)
        else:
            self.chapters.append(chapter)
        chapter.set_manuscript(self)

    def splice_chapters(self, source_chapter, target_chapter):
        """
        Move the source chapter to the position target chapter is at
        """
        # Start by finding the positions of each chapter
        found_source, source_position = self.chapters.find(source_chapter)
        found_target, target_position = self.chapters.find(target_chapter)
        if not found_source or not found_target:
            raise KeyError(f'Could not find the chapters to swap')

        # Now move the source where the target used to be located
        self.chapters.remove(source_position)
        self.chapters.insert(target_position, source_chapter)


class Library(object):
    """
    The library is the collection of manuscripts
    """
    # The base directory where all the manuscripts are located
    _base_directory: Path = None

    # Map of manuscripts
    manuscripts: Gio.ListStore

    def __init__(self, base_directory: str):
        # Keep track of attributes
        self._base_directory = Path(base_directory)

        # Initialise the list store
        self.manuscripts = Gio.ListStore.new(item_type=Manuscript)

        # Perform a scan of the data directory
        self._scan_datadir()

    def _scan_datadir(self):
        logger.info(f'Scanning content of {self._base_directory}')

        # Create one manuscript entry per directory
        for directory in self._base_directory.iterdir():
            logger.info(f'Adding manuscript {directory.name}')
            manuscript = Manuscript(directory)
            self.manuscripts.append(manuscript)

