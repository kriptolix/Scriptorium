# views/editor_manuscript.py
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
"""Editor panel to select and work on the scenes."""

import logging

from gi.repository import Adw, Gtk, Pango, GObject, GLib

from scriptorium.globals import BASE
from scriptorium.dialogs import Writer

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_manuscript.ui")
class ScrptManuscriptPanel(Adw.NavigationPage):
    __gtype_name__ = "ScrptManuscriptPanel"
    __title__ = "Manuscript"
    __icon_name__ = "dictionary-symbolic"
    __description__ = "Edit the information about the manuscript"

    identifier = Gtk.Template.Child()
    edit_title = Gtk.Template.Child()
    edit_synopsis = Gtk.Template.Child()
    show_sidebar_button = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)

        self._editor = editor
        self._manuscript = editor.manuscript
        self.set_title(self.__title__)

        # Bind the identifier, title and synopsis
        editor.manuscript.bind_property(
            "identifier",
            self.identifier,
            "subtitle",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
        editor.manuscript.bind_property(
            "title",
            self.edit_title,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
        editor.manuscript.bind_property(
            "synopsis",
            self.edit_synopsis,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

    def create_message_entry(self, message):
        """Bind a scene card to a scene."""
        message_entry = Adw.ActionRow()
        message_entry.add_css_class("property")
        message_entry.set_title(message.datetime)
        message_entry.set_subtitle(message.message)
        return message_entry

    def bind_side_bar_button(self, split_view):
        """Connect the button to collapse the sidebar."""
        split_view.bind_property(
            "show_sidebar",
            self.show_sidebar_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

    @Gtk.Template.Callback()
    def on_delete_manuscript_activated(self, _button):
        """Handle a request to delete the scene."""
        logger.info(f"Delete {self._manuscript.title}")
        dialog = Adw.AlertDialog(
            heading="Delete manuscript?",
            body=f'This action can not be undone. Are you sure you want to delete the whole manuscript "{self._manuscript.title}"',
            close_response="cancel",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.choose(self, None, self.on_delete_response_selected)

    def on_delete_response_selected(self, _dialog, task):
        """Handle the response to the confirmation dialog."""
        response = _dialog.choose_finish(task)
        if response == "delete":
            # Delete the manuscript
            library = self._manuscript.library
            library.delete_manuscript(self._manuscript)

            # Trigger a close on the editor
            self._editor.close_on_delete()

