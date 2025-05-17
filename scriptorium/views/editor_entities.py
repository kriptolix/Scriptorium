# editor_entity.py
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


from gi.repository import Adw, Gtk, GObject, Gio
from scriptorium.widgets import EntityCard
from scriptorium.globals import BASE

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/views/editor_entities.ui")
class ScrptEntityPanel(Adw.NavigationPage):
    __gtype_name__ = "ScrptEntityPanel"

    __title__ = "Elements"
    __icon_name__ = "find-location-symbolic"
    __description__ = "Set the key entities of the story"

    entities_list = Gtk.Template.Child()
    add_button = Gtk.Template.Child()

    def __init__(self, editor, **kwargs):
        """Create an instance of the panel."""
        super().__init__(**kwargs)
        self._manuscript = editor.manuscript

        # Connect to the entities of the manuscript
        self.entities_list.bind_model(
            editor.manuscript.entities, self.create_entity_card
        )

    def on_add_entity(self, entity_type):
        logger.info(entity_type)

    def create_entity_card(self, entity):
        """Create an instance of the entity card."""
        card = EntityCard(entity)
        return card

