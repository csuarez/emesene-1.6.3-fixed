# -*- coding: utf-8 -*-
#
#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pyisf
import struct
import drawing
import Theme
import InkDrawDemo

import pygtk
import gtk

def Read( INPUT ):
    data = open(INPUT, 'rb').read()
    image = pyisf.IsfDecoder(open(INPUT, 'rb').read(),debug=False)
    image.image.print_info()
    return image

def Display( Isf ):
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    im = gtk.Image()
    pixmap = Isf.image.get_pixmap()
    im.set_from_pixbuf(pixmap)
    win.add(im)
    win.connect('destroy', gtk.main_quit)

    win.show_all()
    gtk.main()
    
def Window( Isf ):
    theme = Theme.Theme(None)
    win = InkDrawDemo.InkDrawDemo(theme)
    win.connect('destroy', gtk.main_quit)
    gtk.main()

if __name__ == '__main__':
    image = Read('agilix.isf')
    Window(image.image)
