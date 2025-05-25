import logging
from gi.repository import Gtk, GObject, Gio
from .resource import Resource
from pathlib import Path

logger = logging.getLogger(__name__)

class Image(Resource):

    def __init__(self, project, identifier: str):
        """Create an image instance."""
        super().__init__(project, identifier)

        base_directory = project.base_directory / Path("images")
        if not base_directory.exists():
            base_directory.mkdir()

    def to_dict(self):
        """Serialize the content of the resource as a dict"""
        pass

    def from_dict(self, data):
        """Parse a serialized JSON content"""
        pass

