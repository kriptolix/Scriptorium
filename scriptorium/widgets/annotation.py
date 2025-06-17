# writer_popover.py
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

# Code inspired from Eloquent:
# https://github.com/sonnyp/Eloquent/blob/main/src/widgets/SuggestionPopover.js

from gi.repository import Adw, Gtk, GObject, GLib
from scriptorium.globals import BASE
from scriptorium.models import Annotation

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/widgets/annotation.ui")
class AnnotationCard(Adw.Bin):
    __gtype_name__ = "AnnotationCard"

    category = GObject.Property(type=str)
    message = GObject.Property(type=str)
    title = GObject.Property(type=str)
    icon = Gtk.Template.Child()
    header = Gtk.Template.Child()

    def __init__(self, annotation: Annotation):
        super().__init__()

        self.title = annotation.title
        self.message = annotation.message
        self.category = annotation.category

        if annotation.category == "warning":
            self.icon.add_css_class("annotation-warning")
            self.icon.set_from_icon_name("dialog-warning-symbolic")
        elif annotation.category == "error":
            self.icon.add_css_class("annotation-error")
            self.icon.set_from_icon_name("dialog-error-symbolic")
        elif annotation.category == "hint":
            self.icon.add_css_class("annotation-hint")
            self.icon.set_from_icon_name("dialog-information-symbolic")
    
