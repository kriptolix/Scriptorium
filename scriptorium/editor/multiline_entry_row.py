import logging

from gi.repository import Adw, Gtk, GObject
from .model import Scene
from .globals import BASE

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/editor/multiline_entry_row.ui")
class MultiLineEntryRow(Adw.PreferencesRow):
    __gtype_name__ = "MultiLineEntryRow"

    title = GObject.Property(type=str)
    text = GObject.Property(type=str)

    content = Gtk.Template.Child()
    edit_icon = Gtk.Template.Child()

    def __init__(self, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        # Bind our text property to the matching one in TextView
        self.bind_property(
            "text",
            self.content.get_buffer(),
            "text",
            GObject.BindingFlags.BIDIRECTIONAL |
            GObject.BindingFlags.SYNC_CREATE
        )

    @Gtk.Template.Callback()
    def on_state_flags_changed(self, _content, _flags):
        """Set the entry as focused."""
        if self.content.is_focus():
            self.add_css_class("focused")
            self.edit_icon.hide()
        else:
            self.remove_css_class("focused")
            self.edit_icon.show()


