from gi.repository import Adw, Gtk, GObject
from scriptorium.models import Entity
from scriptorium.globals import BASE

import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{BASE}/widgets/entity_card.ui")
class EntityCard(Adw.Bin):
    __gtype_name__ = "EntityCard"

    _entity = None
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    suffixes = Gtk.Template.Child()
    prefixes = Gtk.Template.Child()
    avatar = Gtk.Template.Child()

    def __init__(
        self, entity: Entity, can_activate: bool = False, can_move: bool = False
    ):
        super().__init__()
        self._entity = entity

        # Configure the information for the entity
        entity.bind_property(
            "title",
            self,
            "title",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
        entity.bind_property(
            "synopsis",
            self,
            "synopsis",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        # Connect the title to the avatar
        entity.bind_property(
            "title", self.avatar, "text", GObject.BindingFlags.SYNC_CREATE
        )

        # Adjust the display of drag and activation extra
        self.prefixes.set_visible(can_move)
        self.suffixes.set_visible(can_activate)

    @GObject.Property(type=Entity)
    def entity(self):
        return self._entity

