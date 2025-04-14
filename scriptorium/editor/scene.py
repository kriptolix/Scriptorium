from gi.repository import Adw, Gtk, GObject
from .model import Scene
import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/scene.ui")
class SceneCard(Adw.ActionRow):
    __gtype_name__ = "SceneCard"

    _scene = None

    edit_button = Gtk.Template.Child()

    def __init__(self, scene: Scene, **kwargs):
        super().__init__(**kwargs)
        self._scene = scene

        # Configure the information for the scene
        self.set_property('title', scene.title)
        self.set_property('subtitle', scene.synopsis)

    def get_scene(self):
        return self._scene


