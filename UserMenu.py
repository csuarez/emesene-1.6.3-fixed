# -*- coding: utf-8 -*-

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

import gtk
import desktop
from Parser import Url

class UserMenu(gtk.Menu):
    '''This class represents the popup menu that is displayed when you right
    click an user on the userList'''

    def __init__(self , controller, user, group):
        gtk.Menu.__init__(self)

        self.controller = controller

        self.user = user
        self.group = group

        openConversationMenuItem = self.newImageMenuItem(
            _("_Open Conversation"), gtk.STOCK_OPEN)
        self.add(openConversationMenuItem)
        openConversationMenuItem.show()

        sendMailMenuItem = self.newImageMenuItem(_("Send _Mail"), None,
            None, controller.theme.getSmiley("(e)"))
        self.add(sendMailMenuItem)
        sendMailMenuItem.show()

        copyEmail = self.newImageMenuItem(_("Copy email"), gtk.STOCK_COPY)
        self.add(copyEmail)
        copyEmail.show()

        viewMenuItem = self.newImageMenuItem(_("_View"),
            gtk.STOCK_FIND)
        self.viewMenu = gtk.Menu()
        viewMenuItem.set_submenu(self.viewMenu)
        viewMenuItem.show_all()
        self.add(viewMenuItem)

        profileMenuItem = self.newImageMenuItem(_("Profile"),
            gtk.STOCK_NETWORK)
        self.viewMenu.add(profileMenuItem)
        profileMenuItem.show()
        profileMenuItem.connect('activate', self.on_profile_activate)


        avatarHistory = self.newImageMenuItem(_("Avatar history"), gtk.STOCK_OPEN)
        self.viewMenu.add(avatarHistory)
        avatarHistory.show()
        avatarHistory.connect('activate', self.on_show_avatar_history_activate)

        self.controller.emit("usermenu-item-add", self)

        parser = controller.unifiedParser
        sep = False

        for i in user.nick, user.personalMessage:
            urls = [str(x.url) for x in parser.parse(None, i)
                    if type(x) == Url]

            for url in urls:
		if url[:4] == 'www.':
            	    url = 'http://'+url
                if len(url) > 20:
                    dispUrl = url[:20] + '...'
                else:
                    dispUrl = url

                PMurl = self.newImageMenuItem(dispUrl, gtk.STOCK_OPEN)
                PMurl.connect("activate", self.on_PMurl, url)

                if not sep:
                    self.add(gtk.SeparatorMenuItem())
                    sep = True
                self.add(PMurl)

        self.add(gtk.SeparatorMenuItem())

        if (user.alias == ''):
            renameUserMenuItem = self.newImageMenuItem(_("_Set contact alias..."),
                gtk.STOCK_EDIT)
        else:
            renameUserMenuItem = self.newImageMenuItem(_("_Edit contact alias..."),
                gtk.STOCK_EDIT)

        self.add(renameUserMenuItem)
        renameUserMenuItem.show()

        self.add(gtk.SeparatorMenuItem())

        if not user.blocked:
            blockUserMenuItem = self.newImageMenuItem(_("_Block"),
                gtk.STOCK_STOP)
            self.add(blockUserMenuItem)
            blockUserMenuItem.show()
            blockUserMenuItem.connect("activate", self.on_block_user_activate)
        else:
            unblockUserMenuItem = self.newImageMenuItem(_("_Unblock"),
                gtk.STOCK_APPLY)
            self.add(unblockUserMenuItem)
            unblockUserMenuItem.show()
            unblockUserMenuItem.connect("activate",
                self.on_unblock_user_activate)

        deleteUserMenuItem = self.newImageMenuItem(_("_Remove contact"),
            gtk.STOCK_DELETE)
        self.add(deleteUserMenuItem)
        deleteUserMenuItem.show()

        self.add(gtk.SeparatorMenuItem())

        moveMenuItem = self.newImageMenuItem(_("M_ove to group"),
            gtk.STOCK_REDO)
        moveMenu = gtk.Menu()
        groups = self.controller.msn.getGroupNames()
        if groups == []:
            addGroupMenuItem = self.newImageMenuItem(_('Add _group'),
                gtk.STOCK_ADD)
            moveMenu.add(addGroupMenuItem)
            addGroupMenuItem.connect('activate', self.on_add_group_activate)
        else:
            for i in self.controller.msn.getGroupNames():
                i = i.replace('_', '__') # don't use _ as mnemonic
                menuItem = self.newImageMenuItem (i)
                moveMenu.add(menuItem)
                menuItem.connect("activate" , self.moveToActivate, i)

        moveMenuItem.set_submenu(moveMenu)
        moveMenuItem.show_all()
        self.add(moveMenuItem)

        copyMenuItem = self.newImageMenuItem(_("_Copy to group"),
            gtk.STOCK_COPY)
        copyMenu = gtk.Menu()

        groups = self.controller.msn.getGroupNames()
        if groups == []:
            addGroupMenuItem = self.newImageMenuItem(_('Add _group'),
                gtk.STOCK_ADD)
            copyMenu.add(addGroupMenuItem)
            addGroupMenuItem.connect('activate', self.on_add_group_activate)
        else:
            for i in self.controller.msn.getGroupNames():
                i = i.replace('_', '__')
                menuItem = self.newImageMenuItem (i)
                copyMenu.add(menuItem)
                menuItem.connect("activate", self.copyToActivate, i)

        copyMenuItem.set_submenu(copyMenu)
        copyMenuItem.show_all()
        self.add(copyMenuItem)

        removeFromGroupMenuItem = self.newImageMenuItem(
            _("R_emove from group"), gtk.STOCK_DELETE)
        if group.name == "No group":
            removeFromGroupMenuItem.set_sensitive(False)
        self.add(removeFromGroupMenuItem)
        removeFromGroupMenuItem.show()
        removeFromGroupMenuItem.connect("activate", self.removeFromActivate)

        self.show_all()

        renameUserMenuItem.connect("activate", self.on_rename_user_activate)
        deleteUserMenuItem.connect("activate", self.on_delete_user_activate)
        openConversationMenuItem.connect("activate",
            self.on_open_conversation_activate)

        copyEmail.connect("activate", self.on_copy_email_activate)
        sendMailMenuItem.connect("activate" , self.on_send_mail_activate)


    def newImageMenuItem(self, label, stock=None, img=None, animation=None):
        mi = gtk.ImageMenuItem(_(label))

        if stock:
            mi.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
        elif img:
            image = gtk.Image()
            image.set_from_pixbuf(img)
            mi.set_image(image)
        elif animation:
            image = gtk.Image()
            image.set_from_animation(animation)
            mi.set_image(image)
        return mi

    def on_PMurl(self, widget, url):
        desktop.open(str(url))

    def moveToActivate(self, _menuItem, group):
        self.controller.contacts.move_to_group(self.user.email,
            self.group.name, group)

    def copyToActivate(self, _menuItem, group):
        self.controller.contacts.add_to_group(self.user.email, group)

    def removeFromActivate(self, _menuItem):
        self.controller.contacts.remove_from_group(self.user.email,
            self.group.name)

    def on_delete_user_activate(self, *args):
        self.controller.contacts.remove(self.user.email)

    def on_rename_user_activate(self, *args):
        self.controller.contacts.set_alias_dialog(self.user.email)

    def on_block_user_activate(self, *args):
        self.controller.contacts.block(self.user.email)

    def on_unblock_user_activate(self, *args):
        self.controller.contacts.unblock(self.user.email)

    def on_profile_activate(self, *args):
        self.controller.seeProfile(self.user.email)

    def on_open_conversation_activate(self, *args):
        self.controller.newConversation(None, self.user.email, None, True)

    def on_copy_email_activate(self, *args):
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.user.email)

    def on_send_mail_activate(self, *args):
        desktop.open("mailto:%s" % self.user.email)

    def on_show_avatar_history_activate(self,  *args):
        self.controller.seeAvatarHistory(self.user.email)

    def on_add_group_activate(self, *args):
        self.controller.groups.add_dialog()
