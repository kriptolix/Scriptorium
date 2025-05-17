from gi.repository import Adw, Gtk, GObject
from scriptorium.models import Scene
import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/widgets/scene.ui")
class SceneCard(Adw.Bin):
    __gtype_name__ = "SceneCard"

    _scene = None
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    suffixes = Gtk.Template.Child()
    prefixes = Gtk.Template.Child()
    entities = Gtk.Template.Child()

    def __init__(self, scene: Scene, can_activate: bool = False, can_move: bool = False):
        super().__init__()
        self._scene = scene

        # Configure the information for the scene
        self.set_property("title", scene.title)
        self.set_property("synopsis", scene.synopsis)
        self.bind_property(
            "title", scene, "title", GObject.BindingFlags.BIDIRECTIONAL
        )
        self.bind_property(
            "synopsis", scene, "synopsis", GObject.BindingFlags.BIDIRECTIONAL
        )

        # Adjust the display of drag and activation extra
        self.prefixes.set_visible(can_move)
        self.suffixes.set_visible(can_activate)

        # Initialise the list of entities
        for entity in scene.entities:
            self.entities.append(self._get_avatar(entity))

        # Keep an eye on potential changes
        scene.entities.connect("items-changed", self.on_items_changed)

    @GObject.Property(type=Scene)
    def scene(self):
        return self._scene

    def _get_avatar(self, entity):
        avatar = Adw.Avatar(size=24, show_initials=True)
        avatar.set_text(entity.title)
        return avatar

    def on_items_changed(self, liststore, position, removed, added):
        """Handle a request to update the content of the entities list."""

        # Remove widgets for removed items
        for _ in range(removed):
            child = self.entities.get_child_at(position)
            self.entities.remove(child)

        # Add widgets for added items
        for i in range(added):
            entry = liststore.get_item(position + i)
            child = self.entities.get_child_at(position + i - 1)
            self.entities.insert_child_after(self._get_avatar(entity), child)

