# models/entity.py
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
"""An entity is a story element (person, place, prop, ...)"""

from pathlib import Path
from gi.repository import Gtk, GObject, Gio

import logging

logger = logging.getLogger(__name__)


class EntityType(GObject.GEnum):
    """The type of the entity."""
    __gtype_name__ = "EntityType"
    CHARACTER = 1
    LOCATION = 2
    PROP = 3


class Entity(GObject.Object):
    """An entity is a story element (person, place, prop, ...)"""

    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    def __init__(self, manuscript, identifier: str):
        """Create an entity."""
        super().__init__()
        self._identifier = identifier
        self._manuscript = manuscript
        self._links = Gio.ListStore.new(item_type=EntityLink)

    @GObject.Property(type=GObject.Object)
    def manuscript(self):
        """Return the manuscript the scene is associated to."""
        return self._manuscript

    @GObject.Property(type=str)
    def identifier(self):
        """Return the identifier of the scene."""
        return self._identifier

    @GObject.Property(type=Gio.ListStore)
    def links(self):
        """Return the links from this entity."""
        return self._links


class EntityLink(GObject.Object):
    """A directed link from one entity to another"""

    def __init__(self, predicate: str, target: Entity):
        super().__init__()

        self._predicate = predicate
        self._target = target

    @GObject.Property(type=str)
    def predicate(self) -> str:
        return self._predicate

    @GObject.Property(type=Entity)
    def target(self) -> Entity:
        return self._target



