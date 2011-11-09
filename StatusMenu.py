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
import emesenelib.common
import os

class StatusMenu(gtk.Menu):
    '''This class represents the status menu where you can select a given
    status and it will be changed. This is a standalone class because
    it is used in two classes (MainMenu and TrayIcon)'''

    def __init__(self, controller):
        '''Contructor'''
        gtk.Menu.__init__(self)

        self.controller = controller
        self.theme = self.controller.theme
        
        j = 0
        for i in self.controller.status_ordered[0]:
            if i not in self.controller.bad_statuses:
                menuItem = self.newImageMenuItem (
                    self.controller.status_ordered[3][j], None,
                    self.controller.theme.statusToPixbuf(i))
                self.add(menuItem)
                if os.name == "nt":
                    menuItem.connect("button-release-event", self.activateNT, i)
                else:
                    menuItem.connect("activate", self.activate, i)
            j += 1

    def newImageMenuItem(self, label, stock = None, img = None):
        mi = gtk.ImageMenuItem(_(label))

        if stock:
            mi.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
        elif img:
            image = gtk.Image()
            image.set_from_pixbuf(img.scale_simple(16,16,gtk.gdk.INTERP_BILINEAR))
            mi.set_image(image)
        return mi

    def newCheckMenuItem(self, label, checked):
        mi = gtk.CheckMenuItem(_(label))
        mi.set_active(checked)
        return mi

    def activate(self, menuitem, status):
        '''change the status with the userparam'''
        self.controller.msn.changeStatus(status)

    def activateNT(self, menuitem, event, status):
        '''change the status with the userparam, ugly windows hack'''
        self.controller.msn.changeStatus(status)

