from gi.repository import GObject, Gio
from pathlib import Path

class Resource(GObject.Object):
    __gtype_name__ = "Resource"

    # The unique identifier of the resource
    identifier = GObject.Property(type=str)

    # The title of the resource
    title = GObject.Property(type=str)

    # The description of the resource
    synopsis = GObject.Property(type=str)

    # A signal to inform that the resource has been deleted
    deleted = GObject.Signal()

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

    @property
    def references(self):
        """Provide a list of other resources referencing that one."""
        output = set()

        all_resources = self._project.resources
        for other in all_resources:
            # We skip checking ourselves
            if other == self:
                continue

            for prop in GObject.list_properties(type(other)):
                if isinstance(prop, GObject.ParamSpecObject):
                    # Check if the use is a direct assignment
                    if prop.value_type == Resource.__gtype__:
                        if other.get_property(prop.name) == self:
                            output.append(other)
                    # Or if it is found in a list
                    elif prop.value_type == Gio.ListStore.__gtype__:
                        list_store = other.get_property(prop.name)
                        accepted_item_type = list_store.get_item_type()
                        resource_type = self.__gtype__
                        if resource_type.is_a(accepted_item_type):
                            found, position = list_store.find(self)
                            if found:
                                output.append(other)

        return output


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


