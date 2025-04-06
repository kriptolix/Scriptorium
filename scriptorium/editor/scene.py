from gi.repository import Adw, Gtk, GObject, Gio, Gdk

from .model import Scene

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/scene.ui")
class SceneCard(Adw.Bin):
    __gtype_name__ = "SceneCard"

    _scene = None

    scene_title = GObject.Property(type=str)
    scene_synopsis = GObject.Property(type=str)
    
    def get_scene(self):
        return self._scene

    def connect_to_scene(self, scene: Scene):
        self._scene = scene
        self.set_property('scene_title', scene.title)
        self.set_property('scene_synopsis', scene.synopsis)

