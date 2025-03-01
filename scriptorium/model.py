import os
import json
from pathlib import Path

import logging
logger = logging.getLogger(__name__)


class Manuscript(object):
    """
    A manuscript is one particular entry of the library
    """

    # The base directory for this manuscript
    _base_directory: Path = None

    # Store the chapters
    _chapters = {}

    # Store the scenes
    _scenes = {}

    def __init__(self, base_directory: str):
        self._base_directory = base_directory

        self._load_content()

    def _load_content(self):
        """
        Load the content of the manuscript from the directory
        """
        logger.info(f'Loading content from {self._base_directory}')

        # Load all the scenes
        scenes_dir = self._base_directory / Path('scenes')
        for scene_file in scenes_dir.glob('*.md'):
            scene_name = scene_file.name.split('.')[0]
            logger.info(f'Loading scene {scene_name}')
            self._scenes[scene_name] = scene_file.read_text()

        # Load the json description
        data_file = self._base_directory / Path('manuscript.json')
        data = json.loads(data_file.read_text())
        self._chapters = data['chapters']
        logger.info(self._chapters)



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

