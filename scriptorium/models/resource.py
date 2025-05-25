from gi.repository import Gtk, GObject, Gio
from pathlib import Path

class Resource(GObject.Object):

    # The unique identifier of the resource
    identifier = GObject.Property(type=str)

    # The title of the resource
    title = GObject.Property(type=str)

    # The description of the resource
    synopsis = GObject.Property(type=str)

    def __init__(self, project, identifier: str):
        """Create a resource."""
        super().__init__()
        self.identifier = identifier
        self._project = project

    @property
    def project(self):
        # The project the resource is part of
        return self._project

    @property
    def data_files(self):
        # An eventual list of data files associated with the resource
        return []

    def to_dict(self):
        """Serialize the content of the resource as JSON"""
        return {
            "a": "Resource",
            "identifier": self.identifier,
            "title": self.title,
            "synopsis": self.synopsis,
        }

    def from_dict(self, data):
        """Serialize the content of the resource as JSON"""
        self.title = data["title"]
        self.synopsis = data["synopsis"]


