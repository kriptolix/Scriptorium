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

    edit_button = Gtk.Template.Child()
    suffixes = Gtk.Template.Child()

    def __init__(self, entity: Entity, **kwargs):
        super().__init__(**kwargs)
        self._entity = entity

        # Configure the information for the entity
        self.set_property("title", entity.title)
        self.set_property("synopsis", entity.synopsis)

        self.bind_property(
            "title", entity, "title",
            GObject.BindingFlags.BIDIRECTIONAL
        )
        self.bind_property(
            "synopsis", entity, "synopsis",
            GObject.BindingFlags.BIDIRECTIONAL
        )

    @GObject.Property(type=Entity)
    def entity(self):
        return self._entity
