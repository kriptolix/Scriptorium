# text_view.py
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
from gi.repository import Gtk, GObject, Pango, Gdk
from scriptorium.globals import BASE

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/widgets/text_view.ui")
class ScrptTextView(Gtk.TextView):
    __gtype_name__ = "ScrptTextView"

    css_provider = Gtk.CssProvider()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create the tags for the buffer
        text_buffer = self.get_buffer()

        # Text formatting tags
        text_buffer.create_tag("em", style=Pango.Style.ITALIC)
        text_buffer.create_tag("strong", weight=Pango.Weight.BOLD)

        # Error tag
        color_error = Gdk.RGBA()
        color_error.parse("#e01b24")
        text_buffer.create_tag(
            "error",
            underline=Pango.Underline.ERROR,
            underline_rgba=color_error
        )

        # Warning tag
        color_warning = Gdk.RGBA()
        color_warning.parse("#f5c211")
        text_buffer.create_tag(
            "warning",
            underline=Pango.Underline.ERROR,
            underline_rgba=color_warning
        )

        # Hint tag
        color_hint = Gdk.RGBA()
        color_hint.parse("#62a0ea")
        text_buffer.create_tag(
            "hint",
            underline=Pango.Underline.ERROR,
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

