from gi.repository import Adw, Gtk, GObject
from scriptorium.models import Chapter
import logging

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/widgets/chapter.ui")
class ChapterCard(Adw.Bin):
    __gtype_name__ = "ChapterCard"

    _scene = None
    title = GObject.Property(type=str)
    synopsis = GObject.Property(type=str)

    edit_button = Gtk.Template.Child()
    suffixes = Gtk.Template.Child()

    def __init__(self, chapter: Chapter):
        super().__init__()
        self._chapter = chapter

        # Configure the information for the scene
        self.set_property('title', chapter.title)
        self.set_property('synopsis', chapter.synopsis)

        self.bind_property(
            "title",
            chapter,
            "title",
            GObject.BindingFlags.BIDIRECTIONAL
        )
        self.bind_property(
            "synopsis",
            chapter,
            "synopsis",
            GObject.BindingFlags.BIDIRECTIONAL
        )

    @GObject.Property(type=Chapter)
    def chapter(self):
        return self._chapter

    def hide_suffix(self):
        self.suffixes.set_visible(False)
