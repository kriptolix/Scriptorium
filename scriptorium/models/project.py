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

PROJECT_DESCRIPTION_VERSION = 1


class Project(GObject.Object):
    __gtype_name__ = "Project"

    # The main manuscript used for editing and publishing
    manuscript = GObject.Property(type=Resource)

    # The title for the project
    title = GObject.Property(type=str, default='New project')

    # Can the project be opened?
    can_be_opened = GObject.Property(type=bool, default=False)

    # Is the project opened ?
    is_opened = GObject.Property(type=bool, default=False)

    # The content of the YAML file descriptior
    _yaml_data = None

    def __init__(self, project_path):
        """Create a resource."""
        super().__init__()

        # Keep track of the attributes
        self._base_directory = Path(project_path)

        # All the resources
        self._resources = Gio.ListStore(item_type=Resource)

        # TODO Load the YAML data and extract the project format version
        # Add a bool function to check if up to date
        # Add a function to trigger a migration
        # Push the code below to after any migration has been done

        # Check if this is a directory we need to initialize
        if self._base_directory.exists():
            # Initialise the interface for tracking versions of the manuscript
            self._repo = git.Repo(self._base_directory)

            # Load the YAML data
            self._load_yaml()
        else:
            # Let's create the project
            self._base_directory.mkdir()
            self._repo = git.Repo.init(self._base_directory)

            # Initialise the YAML data
            self._yaml_data = {
                "version": PROJECT_DESCRIPTION_VERSION,
                "manuscript": None,
                "title": self.title,
                "resources": []
            }

            # Do a first commit
            self._save_yaml()
            self.repo.index.commit("Created project")

        # See if we can open the project
        self._set_can_be_opened()

    def _set_can_be_opened(self):
        """Set property to true if the project has the right format."""

        # The initial release of Scriptorium missed a version indicator
        project_version = self._yaml_data.get("version", 0)
        self.can_be_opened = project_version == PROJECT_DESCRIPTION_VERSION

    def migrate(self) -> bool:
        """Migrate the project to the current version of the format."""

        try:
            # The current version is the one in the file or 0 otherwise
            current_version = self._yaml_data.get("version", 0)

            # Hello time travelers! Sorry, can't do anything for you
            if current_version > PROJECT_DESCRIPTION_VERSION:
                logger.error("Can't migrate a project from a future version !")
                return False

            # Handle migrating from 0 to 1
            if current_version == 0:
                self._migrate_0_to_1()
                current_version = 1

            # Here we'll be able to chain for future updates
            # Something like:
            # if current_version == 1:
            #     self._migrate_1_to_2()
            #     current_version = 2

            # Set the correct version
            self._yaml_data["version"] = PROJECT_DESCRIPTION_VERSION

            # Save the new YAML
            self._save_yaml()

            # Commit the migration
            self.repo.index.commit(f"Migrated project to new format")

            # The project can be opened now
            self.can_be_opened = True

            return True
        except Exception as e:
            # Return false if anything goes wrong
            logger.error(f"Migration issue! {e}")
            return False

    def _migrate_0_to_1(self):
        """Migrate the loaded YAML data from schema 0 to schema 1."""

        # We changed the keys "chapters" and "scenes" into "content"
        for resource in self._yaml_data.get("resources", []):
            for key in ['chapters', 'scenes']:
                if key in resource:
                    resource['content'] = resource.pop(key)

        # We added a title key. By default, use the title of the manuscript
        for resource in self._yaml_data.get("resources", []):
            if resource.get("a", "") == "Manuscript":
                self._yaml_data["title"] = resource["title"]
                self.title = self._yaml_data["title"]

    def _load_yaml(self):
        """Load the YAML project description into the dict structure."""

        # Load all the YAML payload into the eponym dict
        yaml_file = self._base_directory / Path("manuscript.yml")
        with yaml_file.open("r") as file:
            self._yaml_data = yaml.safe_load(file)

        # Set the title
        self.title = self._yaml_data.get("title", "")

    def _save_yaml(self):
        """Dump the content of the dict into a YAML file."""

        yaml_file = self._base_directory / Path("manuscript.yml")
        with yaml_file.open(mode="w") as file:
            yaml.safe_dump(self._yaml_data, file, indent=2, sort_keys=True)

        # Add this edit to the list of changes to be in the next commit
        self.repo.index.add(yaml_file)

    @property
    def base_directory(self) -> Path:
        """The base directory."""
        return self._base_directory

    @property
    def repo(self):
        """Return a pointer to the Git repository of the manuscript."""
        return self._repo

    @property
    def resources(self):
        """Return a pointer to all the resources."""
        return self._resources

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
    def images(self):
        """The instances of Image in the manuscript."""
        model = Gtk.FilterListModel(
            model=self._resources,
            filter=Gtk.CustomFilter.new(lambda x: isinstance(x, Image))
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
        self.save_to_disk()
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

        # Look at the type of the resource we just removed
        resource_type = resource.__gtype__

        # Remove all references to it from other resources
        for other in self._resources:
            for prop in GObject.list_properties(type(other)):
                if isinstance(prop, GObject.ParamSpecObject):
                    # If it was a direct assignment, set it to None instead
                    accepted_item_type = prop.value_type
                    if resource_type.is_a(accepted_item_type):
                        if other.get_property(prop.name) == resource:
                            other.set_property(prop.name, None)
                    # If the resource was in a list, remove it from it
                    elif prop.value_type == Gio.ListStore.__gtype__:
                        list_store = other.get_property(prop.name)
                        accepted_item_type = list_store.get_item_type()
                        if resource_type.is_a(accepted_item_type):
                            found, position = list_store.find(resource)
                            if found:
                                list_store.remove(position)

        # Delete the file on disk (if any)
        for data_file in resource.data_files:
            if data_file.exists():
                data_file.unlink()

        # Keep track of the deletion of this scene in the history
        self.save_to_disk()
        for data_file in resource.data_files:
            self.repo.index.remove(data_file)
        self.repo.index.commit(f'Deleted resource "{resource.identifier}"')

        # Finally emit the signal
        resource.emit("deleted")

    def open(self):
        """Open the project by parsing the dict structure into objects."""
        logger.info(f"Open {self.title}")

        # Load all the resources
        if not self.is_opened:
            for resource_data in self._yaml_data["resources"]:
                resource = self.get_resource(resource_data["identifier"])

                # If we find the Manuscript update the pointer
                if isinstance(resource, Manuscript):
                    self.manuscript = resource

            self.is_opened = True
            logger.info(f"Loaded {len(self.resources)} resources")

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

        # Set the YAML data
        self._yaml_data = {
            "version": PROJECT_DESCRIPTION_VERSION,
            "title": self.title,
            "resources": resources
        }

        # Save it
        self._save_yaml()

    def get_resource(self, identifier: str):
        """Return one of the resource and load it if needed."""
        # Check if we already loaded the resource
        for resource in self._resources:
            if resource.identifier == identifier:
                return resource
        logger.debug(f"Could not find {identifier}, trying to load it")

        # Find the YAML data block
        resource_data = None
        for data in self._yaml_data["resources"]:
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
                if prop.value_type.is_a(Resource.__gtype__):
                    resource.set_property(
                        prop.name,
                        self.get_resource(value)
                    )
                elif prop.value_type == Gio.ListStore.__gtype__:
                    for v in value:
                        store = resource.get_property(prop.name)
                        store.append(self.get_resource(v))

        self._resources.append(resource)
        return resource
