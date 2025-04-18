from gi.repository import Adw, Gtk, GObject, Pango
from .model import Scene
import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/editor/writer.ui")
class Writer(Adw.Dialog):
    __gtype_name__ = "Writer"

    text_view = Gtk.Template.Child()
    label_words = Gtk.Template.Child()

    def __init__(self, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        text_buffer = self.text_view.get_buffer()

        # Create the tags for the buffer
        text_buffer.create_tag("em", style=Pango.Style.ITALIC)

        # Connect a signal to refresh the word count
        text_buffer.connect("changed", self.on_buffer_changed)

        # Detect when the editor is getting closed
        self.connect("closed", self.on_dialog_closed)

    def on_buffer_changed(self, text_buffer):
        """Keep an eye on modifications of the buffer."""
        start_iter, end_iter = text_buffer.get_bounds()
        content = text_buffer.get_text(start_iter, end_iter, False)
        words = len(content.split())
        self.label_words.set_label(str(words))

    def load_scene(self, scene):
        """Switch to editing the scene that has been selected."""
        logger.info(f"Open editor for {scene.title}")

        # Set the editor title to the title of the scene
        self.set_title(scene.title)

        # Get the text buffer
        text_buffer = self.text_view.get_buffer()

        # Assign the scene to it
        text_buffer.scene = scene

        # We don't want undo to span across scenes
        text_buffer.begin_irreversible_action()

        # Delete previous content
        start_iter, end_iter = text_buffer.get_bounds()
        text_buffer.delete(start_iter, end_iter)

        # Load the scene
        scene.load_into_buffer(text_buffer)

        # Finish
        text_buffer.end_irreversible_action()


    def on_dialog_closed(self, _dialog):
        """Perform any action needed when closing the editor."""
        text_buffer = self.text_view.get_buffer()
        logger.info(f"Save content of {text_buffer.scene.title}")
        text_buffer.scene.save_from_buffer(text_buffer)
