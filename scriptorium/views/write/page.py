# views/write/page.py
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
from gi.repository import Adw, Gtk, Gdk, GLib, Gio, GObject
from scriptorium.globals import BASE
from scriptorium.widgets import AnnotationCard
from scriptorium.models import Chapter, Scene
from scriptorium.utils import switch_tag_for_selection

import logging
import threading

logger = logging.getLogger(__name__)

# make font selectable like in https://gitlab.gnome.org/GNOME/gnome-text-editor/-/blob/main/src/editor-preferences-dialog.c

# Mutex to avoid having to matches callback edit the buffer at the same time
text_buffer_lock = threading.Lock()

@Gtk.Template(resource_path=f"{BASE}/views/write/page.ui")
class WritePage(Adw.Bin):
    __gtype_name__ = "WritePage"

    text_view = Gtk.Template.Child()
    label_words = Gtk.Template.Child()
    css_provider = Gtk.CssProvider()
    annotations_list = Gtk.Template.Child()
    show_annotations = Gtk.Template.Child()

    navigation = Gtk.Template.Child()

    def __init__(self):
        """Create an instance of the editor."""
        super().__init__()
        #self._scene = scene

        # Instantiated with a timeout to detect when the editor is idle
        self._idle_timeout_id = None

        # Instantiated with a list of annotations from the spellchecker
        self._annotations = None

        self.text_view.get_buffer().connect("changed", self.on_buffer_changed)


    def connect_to_project(self, project):
        self.project = project

        self.navigation.connect_to(project)

    @Gtk.Template.Callback()
    def do_toggle_bold(self, _src, _param = None):
        switch_tag_for_selection(self.text_view.get_buffer(), "strong")

    @Gtk.Template.Callback()
    def do_toggle_italics(self, _src, _param = None):
        switch_tag_for_selection(self.text_view.get_buffer(), "em")

    def on_received_annotations(self, annotations):
        # If there is another check queued forget that one
        if self._idle_timeout_id is not None:
            return

        self._annotations = annotations
        self.refresh_annotations_tags()

        # Clear the list box
        self.annotations_list.remove_all()

        # Then add the new card
        for annotation in annotations:
            card = AnnotationCard(self.text_view.get_buffer(), annotation)
            self.annotations_list.append(card)

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
            language_tool.check(content, "en-GB", self.on_received_annotations)

        # Don't repeat that callback
        return False

    def refresh_annotations_tags(self):
        # Start by removing all previous annotations
        text_buffer = self.text_view.get_buffer()
        start_iter, end_iter = text_buffer.get_bounds()
        text_buffer.remove_tag_by_name("error", start_iter, end_iter)
        text_buffer.remove_tag_by_name("warning", start_iter, end_iter)
        text_buffer.remove_tag_by_name("hint", start_iter, end_iter)

        # Then add the new ones
        if self.show_annotations.get_active() and self._annotations:
            for annotation in self._annotations:
                start_iter = text_buffer.get_iter_at_offset(
                    annotation.offset
                )
                end_iter = text_buffer.get_iter_at_offset(
                    annotation.offset + annotation.length
                )
                text_buffer.apply_tag_by_name(
                    annotation.category, start_iter, end_iter
                )

    @Gtk.Template.Callback()
    def on_show_annotations_toggled(self, _toggle_button):
        self.refresh_annotations_tags()

    def on_buffer_changed(self, text_buffer):
        """Keep an eye on modifications of the buffer."""
        if self._idle_timeout_id:
            GLib.source_remove(self._idle_timeout_id)

        self._idle_timeout_id = GLib.timeout_add(200, self.on_editor_idle)

    #@Gtk.Template.Callback()
    def on_writer_opened(self, _dialog):
        """Switch to editing the scene that has been selected."""
        logger.info(f"Open editor for {self._scene.title}")

        # Create all the actions
        action_group = Gio.SimpleActionGroup()
        controller = Gtk.ShortcutController()

        action = Gio.SimpleAction.new("do_toggle_bold", None)
        action.connect("activate", self.do_toggle_bold)
        action_group.add_action(action)
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary>b"),
            Gtk.NamedAction.new("custom.do_toggle_bold")
        )
        controller.add_shortcut(shortcut)

        action = Gio.SimpleAction.new("do_toggle_italics", None)
        action.connect("activate", self.do_toggle_italics)
        action_group.add_action(action)
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary>i"),
            Gtk.NamedAction.new("custom.do_toggle_italics")
        )
        controller.add_shortcut(shortcut)

        self.text_view.insert_action_group("custom", action_group)
        self.text_view.add_controller(controller)

        # Set the editor title to the title of the scene
        self.set_title(self._scene.title)

        # Load the content of the scene
        text_buffer = self.text_view.get_buffer()
        self._scene.load_into_buffer(text_buffer)

    #@Gtk.Template.Callback()
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


