import logging

from gi.repository import Adw, Gtk, GObject
from scriptorium.globals import BASE

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/widgets/multiline_entry_row.ui")
class MultiLineEntryRow(Adw.PreferencesRow):
    __gtype_name__ = "MultiLineEntryRow"

    header = GObject.Property(type=str)
    text = GObject.Property(type=str)

    content = Gtk.Template.Child()
    edit_icon = Gtk.Template.Child()
    #empty_title = Gtk.Template.Child()
    title = Gtk.Template.Child()
    #text_buffer = Gtk.Template.Child()

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

        #self.target = Adw.CallbackAnimationTarget.new(self.empty_animation)
        #self.animation = Adw.TimedAnimation.new(self, 0, 0, 150, self.target)
        #self.animation.set_repeat_count(1)
        #self.update_empty()

    def update_empty(self):
        start, end = self.text_buffer.get_bounds()
        empty_text = (len(self.text_buffer.get_text(start, end, False)) == 0)
        #focused = self.content.is_focus()
        #self.animation.set_value_from(0)
        #self.animation.set_value_to(0 if empty_text or not focused else 1)
        #self.animation.play()

        if focused or not empty_text:
            #self.title.set_opacity(1)
            #self.empty_title.set_opacity(0)
            self.title.add_css_class("subtitle")
            self.title.remove_css_class("title")
            self.title.remove_css_class("dim-label")
        else:
            #self.title.set_opacity(0)
            #self.empty_title.set_opacity(1)
            self.title.remove_css_class("subtitle")
            self.title.add_css_class("title")
            self.title.add_css_class("dim-label")

    #def empty_animation(self, value):
    #    self.title.set_opacity(value)
    #    self.empty_title.set_opacity(1 - value)

    @Gtk.Template.Callback()
    def on_state_flags_changed(self, _content, _flags):
        """Set the entry as focused."""
        if self.content.is_focus():
            self.add_css_class("focused")
            self.edit_icon.hide()
        else:
            self.remove_css_class("focused")
            self.edit_icon.show()
        #self.update_empty()

    #@Gtk.Template.Callback()
    #def on_textbuffer_changed(self, _buffer):
        #self.update_empty()

