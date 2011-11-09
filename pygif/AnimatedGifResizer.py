#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2009 Riccardo (C10uD) <c10ud.dev@gmail.com>
###
### This library is free software; you can redistribute it and/or
### modify it under the terms of the GNU Lesser General Public
### License as published by the Free Software Foundation; either
### version 2.1 of the License, or (at your option) any later version.
###
### This library is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
### Lesser General Public License for more details.
###
### You should have received a copy of the GNU Lesser General Public
### License along with this library; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import pygtk
import gtk
import gobject

class AnimatedResizableImage(gtk.Image):
    def __init__(self, maxh=None, maxw=None):
        gtk.Image.__init__(self)    
        
        self.maxh = maxh
        self.maxw = maxw
        self.edited_dimensions = False
        self.mustKill = False
        self.connect('destroy', self._must_destroy)
        
    def _must_destroy(self, *args):
        self.mustKill = True
        
    def set_tooltip(self, tooltiptext):
        self.set_property('has-tooltip', True)
        self.set_property('tooltip-text', tooltiptext)

    def set_from_filename(self, filename):
        animation = gtk.gdk.PixbufAnimation(filename)
        if animation.is_static_image():
            self._place_static(animation)
            return
        self._start_animation(animation)
        
    def set_from_custom_animation(self, animation):
        if animation.is_static_image():
            self._place_static(animation)
            return
        self._start_animation(animation)
          
    def _place_static(self, animation):
        self.h = animation.get_height()
        self.w = animation.get_width()
        ratio = float(self.w) / self.h
        while self.h > self.maxh or self.w > self.maxw:
            self.edited_dimensions = True
            if self.h < self.maxh:
                self.h -= 10
            else:
                self.h = self.maxh
            self.w = self.h * ratio
            
        if self.edited_dimensions:
            self.set_from_pixbuf(animation.get_static_image().scale_simple(\
                    int(self.w), self.h, gtk.gdk.INTERP_BILINEAR))    
        else:
            self.set_from_pixbuf(animation.get_static_image())    
            
    def _start_animation(self, animation):
        iteran = animation.get_iter()
        
        self.h = animation.get_height()
        self.w = animation.get_width()
        ratio = float(self.w) / self.h
        while self.h > self.maxh or self.w > self.maxw:
            self.edited_dimensions = True
            if self.h <= self.maxh:
                self.h -= 10
            else:
                self.h = self.maxh
            self.w = self.h * ratio  
        
        if not self.edited_dimensions:
            self.set_from_animation(animation) # fallback to default handler
            return
         
        gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)
    
    def _advance(self, iteran):
        iteran.advance()
        if not self.mustKill:
            self.set_from_pixbuf(iteran.get_pixbuf().scale_simple(int(self.w), \
                    self.h, gtk.gdk.INTERP_NEAREST))
        else:
            return False # end the update game.
        
        gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)
        return False

    

def close_application(widget, event, data=None):
    gtk.main_quit()
    return False
    
if __name__ == "__main__":
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.connect("delete_event", close_application)
    window.set_border_width(10)
    window.show()
    hbox = gtk.HBox()
    
    ari = AnimatedResizableImage(800, 800)
    ari.set_tooltip('hy')
    ari.set_from_filename('toggi.gif')
        
    hbox.pack_start(ari)
    window.add(hbox)
    window.show_all()
    gtk.main()

