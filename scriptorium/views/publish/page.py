# views/editor_formatting.py
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

import logging
from gi.repository import Adw, Gtk, Gio, GObject
from scriptorium.models import Project, Chapter
from scriptorium.globals import BASE
from scriptorium.utils.publisher import Publisher

try:
    from gi.repository import WebKit
    HAVE_WEBKIT = True
except ImportError:
    HAVE_WEBKIT = False

logger = logging.getLogger(__name__)

class NavigationRow(Gtk.Box):

    content = GObject.Property(type=str)

    def __init__(self, title):
        super().__init__(margin_top=6)
        label = Gtk.Label(label = title)
        self.append(label)

@Gtk.Template(resource_path=f"{BASE}/views/publish/page.ui")
class PublishPage(Adw.Bin):

    __gtype_name__ = "PublishPage"
    __title__ = "Formatting"
    __icon_name__ = "open-book-symbolic"
    __description__ = "Preview and modify the formatting"

    web_view_placeholder = Gtk.Template.Child()
    chapters_list = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # If we have WebKit set the component, otherwise show placeholder
        if HAVE_WEBKIT:
            logger.info("Webkit is available")
            self.web_view = WebKit.WebView()
            self.web_view.set_zoom_level(1)
            self.web_view.set_margin_start(6)
            self.web_view.set_margin_end(6)
            self.web_view.set_margin_top(6)
            self.web_view.set_margin_bottom(6)
            self.web_view.set_vexpand(True)
            self.web_view.set_hexpand(True)
            self.web_view_placeholder.append(self.web_view)
        else:
            widget = Adw.StatusPage(
                title="Not available",
                icon_name="process-stop-symbolic",
                description="This feature is not available on your operating system"
            )
            widget.set_vexpand(True)
            widget.set_hexpand(True)
            self.web_view_placeholder.append(widget)

        self.chapters_list.connect(
             "row-selected",
             self.on_selected_item
        )

    def connect_to_project(self, project):
        logger.info("Project changed")
        self._project = project
        self._publisher = Publisher(project.manuscript)
        logger.info(self._publisher.table_of_contents())
        self.reload_book()

    def reload_book(self):
        # Remove all the previous content
        self.chapters_list.remove_all()

        # Load the new ToC
        book_parts = self._publisher.table_of_contents()
        for part in book_parts:
            widget = NavigationRow(part.title)
            widget.content = part.html
            self.chapters_list.append(widget)

        # Select the first item
        row = self.chapters_list.get_row_at_index(0)
        self.chapters_list.select_row(row)

    def on_selected_item(self, _src, _selected_item):
        selected_row = self.chapters_list.get_selected_row()
        if selected_row is None:
            return

        selected_chapter = selected_row.get_child()
        logger.info(f"Chapter selected: {selected_chapter}")

        # Get all the HTML content from the model
        content = selected_chapter.content
        logger.info(content)

        # Instantiate the template for the rendering
        #emulator_html = Gio.File.new_for_uri(
        #    f"resource:/{BASE}/views/publish/page.html"
        #)
        #html_content = emulator_html.load_contents()[1].decode()
        #html_content = html_content.replace("{content}", content)

        # Load the content
        if HAVE_WEBKIT:
            self.web_view.load_html(content, "file:///")


