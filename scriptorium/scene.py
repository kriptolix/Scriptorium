from gi.repository import Adw, Gtk, GObject, Gio, Gdk

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/scene.ui")
class SceneCard(Gtk.Box):
    __gtype_name__ = "SceneCard"

    scene_title = GObject.Property(type=str)
    scene_synopsis = GObject.Property(type=str)
    
