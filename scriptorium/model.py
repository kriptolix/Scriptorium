import os
import json
from pathlib import Path
from gi.repository import Gtk, GObject, Gio

from .utils import html_to_buffer, buffer_to_html

import logging
logger = logging.getLogger(__name__)

class Scene(GObject.Object):
    scene_path = GObject.Property(type=str)
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    _buffer: Gtk.TextBuffer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_into_buffer(self, buffer: Gtk.TextBuffer):
        logger.info(f'Loading info buffer from {self.scene_path}')

        # Load the content of the file and push to the buffer
        html_content = self.to_html()
        html_to_buffer(html_content, buffer)

    def save_from_buffer(self, buffer: Gtk.TextBuffer):
        logger.info(f'Saving buffer to {self.scene_path}')

        # Write the content of the buffer
        html_content = buffer_to_html(buffer)
        Path(self.scene_path).write_text(html_content)

    def to_html(self):
        """
        Get the HTML payload for the scene
        """
        logger.info(f'Loading raw HTML from {self.scene_path}')

        # Check if we can do that
        if not Path(self.scene_path).exists():
            raise FileNotFoundError(f'Could not open {scene_path}')

        html_content = Path(self.scene_path).read_text()
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
        scenes_dir = self._base_directory / Path('scenes')
        logger.info(f'Loading content from {self._base_directory}')

        # Load the data for this manuscript
        data_file = self._base_directory / Path('manuscript.json')
        data = json.loads(data_file.read_text())

        # Load the content of the chapters
        for entry in data['chapters']:
            logger.info(f"Adding chapter: {entry['title']}")
            chapter = Chapter(title=entry['title'], synopsis=entry['synopsis'])
            self.chapters.append(chapter)

            for scene_identifier in entry['scenes']:
                logger.info(f"Adding scene: {scene_identifier}")
                scene_path = scenes_dir / Path(f'{scene_identifier}.html')
                scene = Scene(scene_path=scene_path.resolve())
                scene.title = data['scenes'][scene_identifier]['title']
                scene.synopsis = data['scenes'][scene_identifier]['synopsis']
                chapter.scenes.append(scene)

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

