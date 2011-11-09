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

class GroupMenu(gtk.Menu):
    '''This class represent the popup menu that is displayed when you right click a group on
    the userList'''

    def __init__(self, controller, group):
        gtk.Menu.__init__(self)

        self.controller = controller
        self.group = group

        someoneBlocked = False
        someoneUnblocked = False

        addGroupMenuItem = self.newImageMenuItem\
                    (_('Add _group...'), gtk.STOCK_ADD)
        self.add(addGroupMenuItem)

        addGroupMenuItem.connect('activate', self.on_add_group_activate)

        if group.id != 'nogroup':
            renameGroupMenuItem = self.newImageMenuItem\
                        (_('Re_name group...'), gtk.STOCK_EDIT)
            self.add(renameGroupMenuItem)

            self.add(gtk.SeparatorMenuItem())

            for email, user in self.group.users.items():
                if not user.blocked and not someoneUnblocked:
                    blockGroupMenuItem = self.newImageMenuItem\
                        (_('Block group'), gtk.STOCK_STOP)
                    self.add(blockGroupMenuItem)
                    blockGroupMenuItem.connect('activate', self.on_block_group_activate)
                    someoneUnblocked = True

                elif user.blocked and not someoneBlocked:
                    unblockGroupMenuItem = self.newImageMenuItem\
                        (_('Unblock group'), gtk.STOCK_APPLY)
                    self.add(unblockGroupMenuItem)
                    unblockGroupMenuItem.connect('activate', self.on_unblock_group_activate)
                    someoneBlocked = True

                elif someoneBlocked and someoneUnblocked:
                    break

            self.add(gtk.SeparatorMenuItem())

            deleteGroupMenuItem = self.newImageMenuItem\
                        (_('Re_move group'), gtk.STOCK_DELETE)
            self.add(deleteGroupMenuItem)

            deleteGroupMenuItem.connect('activate', self.on_delete_group_activate)
            renameGroupMenuItem.connect('activate', self.on_rename_group_activate)

        self.show_all()

    def newImageMenuItem(self, label, stock = None, img = None):
        mi = gtk.ImageMenuItem(_(label))

        if stock:
            mi.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
        elif img:
            image = gtk.Image()
            image.set_from_pixbuf(img)
            mi.set_image(image)
        return mi

    def on_add_user_group_activate(self, *args):
        self.controller.addUserDialog(self.group.name)

    def on_add_group_activate(self, *args):
        self.controller.groups.add_dialog()

    def on_delete_group_activate(self, *args):
        self.controller.removeGroup(self.group)

    def on_rename_group_activate(self, *args):
        self.controller.groups.rename_dialog(self.group.name)

    def on_block_group_activate(self, *args):
        for email, user in self.group.users.items():
            if not user.blocked:
                self.controller.contacts.block(email)

    def on_unblock_group_activate(self, *args):
        for email, user in self.group.users.items():
            if user.blocked:
                self.controller.contacts.unblock(email)
