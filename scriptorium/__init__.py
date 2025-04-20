# Set the target version of the libraries
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
gi.require_version("Tsparql", "3.0")

# Manually init Adw to be sure it's recognized
from gi.repository import Adw
Adw.init()

# Load the custom widget
from .multiline_entry_row import MultiLineEntryRow



