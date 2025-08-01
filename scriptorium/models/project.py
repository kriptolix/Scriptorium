import logging
from gi.repository import GObject, Gio, Gtk
import git
import yaml
from pathlib import Path
import uuid

from .resource import Resource
from .image import Image
from .chapter import Chapter
from .scene import Scene
from .entity import Entity
from .manuscript import Manuscript
from .link import Link

logger = logging.getLogger(__name__)

CLASSES = {
    "Scene": Scene,
    "Entity": Entity,
    "Chapter": Chapter,
    "Image": Image,
    "Manuscript": Manuscript
}


class Project(GObject.Object):
    __gtype_name__ = "Project"

    manuscript = GObject.Property(type=Resource)

    def __init__(self, manuscript_path):
        """Create a resource."""
        super().__init__()

        # Keep track of the attributes
        self._base_directory = Path(manuscript_path)

        # All the resources
        self._resources = Gio.ListStore(item_type=Resource)

        # If the manuscript has been initialised, load the content
        if self._base_directory.exists():
            # Initialise the interface for tracking versions of the manuscript
            self._repo = git.Repo(self._base_directory)

            # Load the description file from disk
            self.load_from_disk()
        else:
            # Let's create the project
            self._base_directory.mkdir()
            self._repo = git.Repo.init(self._base_directory)

            # Do a first commit
            yaml_file_path = self.save_to_disk()
            self.repo.index.add(yaml_file_path)
            self.repo.index.commit(f'Created project')

    @property
    def base_directory(self) -> Path:
        """The base directory."""
        return self._base_directory

    @property
    def repo(self):
        """Return a pointer to the Git repository of the manuscript."""
        return self._repo

    @GObject.Property(type=Gio.ListStore)
    def scenes(self):
        """The scenes of the manuscript."""
        model = Gtk.FilterListModel(
            model=self._resources,
            filter=Gtk.CustomFilter.new(lambda x: isinstance(x, Scene))
        )
        return model

    @GObject.Property(type=Gio.ListStore)
    def entities(self):
        """The scenes of the manuscript."""
        model = Gtk.FilterListModel(
            model=self._resources,
            filter=Gtk.CustomFilter.new(lambda x: isinstance(x, Entity))
        )
        return model

    @GObject.Property(type=Gio.ListStore)
    def links(self):
        """The scenes of the manuscript."""
        model = Gtk.FilterListModel(
            model=self._resources,
            filter=Gtk.CustomFilter.new(lambda x: isinstance(x, Link))
        )
        return model

    @property
    def identifier(self):
        """Return the project identifier."""
        return self._base_directory.name

    def create_resource(self, cls, title: str, synopsis: str = ""):
        # Create the resource
        resource = cls(self, str(uuid.uuid4()))
        resource.title = title
        resource.synopsis = synopsis
        self._resources.append(resource)

        # Keep track of the creation in the project history
        yaml_file_path = self.save_to_disk()
        self.repo.index.add(yaml_file_path)
        for data_file in resource.data_files:
            self.repo.index.add(data_file)
        self.repo.index.commit(f'Created new {cls.__gtype_name__} "{title}"')

        return resource

    def delete_resource(self, resource):
        """Delete the resource."""
        logger.info(f"Delete {resource}")

        # Find it
        found, position = self._resources.find(resource)
        if not found:
            raise ValueError("The resource does not exist")

        # Remove the resource
        self._resources.remove(position)

        # Remove all references to it
        for other in self._resources:
            for prop in GObject.list_properties(type(other)):
                if isinstance(prop, GObject.ParamSpecObject):
                    # If it was a direct assignment, set it to None instead
                    if prop.value_type == Resource.__gtype__:
                        if other.get_property(prop.name) == resource:
                            other.set_property(prop.name, None)
                    # If the resource was in a list, remove it from it
                    elif prop.value_type == Gio.ListStore.__gtype__:
                        list_store = other.get_property(prop.name)
                        accepted_item_type = list_store.get_item_type()
                        resource_type = resource.__gtype__
                        if resource_type.is_a(accepted_item_type):
                            found, position = list_store.find(resource)
                            if found:
                                list_store.remove(position)

        # Delete the file on disk (if any)
        for data_file in resource.data_files:
            if data_file.exists():
                data_file.unlink()

        # Keep track of the deletion of this scene in the history
        yaml_file_path = self.save_to_disk()
        self.repo.index.add(yaml_file_path)
        for data_file in resource.data_files:
            self.repo.index.remove(data_file)
        self.repo.index.commit(f'Deleted resource "{resource.identifier}"')

    def load_from_disk(self):
        # Load the YAML data
        yaml_file = self._base_directory / Path("manuscript.yml")
        with yaml_file.open("r") as file:
            yaml_data = yaml.safe_load(file)

        # Load all the resources
        for resource_data in yaml_data["resources"]:
            if resource_data["a"] == "Link":
                continue

            self.get_resource(resource_data["identifier"], yaml_data)

        # Load the pointer to the manuscript
        manuscript_id = yaml_data["manuscript"]
        self.manuscript = self.get_resource(manuscript_id, yaml_data)

    def save_to_disk(self):
        """Save all the content of the project to disk."""

        # Serialize all the resources and their properties
        resources = []
        for resource in self._resources:
            cls = type(resource)
            entry = {
                "a": cls.__gtype_name__,
            }
            props = GObject.list_properties(cls)
            for prop in props:
                if isinstance(prop, GObject.ParamSpecString):
                    entry[prop.name] = resource.get_property(prop.name)
                elif isinstance(prop, GObject.ParamSpecInt):
                    entry[prop.name] = resource.get_property(prop.name)
                elif isinstance(prop, GObject.ParamSpecObject):
                    value = resource.get_property(prop.name)
                    if value is not None:
                        if isinstance(value, Resource):
                            entry[prop.name] = value.identifier
                        elif isinstance(value, Gio.ListStore):
                            values = [v.identifier for v in value]
                            entry[prop.name] = values
            resources.append(entry)

        # Save to disk
        yaml_file = self._base_directory / Path("manuscript.yml")
        with yaml_file.open(mode="w") as file:
            yaml.safe_dump(
                {
                    "version": 1,
                    "manuscript": self.manuscript.identifier,
                    "resources": resources
                }, file, indent=2, sort_keys=True
            )

        # Return the name of the project file
        return yaml_file.resolve()

    def get_resource(self, identifier: str, yaml_data=None):
        """Return one of the resource and load it if needed."""
        # Check if we already loaded the resource
        for resource in self._resources:
            if resource.identifier == identifier:
                return resource
        logger.debug(f"Could not find {identifier}, trying to load it")

        # Find the YAML data block
        resource_data = None
        if yaml_data:
            for data in yaml_data["resources"]:
                if data["identifier"] == identifier:
                    resource_data = data
        if resource_data is None:
            logger.error(f"Could not find {identifier} in the YAML file")
            return None

        # Give up if we don't know how to create the resource
        if resource_data["a"] not in CLASSES:
            logger.error(f"Can't create a {resource_data['a']}")
            return None

        # Instantiate the resource
        cls = CLASSES[resource_data["a"]]
        identifier = resource_data["identifier"]
        resource = cls(self, identifier)

        # Try to restore its properties
        props = GObject.list_properties(cls)
        for prop in props:
            if prop.name not in resource_data:
                continue
            value = resource_data[prop.name]
            if isinstance(prop, GObject.ParamSpecString):
                resource.set_property(prop.name, value)
            elif isinstance(prop, GObject.ParamSpecInt):
                resource.set_property(prop.name, value)
            elif isinstance(prop, GObject.ParamSpecObject):
                if prop.value_type == Resource.__gtype__:
                    resource.set_property(
                        prop.name,
                        self.get_resource(value, yaml_data)
                    )
                elif prop.value_type == Gio.ListStore.__gtype__:
                    for v in value:
                        store = resource.get_property(prop.name)
                        store.append(self.get_resource(v, yaml_data))

        self._resources.append(resource)
        return resource
