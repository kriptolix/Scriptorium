import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw
from gi.repository import Gtk

from .writing import EditorWritingView
from .plotting import EditorPlottingView
from .formatting import EditorFormattingView



