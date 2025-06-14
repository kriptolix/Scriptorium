from gi.repository import Adw, Gtk, Pango, Gdk, GLib
from scriptorium.globals import BASE
import logging
import threading

logger = logging.getLogger(__name__)

# make font selectable like in https://gitlab.gnome.org/GNOME/gnome-text-editor/-/blob/main/src/editor-preferences-dialog.c

# Mutex to avoid having to matches callback edit the buffer at the same time
text_buffer_lock = threading.Lock()


@Gtk.Template(resource_path=f"{BASE}/dialogs/writer.ui")
class Writer(Adw.Dialog):
    __gtype_name__ = "Writer"

    text_view = Gtk.Template.Child()
    label_words = Gtk.Template.Child()
    css_provider = Gtk.CssProvider()

    def __init__(self, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        # Create the tags for the buffer
        text_buffer = self.text_view.get_buffer()

        # Italics tag
        text_buffer.create_tag("em", style=Pango.Style.ITALIC)

        # Error tag
        color_error = Gdk.RGBA()
        color_error.parse("#e01b24")
        text_buffer.create_tag(
            "error",
            underline=Pango.Underline.SINGLE,
            underline_rgba=color_error
        )

        # Warning tag
        color_warning = Gdk.RGBA()
        color_warning.parse("#f5c211")
        text_buffer.create_tag(
            "warning",
            underline=Pango.Underline.SINGLE,
            underline_rgba=color_warning
        )

        # Hint tag
        color_hint = Gdk.RGBA()
        color_hint.parse("#62a0ea")
        text_buffer.create_tag(
            "hint",
            underline=Pango.Underline.SINGLE,
            underline_rgba=color_hint
        )

        # Set the style for the editor
        style = """textview.text_editor {
            font-family: Cantarell, serif;
            font-size: 18px;
            line-height: 1.2;
        }"""
        self.css_provider.load_from_string(style)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._check_timeout_id = None

    def check_content(self, language_tool):
        text_buffer = self.text_view.get_buffer()
        start_iter, end_iter = text_buffer.get_bounds()
        content = text_buffer.get_text(start_iter, end_iter, False)
        language_tool.check(content, "en-GB", self.process_matches)

        # This is called from a timer, we don't want to repeat execution
        self._check_timeout_id = None
        return False

    def process_matches(self, results):
        # If there is another check queued forget that one
        if self._check_timeout_id is not None:
            return

        if text_buffer_lock.acquire(blocking=True):
            try:
                # Start by removing all previous annotations
                text_buffer = self.text_view.get_buffer()
                start_iter, end_iter = text_buffer.get_bounds()
                text_buffer.remove_tag_by_name("error", start_iter, end_iter)
                text_buffer.remove_tag_by_name("warning", start_iter, end_iter)
                text_buffer.remove_tag_by_name("hint", start_iter, end_iter)

                # Then add the new ones
                for match in results['matches']:
                    start_iter = text_buffer.get_iter_at_offset(match['offset'])
                    end_iter = text_buffer.get_iter_at_offset(match['offset'] + match['length'])
                    if match["type"]["typeName"] == "Hint":
                        tag_name = "hint"
                    elif match["rule"]["issueType"] == "style":
                        tag_name = "hint"
                    elif match["type"]["typeName"] == "Other":
                        tag_name = "warning"
                    elif match["rule"]["issueType"] == "inconsistency":
                        tag_name = "warning"
                    else:
                        tag_name = "error"
                    text_buffer.apply_tag_by_name(tag_name, start_iter, end_iter)
            finally:
                text_buffer_lock.release()

    @Gtk.Template.Callback()
    def on_buffer_changed(self, text_buffer):
        """Keep an eye on modifications of the buffer."""

        # Update the number of words
        start_iter, end_iter = text_buffer.get_bounds()
        content = text_buffer.get_text(start_iter, end_iter, False)
        words = len(content.split())
        self.label_words.set_label(str(words))

        # Set a new timeout to check the content
        if self._check_timeout_id is not None:
            GLib.source_remove(self._check_timeout_id)
        window = self.props.root
        if window is not None:
            application = window.props.application
            language_tool = application.language_tool
            self._check_timeout_id = GLib.timeout_add_seconds(0.5, self.check_content, language_tool)

    @Gtk.Template.Callback()
    def on_writer_closed(self, _dialog):
        """Perform any action needed when closing the editor."""
        Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(),
                                                    self.css_provider)
        text_buffer = self.text_view.get_buffer()

        # Remove all the language check annotations
        start_iter, end_iter = text_buffer.get_bounds()
        text_buffer.remove_tag_by_name("error", start_iter, end_iter)
        text_buffer.remove_tag_by_name("warning", start_iter, end_iter)
        text_buffer.remove_tag_by_name("hint", start_iter, end_iter)

        logger.info(f"Save content of {text_buffer.scene.title}")
        text_buffer.scene.save_from_buffer(text_buffer)

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


