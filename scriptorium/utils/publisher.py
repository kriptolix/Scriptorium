# utils/publisher.py
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
from gi.repository import Gtk, Gio, GObject
from scriptorium.models import Manuscript, Chapter, Scene
from scriptorium.globals import BASE
from jinja2 import Environment, PackageLoader, select_autoescape
from ebooklib import epub

import logging
logger = logging.getLogger(__name__)


# Wrapper for epub.EpubHtml using lazy loading and cache
class PublisherSection(GObject.Object):
    """
    A Section in a document. Calling render will return the instanciated
    template.
    https://pypi.org/project/EbookLib/
    """

    title = GObject.Property(type=str)

    def __init__(self, title, template, parameters):
        super().__init__()
        self.title = title
        self._template = template
        self._parameters = parameters
        self._html = None

    @property
    def html(self) -> str:
        if self._html is None:
            self._html = self._template.render(self._parameters)
        return self._html

    @property
    def epub_html(self) -> epub.EpubHtml:
        epub_html = epub.EpubHtml(
                title=self._title,
                file_name=f"{self._title.lower().replace(' ', '_')}.xhtml",
                lang="en"
            )
        epub_html.content = self.html
        return epub_html


# Create instances of PublisherSection and return the toc. When asked to export
# the book call the rest of the epub lib functions
# Need a separate call to get the CSS to render in the app. Maybe wrap that into a separate styling object
class Publisher(object):
    """
    Publisher is a helper class to encapsulate the content of the manuscript
    as a set of HTML files. This content can be used as a view in the editor
    or exported to disk as an epub.
    """

    def __init__(self, manuscript: Manuscript):
        """Create a new instance of a Publisher."""

        # Keep a pointer to the manuscript
        self._manuscript = manuscript

        # Load the templates
        self._env = Environment(
            loader=PackageLoader("scriptorium"),
            autoescape=select_autoescape()
        )
        logger.info(self._env.list_templates())

        self._toc = None

    def table_of_contents(self):
        if self._toc is None:
            self._toc = []

            # Add the cover page
            cover_img = self._manuscript.cover
            if cover_img is not None:
                logger.info(f"Cover => {cover_img.path}")
                self._toc.append(PublisherSection(
                    title="Cover",
                    template=self._env.get_template("templates/cover.xhtml"),
                    parameters={
                        "image_path": f"file://{cover_img.path}",
                        "image_width": cover_img.width,
                        "image_height": cover_img.height
                    }
                ))
                logger.info(self._toc[0].html)
        return self._toc

    def content(self) -> list:
        """Return the content of the manuscript as a list of HTML chapters."""

        # Prepare the output
        output = []

        # Add a cover page
        self._add_cover(output)

        # Add all the content
        self._add_chapters(output)

        return output

    def _add_cover(self, output):
        template = self._env.get_template("templates/cover.xhtml")
        logger.info(template)

    def _add_chapters(self, output):
        """
        Create the HTML pages for all the chapters and add them to the output.
        """

        # Create a tree model to iterate over the content
        model = Gtk.TreeListModel.new(
            self._manuscript.content, False, True,
            lambda item:
            item.content if isinstance(item, (Manuscript, Chapter)) else None
        )

        # Iterate on each row
        previous_resource = None
        previous_depth = None
        chapter_index = 1
        for idx in range(0, model.get_n_items()):
            # See what we have on that row
            row = model.get_row(idx)
            resource = row.get_item()
            depth = row.get_depth()

            # We start something new
            if row.get_depth() == 0:
                if isinstance(resource, Chapter):
                    output.append([f"Chapter {chapter_index}", ""])
                elif isinstance(resource, Scene):
                    # We stitch together the scenes at root level as long as
                    # they come in a sequence
                    logger.info(f"{resource.title} has prev {previous_resource.title}")
                    if not isinstance(previous_resource, Scene) or previous_depth != depth:
                        output.append([f"Chapter {chapter_index}", ""])
                chapter_index += 1

            # Now add the content to the last part of the output
            if isinstance(resource, Scene):
                # If the previous thing was a scene we add a scene separator
                if isinstance(previous_resource, Scene) and previous_depth == depth:
                    output[-1][1] += "<span>...</span>"
                # Add the content of the scene
                output[-1][1] += resource.to_html()
            elif isinstance(resource, Chapter):
                d = row.get_depth()
                output[-1][1] += f"<h{d+1}>{resource.title}</h{d+1}>"

            # Set the previous item as the current one
            previous_resource = resource
            previous_depth = depth
        
