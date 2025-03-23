from gi.repository import Adw, Gtk, GObject, Gio, Gdk

from .model import Chapter
from .scene import SceneCard

import logging
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/chapter_column.ui")
class ChapterColumn(Adw.Bin):
    __gtype_name__ = "ChapterColumn"

    chapter_title = GObject.Property(type=str)
    scenes_list = Gtk.Template.Child()
    scene_card_factory = Gtk.Template.Child()

    _chapter = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scene_card_factory.connect("setup", self.on_setup_scene_card)
        self.scene_card_factory.connect("bind", self.on_bind_scene_card, self.scenes_list)

    def connect_to_chapter(self, chapter: Chapter):
        """
        Connect the column to a chapter
        """
        self._chapter = chapter

        # Set the title of the column
        self.set_property('chapter_title', chapter.title)

        # Set the provider model for the scenes
        selection_model = Gtk.NoSelection(model=chapter.scenes)
        self.scenes_list.set_model(selection_model)

        # Configure a chapter as drop target
        drop_target = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop_chapter, chapter)
        self.scenes_list.add_controller(drop_target)

    def on_setup_scene_card(self, _, list_item):
        list_item.set_child(SceneCard())

    def on_bind_scene_card(self, _, list_item, scenes_list):
        # Bind the scene card to its content
        scene = list_item.get_item()
        scene_card = list_item.get_child()
        scene_card.connect_to_scene(scene)

        # Enable drag and drop for a scene
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_prepare, list_item)
        drag_source.connect("drag-begin", self.on_drag_begin, list_item)
        scene_card.add_controller(drag_source)

        # Configure them as drop target for insertion
        drop_target = Gtk.DropTarget.new(SceneCard, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop, list_item, self._chapter)
        scene_card.add_controller(drop_target)

    def on_prepare(self, _source, _x, _y, list_item):
        """
        Prepare for a DnD by attaching the scene card to the event
        """
        # Get the scene card
        scene_card = list_item.get_child()

        # Set it as the value
        value = GObject.Value()
        value.init(SceneCard)
        value.set_object(scene_card)
        return Gdk.ContentProvider.new_for_value(value)

    def on_drag_begin(self, drag_source, drag, list_item):
        """
        Called when the scene starts being dragged around
        """
        # Get the scene card
        scene_card = list_item.get_child()

        # Take a snaphot of the card and set it as icon
        snapshot = Gtk.WidgetPaintable.new(scene_card)
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(Gtk.Picture.new_for_paintable(snapshot))

    def on_drop(self, _drop, scene_card, _x, _y, scenes_list_item, chapter):
        # Get the scene and target position
        scene = scene_card.get_scene()
        target_position = scenes_list_item.get_position()

        # Move the scene card
        logger.info(f'Insert {scene} in {chapter} at {target_position}')
        scene.move_to_chapter(chapter, target_position)

    def on_drop_chapter(self, _drop, scene_card, _x, _y, chapter):
        # Get the scene
        scene = scene_card.get_scene()

        # Move the scene card
        logger.info(f'Drop {scene} into {chapter}')
        scene.move_to_chapter(chapter, -1)

