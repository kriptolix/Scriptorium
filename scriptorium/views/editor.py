# editor.py
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

from gi.repository import Adw, Gtk, GObject, Gio, GLib
from pathlib import Path

from scriptorium.globals import BASE
from scriptorium.dialogs import ScrptAddDialog
from scriptorium.widgets import ThemeSelector
from scriptorium.models import Project, Scene, Chapter, Image

import scriptorium.views.write
import scriptorium.views.publish
import scriptorium.views.plan

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor.ui")
class ScrptEditorView(Adw.NavigationPage):
    """The editor is the main view to modify a manuscript."""

    __gtype_name__ = "ScrptEditorView"

    project = GObject.Property(type=Project)

    win_menu = Gtk.Template.Child()
    write_page = Gtk.Template.Child()
    publish_page = Gtk.Template.Child()
    plan_page = Gtk.Template.Child()
    file_filter_image = Gtk.Template.Child()

    def __init__(self):
        """Create a new instance of the editor."""
        super().__init__()

        # Connect an instance of the theme button to the menu
        popover = self.win_menu.get_popover()
        popover.add_child(ThemeSelector(), "theme")

        # Create the custom action group for the editor
        group = Gio.SimpleActionGroup()
        self.insert_action_group("editor", group)

        # Create the action to add a new resource
        action = Gio.SimpleAction.new(
            name="add_resource",
            parameter_type=GLib.VariantType.new("(ss)")
            )
        action.connect("activate", self.on_add_resource)
        group.add_action(action)

        # Create the action to delete a resource
        action = Gio.SimpleAction.new(
            name="delete_resource",
            parameter_type=GLib.VariantType.new("s")
            )
        action.connect("activate", self.on_delete_resource)
        group.add_action(action)

        # Create the action to import an image into the project
        action = Gio.SimpleAction.new(
            name="import_image",
            parameter_type=None
            )
        action.connect("activate", self.on_import_image)
        group.add_action(action)

        # Create the action set the cover of the project
        action = Gio.SimpleAction.new(
            name="set_cover",
            parameter_type=GLib.VariantType.new("s")
            )
        action.connect("activate", self.on_set_cover)
        group.add_action(action)

        # Create the action to import a new cover and set it
        action = Gio.SimpleAction.new(
            name="import_cover",
            parameter_type=None
            )
        action.connect("activate", self.on_import_cover)
        group.add_action(action)

    def connect_to_project(self, project: Project):
        # Keep track of the project the editor is associated to
        self.project = project

        self.write_page.connect_to_project(project)
        self.publish_page.connect_to_project(project)
        self.plan_page.connect_to_project(project)

    @Gtk.Template.Callback()
    def on_editorview_closed(self, _editorview):
        """Handle a request to close the editor."""
        if self.project is not None:
            logger.info("Editor is closed, saving the manuscript")
            self.project.save_to_disk()

    def close_on_delete(self):
        self.project = None
        self.window.close_editor(self)

    def on_add_resource(self, _action, parameters):
        """Add a new resource to the project."""

        # We have two parameters, the target type and an optional parent
        target_type, parent = parameters.unpack()

        logger.info(f"Add a new {target_type} as child of {parent}")

        dialog = ScrptAddDialog(target_type)

        def handle_response(dialog, task):
            if dialog.choose_finish(task) == "add":
                logger.info(f"Add entity {dialog.title}: {dialog.synopsis}")
                # Create the new resource
                resource = self.project.create_resource(
                    eval(target_type), dialog.title, dialog.synopsis
                )
                # If we want to add it as a child of something, do so now
                if parent != '':
                    parent_resource = self.project.get_resource(parent)
                    parent_resource.content.append(resource)

        dialog.choose(self, None, handle_response)

    def on_delete_resource(self, _action, parameter):
        """Delete a resource from the project."""

        resource_identifier = parameter.get_string()
        resource = self.project.get_resource(resource_identifier)

        logger.info(f"Delete {resource.title}")

        dialog = Adw.AlertDialog(
            heading=f"Delete {resource.__gtype_name__}",
            body=f'This action can not be undone! Are you sure you want to delete "{resource.title}" ?',
            close_response="cancel",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        def handle_response(dialog, task):
            response = dialog.choose_finish(task)
            if response == "delete":
                # Delete the resource
                self.project.delete_resource(resource)

        dialog.choose(self, None, handle_response)

    def on_import_image(self, _action, parameters):
        """Import an image into the project."""
        logger.info(f"Import image")
        self._import_image(None)

    def on_import_cover(self, _action, parameters):
        """Import an image into the project."""
        logger.info(f"Import image and set it as cover")
        self._import_image(self._set_cover)

    def on_set_cover(self, _action, parameter):
        logger.info(f"Set cover")
        self._set_cover(parameter.get_string())

    def _import_image(self, action = None) -> str:
        """Import an image into the project. Return the resource identifier."""

        # Callback
        def on_image_opened(file_dialog, result, action_callback):
            try:
                # Get the file path
                file = file_dialog.open_finish(result)
                file_path = Path(file.get_path())

                # Get the file name
                info = file.query_info(
                    "standard::name", Gio.FileQueryInfoFlags.NONE, None
                )
                file_name = info.get_name()

                # Create the resource and set the content
                resource = self.project.create_resource(Image, file_name)
                resource.set_content_from_path(file_path)

                logger.info(f"Loaded image as {resource.identifier}")
                action_callback(resource.identifier)
            except GLib.GError:
                logger.info("Error or no file selected")

        # Create and show the dialog
        file_dialog = Gtk.FileDialog(default_filter=self.file_filter_image)
        file_dialog.open(
            self.props.root, None, on_image_opened, action
        )

    def _set_cover(self, resource_identifier):
        """Set the cover for the manuscript."""
        logger.info(f"Set cover to {resource_identifier}")

        if resource_identifier is not None and resource_identifier != '':
            resource = self.project.get_resource(resource_identifier)
            self.project.manuscript.cover = resource
        else:
            self.project.manuscript.cover = None

