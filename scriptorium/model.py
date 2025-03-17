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

    _scene_path = None

    def __init__(self, identifier:str, base_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.identifier = identifier

        scene_path = base_path / Path(f'{self.identifier}.html')
        self._scene_path = scene_path.resolve()

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
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)
    scenes: Gio.ListStore

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scenes = Gio.ListStore.new(item_type=Scene)

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

class Manuscript(GObject.Object):
    # The base directory of the manuscript
    _base_directory = None

    # Properties of the manuscript
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)
    chapters = Gio.ListStore(item_type=Chapter)

    def __init__(self, manuscript_path, **kwargs):
        super().__init__(**kwargs)

        self._base_directory = manuscript_path
        self.load_from_disk()

    def metadata(self):
        """
        Return the metadata as a map
        """
        data = {
            'title': self.title,
            'synopsis': self.synopsis,
            'chapters': [chapter.metadata() for chapter in self.chapters],
        }
        return data

    def save_to_disk(self):
        """
        Save the content of the manuscript as a file
        """
        data = self.metadata()

        yaml_file = self._base_directory / Path('manuscript.yml')
        with yaml_file.open(mode='w') as file:
            yaml.dump(data, file, width=80, indent=2)

    def load_from_disk(self):
        """
        Load the content of the manuscript from a file
        """
        yaml_file = self._base_directory / Path('manuscript.yml')
        with yaml_file.open('r') as file:
            data = yaml.safe_load(file)

        self.title = data['title']
        self.synopsis = data['synopsis']
        for chapter in data['chapters']:
            logger.info(f"Adding chapter: {chapter['title']}")
            chapter_entry = Chapter()
            chapter_entry.title = chapter['title']
            chapter_entry.synopsis = chapter['synopsis'].replace('\n', ' ')
            for scene in chapter['scenes']:
                logger.info(f"Adding scene: {scene['title']}")
                scenes_dir = self._base_directory / Path('scenes')
                scene_entry = Scene(identifier=scene['identifier'], base_path=scenes_dir)
                scene_entry.title = scene['title']
                scene_entry.synopsis = scene['synopsis'].replace('\n', ' ')
                chapter_entry.scenes.append(scene_entry)
            self.chapters.append(chapter_entry)



class Library(object):
    """
    The library is the collection of manuscripts
    """

    # The base directory where all the manuscripts are located
    _base_directory: Path = None

    # Map of manuscripts
    _manuscripts = {}

    def __init__(self, base_directory: str):
        self._base_directory = Path(base_directory)
        logger.info(self._base_directory)

        # Create one manuscript entry per directory
        for directory in self._base_directory.iterdir():
            self._manuscripts[directory.name] = Manuscript(directory)

