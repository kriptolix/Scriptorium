from gi.repository import Gtk, GObject, Gio
from .resource import Resource

class Link(Resource):
    """A directed link from one resource to another."""
    __gtype_name__ = "Link"

    source = GObject.Property(type=Resource)
    predicate = GObject.Property(type=str)
    target = GObject.Property(type=Resource)

    # The index of this link when several exist with the same source+predicate
    index = GObject.Property(type=int)

    def __init__(self, project, source: Resource, predicate: str, target: Resource):
        identifier = f"{source.identifier}_{predicate}_{target.identifier}"
        super().__init__(project, identifier)
        self.title = f"{source.title} {predicate} {target.title}"

        self.source = source
        self.predicate = predicate
        self.target = target

        self.index = 0


