# window.py
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

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

import scriptorium.editor
import scriptorium.library
from .model import Library

import logging
logger = logging.getLogger(__name__)

# Default status: show the gallery of books, a plus button on top left
# and the title "Scriptorium"
# People click on one of the book to switch mode. Using + opens a simple
# dialog to ask for the name and create a new book

# In editor mode the + is replaced by a X to close the book and return select
# a different one from the gallery

from pathlib import Path


@Gtk.Template(resource_path='/com/github/cgueret/Scriptorium/ui/window.ui')
class ScriptoriumWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ScriptoriumWindow'

    navigation = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load custom CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(Gio.File.new_for_uri("resource://com/github/cgueret/Scriptorium/ui/style.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Get the data folder
        logger.info(f'Data location: {GLib.get_user_data_dir()}')
        manuscript_path = Path(GLib.get_user_data_dir())
        self.navigation.find_page('library').set_property('manuscripts_base_path', manuscript_path.resolve())


        # Display the editor (for working on it)
        library = self.navigation.find_page('library')
        first_child = library.flowbox.get_child_at_index(0)
        library.flowbox.emit("child-activated", first_child)

