from gi.repository import Adw, Gtk, GObject
from scriptorium.models import Scene
import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/scene.ui")
class SceneCard(Adw.PreferencesRow):
    __gtype_name__ = "SceneCard"

    _scene = None
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    edit_button = Gtk.Template.Child()
    suffixes = Gtk.Template.Child()

    def __init__(self, scene: Scene, **kwargs):
        super().__init__(**kwargs)
        self._scene = scene

        # Configure the information for the scene
        self.set_property('title', scene.title)
        self.set_property('synopsis', scene.synopsis)

        self.bind_property(
            "title",
            scene,
            "title",
            GObject.BindingFlags.BIDIRECTIONAL
        )
        self.bind_property(
            "synopsis",
            scene,
            "synopsis",
            GObject.BindingFlags.BIDIRECTIONAL
        )

    def get_scene(self):
        return self._scene

    def hide_suffix(self):
        self.suffixes.set_visible(False)
