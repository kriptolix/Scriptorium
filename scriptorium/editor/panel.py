from gi.repository import Adw, Gtk, Pango, GObject

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/panel.ui")
class ScrptPanel(Adw.Bin):
    __gtype_name__ = "ScrptPanel"
