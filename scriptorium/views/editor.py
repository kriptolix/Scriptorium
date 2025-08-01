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

from scriptorium.globals import BASE
from scriptorium.dialogs import ScrptAddDialog
from scriptorium.widgets import ThemeSelector
from scriptorium.models import Project, Scene, Chapter

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

    def __init__(self):
        """Create a new instance of the editor."""
        super().__init__()

        # Connect an instance of the theme button to the menu
        popover = self.win_menu.get_popover()
        popover.add_child(ThemeSelector(), "theme")

        # Create the action to add a new resource
        action = Gio.SimpleAction.new(
            name="add_resource",
            parameter_type=GLib.VariantType.new("(ss)")
            )
        action.connect("activate", self.on_add_resource)

        group = Gio.SimpleActionGroup()
        group.add_action(action)

        self.insert_action_group("editor", group)

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

