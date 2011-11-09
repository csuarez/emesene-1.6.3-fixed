# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import gobject

SEXYLIKE = False
if gtk.gtk_version >= (2, 16, 1):
    SEXYLIKE = True
    
class FilterEntry(gtk.HBox):

    __gsignals__ = { 'filter-entry-lost-focus' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ()),
    }

    def __init__(self, callback):
        '''the callback is a function that receive
        the string typed here as only parameter'''

        gtk.HBox.__init__(self)
        self.set_border_width(2)
        #self.set_spacing(4)
        self.callback = callback

        if SEXYLIKE:
            self.entry = gtk.Entry()
            self.entry.set_property('primary-icon-stock', gtk.STOCK_FIND)
            self.entry.set_property('secondary-icon-stock', gtk.STOCK_CLEAR)
            self.entry.set_property('primary-icon-activatable' , False)
            self.entry.connect('icon-release', self.secondary_icon_clicked)
        else:
            self.entry = gtk.Entry()
            self.icon = gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_MENU)
            self.pack_start(self.icon, False)
            
        self.entry.connect('changed', self.entryChanged)
        self.entry.connect('key_press_event', self.entryKeypressEvent)
        self.entry.connect('focus-out-event', self.lost_focus)

        self.pack_start(self.entry)
        self.show_all()
    
    def secondary_icon_clicked(self, entry, icontype, event):
        ''' clean the entry '''
        # <enum GTK_ENTRY_ICON_SECONDARY of type GtkEntryIconPosition> == 1
        if icontype == 1 and event.type == gtk.gdk.BUTTON_RELEASE:
            self.entry.props.text = ''

    def entryChanged(self, *args):
        self.callback(self.entry.get_text())

    def entryKeypressEvent(self, widget, event):
        keyval = gtk.gdk.keyval_name(event.keyval)
        if keyval == 'Escape':
            self.entry.props.text = ''
            return True
        return False

    def lost_focus(self, widget, event):
        self.emit('filter-entry-lost-focus')
