# dialogs/writer.py
#
# Copyright 2025 Christophe Gueret
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk, Pango, Gdk, GLib
from scriptorium.globals import BASE
from scriptorium.widgets import WriterPopover
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
        self._button_down = False

        gesture = Gtk.GestureClick()
        gesture.connect("pressed", self.on_text_view_click, self.text_view)
        gesture.connect("released", self.check_selection_after_release)
            #lambda *args : GLib.timeout_add(0, self.check_selection_after_release)
        #)
        gesture.connect("unpaired_release",self.check_selection_after_release)
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

        self.popover = None

    def check_selection_after_release(self, *args):
        logger.info("release")

        buffer = self.text_view.get_buffer()
        if not buffer.get_has_selection():
            return False

        start_iter, end_iter = buffer.get_selection_bounds()
        if start_iter.get_offset() == end_iter.get_offset():
            return False

        logger.info(f"Release with {buffer.get_text(start_iter, end_iter, False)}")

        # Aim to place the popover under the selected text and in the middle
        rect_start = self.text_view.get_iter_location(start_iter)
        win_start_x, win_start_y = self.text_view.buffer_to_window_coords(
            Gtk.TextWindowType.WIDGET,
            rect_start.x, rect_start.y
        )
        rect_end = self.text_view.get_iter_location(end_iter)
        win_end_x, win_end_y = self.text_view.buffer_to_window_coords(
            Gtk.TextWindowType.WIDGET,
            rect_end.x, rect_end.y
        )
        x = win_end_x
        y = win_end_y + rect_start.height * 0.8

        if self.popover is None:
            self.anchor_overlay = Adw.Bin()
            self.popover = WriterPopover()
            self.popover.set_parent(self.anchor_overlay)
            self.text_view.add_overlay(child=self.anchor_overlay, xpos=x, ypos=y)
        else:
            self.text_view.move_overlay(child=self.anchor_overlay, xpos=x, ypos=y)

        self.popover.category = buffer.get_text(start_iter, end_iter, False)
        self.popover.set_pointing_to(Gdk.Rectangle(x, y))
        self.popover.popup()
        #def show_popup():
        #    self.popover.popup()
        #    return False
        #GLib.idle_add(show_popup)

        return False

    def trigger_highlight_for_match(self, match):
        buffer = self.text_view.get_buffer()
        start_iter = buffer.get_iter_at_offset(
            match['offset']
        )
        end_iter = buffer.get_iter_at_offset(
            match['offset'] + match['length']
        )
        buffer.select_range(start_iter, end_iter)
        return False

    def on_text_view_click(self, _gesture, n_press, x, y, text_view):
        # If we are on a suggestion, automatically select it.
        # This will trigger the selection changed
        if self.popover:
            self.popover.popdown()

        if isinstance(_gesture, Gtk.GestureClick) and n_press == 1:
            buff_x, buff_y = self.text_view.window_to_buffer_coords(
                Gtk.TextWindowType.WIDGET,
                x, y
            )
            found, click_iter = self.text_view.get_iter_at_location(
                buff_x, buff_y
            )
            if found and self._matches is not None:
                offset = click_iter.get_offset()
                for match in self._matches:
                    if match['offset'] < offset < match['offset'] + match['length']:
                        GLib.idle_add(self.trigger_highlight_for_match, match)

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

        # If language tool is not ready try again later
        if not language_tool.server_is_alive:
            self._idle_timeout_id = GLib.timeout_add(200, self.on_editor_idle)
        else:
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


