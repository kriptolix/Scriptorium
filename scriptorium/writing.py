# writing.py
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

from gi.repository import Gtk
from gi.repository import Adw

class CustomModel(Gtk.StringList, Gtk.SectionModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for i in range(1, 21):
            self.append(f"Item {i}")

    def do_get_section(self, position):
        print (position)
        start = position
        end = start + 5
        return (start, end)

@Gtk.Template(resource_path="/com/github/cgueret/Scriptorium/ui/writing.ui")
class Writing(Adw.Bin):
    __gtype_name__ = "Writing"

    list_view = Gtk.Template.Child()
    item_factory = Gtk.Template.Child()
    header_factory = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        custom_model = CustomModel()


        self.item_factory.connect("setup", self.on_setup_item)
        self.item_factory.connect("bind", self.on_bind_item)

        self.header_factory.connect("setup", self.on_setup_header)
        self.header_factory.connect("bind", self.on_bind_header)

        selection_model = Gtk.SingleSelection(model=custom_model)
        selection_model.connect("selection-changed", self.on_selection_changed)
        self.list_view.set_model(selection_model)

    def on_setup_item(self, _, list_item):
        list_item.set_child(Gtk.Label(margin_start=12, halign=Gtk.Align.START))

    def on_bind_item(self, _, list_item):
        item = list_item.get_item()
        label = list_item.get_child()
        label.set_label(item.get_string())

    def on_setup_header(self, _, list_item):
        list_item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def on_bind_header(self, _, list_item):
        item = list_item.get_item()
        label = list_item.get_child()
        label.set_label("Header " + item.get_string())

    def on_selection_changed(self, selection, position, n_items):
        print (selection)
        print (position, n_items)
        selected_item = selection.get_selected()
        print(f"Model item selected from view: {selected_item}")



