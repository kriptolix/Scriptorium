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

    def __init__(self, scene):
        """Create an instance of the editor."""
        super().__init__()
        self._scene = scene

        self._idle_timeout_id = None
        self._matches = None

        gesture = Gtk.GestureClick()
        gesture.connect("pressed", self.on_text_view_click, self.text_view)
        self.text_view.add_controller(gesture)

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

    def on_text_view_click(self, _gesture, button, x, y, text_view):
        # If we are on a suggestion, automatically select it.
        # This will trigger the selection changed
        if isinstance(_gesture, Gtk.GestureClick) and button == 1:
            buff_x, buff_y = self.text_view.window_to_buffer_coords(
                Gtk.TextWindowType.WIDGET,
                x, y
            )
            found, click_iter = self.text_view.get_iter_at_location(
                buff_x, buff_y
            )
            if found and self._matches is not None:
                buffer = self.text_view.get_buffer()
                for match in self._matches:
                    start_iter = buffer.get_iter_at_offset(
                        match['offset']
                    )
                    end_iter = buffer.get_iter_at_offset(
                        match['offset'] + match['length']
                    )
                    if click_iter.in_range(start_iter, end_iter):
                        def do_select():
                            buffer.select_range(start_iter, end_iter)
                            return False
                        GLib.idle_add(do_select)
                        break

    def process_matches(self, results):
        # If there is another check queued forget that one
        if self._idle_timeout_id is not None:
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
                self._matches = results['matches']
                for match in self._matches:
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

    def on_editor_idle(self):
        self._idle_timeout_id = None

        text_buffer = self.text_view.get_buffer()
        start_iter, end_iter = text_buffer.get_bounds()
        content = text_buffer.get_text(start_iter, end_iter, False)

        # Update the number of words
        words = len(content.split())
        self.label_words.set_label(str(words))

        # Call LanguageTool
        window = self.props.root
        application = window.props.application
        language_tool = application.language_tool
        language_tool.check(content, "en-GB", self.process_matches)

        # Don't repeat that callback
        return False

    @Gtk.Template.Callback()
    def on_buffer_changed(self, text_buffer):
        """Keep an eye on modifications of the buffer."""
        if self._idle_timeout_id:
            GLib.source_remove(self._idle_timeout_id)

        self._idle_timeout_id = GLib.timeout_add(200, self.on_editor_idle)

    @Gtk.Template.Callback()
    def on_selection_changed(self, text_buffer, selection):
        # Show the pop over for the selection: style elements + suggestions eventually
        # If we are on more than one suggestion do not show any
        if not text_buffer.get_has_selection():
            return

        logger.info("Selected")

    @Gtk.Template.Callback()
    def on_writer_opened(self, _dialog):
        """Switch to editing the scene that has been selected."""
        logger.info(f"Open editor for {self._scene.title}")

        # Set the editor title to the title of the scene
        self.set_title(self._scene.title)

        # Load the content of the scene
        text_buffer = self.text_view.get_buffer()
        self._scene.load_into_buffer(text_buffer)

    @Gtk.Template.Callback()
    def on_writer_closed(self, _dialog):
        """Perform any action needed when closing the editor."""
        logger.info(f"Close editor for {self._scene.title}")

        if self._idle_timeout_id:
            GLib.source_remove(self._idle_timeout_id)

        # Remove the styling
        Gtk.StyleContext.remove_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider
        )

        # Remove all the language check annotations
        text_buffer = self.text_view.get_buffer()
        start_iter, end_iter = text_buffer.get_bounds()
        text_buffer.remove_tag_by_name("error", start_iter, end_iter)
        text_buffer.remove_tag_by_name("warning", start_iter, end_iter)
        text_buffer.remove_tag_by_name("hint", start_iter, end_iter)

        # Save the content of the buffer
        self._scene.save_from_buffer(text_buffer)


