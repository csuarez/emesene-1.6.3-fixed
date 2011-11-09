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

import os
import gtk
from gobject import timeout_add, source_remove

from Theme import resizePixbuf
import CustomEmoticons

import stock
import dialog

class SmilieWindow(gtk.Window):
    '''this is the window that opens when you press the smilie button on the
    conversation window'''

    def __init__(self, controller, callback, parent=None):
        '''class constructor'''
        gtk.Window.__init__(self)

        self.set_decorated(False)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        if parent:
            self.set_transient_for(parent)
	
        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_resizable(False)
        self.set_title(_('Smilies'))
        self.set_border_width(2)

        self.callback = callback

        self.vbox = gtk.VBox()
        table1 = gtk.Table()
	
        self.theme = controller.theme
        self.controller = controller

        self.customEmoticons = controller.customEmoticons
        self.config = controller.config

        self.closed = True

        x = 0
        y = 0

        smilie_list = self.theme.getSingleSmileysList()

        imSmileys = ['*red+u','*bgca','*hsus', \
                     '*naf','*mssoc','*9mil','*sierra', \
                     '*help','*komen','*unicef']

        for i in smilie_list:
            if i in imSmileys:
                continue

            elif x == 16:
                x = 0
                y += 1
            try:
                button = gtk.Button()
                button.set_relief(gtk.RELIEF_NONE)
                button.set_tooltip_text(i)
                smilieImage = gtk.Image()
                pixbuf = self.theme.getSmiley(i)
                if type(pixbuf) == gtk.gdk.PixbufAnimation:
                    smilieImage.set_from_animation(pixbuf)
                else:
                    smilieImage.set_from_pixbuf(pixbuf)
                button.set_image(smilieImage)
                button.connect('clicked', self.clicked, i)
                button.connect('enter-notify-event',
                    self.on_enter_notify_event)
                table1.attach(button, x, x+1, y, y+1)
            except Exception, e:
                print 'error adding smilie ', i
                print e
                x -= 1
            x += 1

        self.ceLabel = gtk.Label(_('Custom Emoticons'))

        self.vbox.pack_start(table1)
        self.vbox.pack_start(self.ceLabel)

        self.add(self.vbox)
        self.vbox.show_all()
        self.connect('delete-event', self.on_delete_event)
        self.connect('leave-notify-event', self.on_leave_notify_event)
        self.connect('enter-notify-event', self.on_enter_notify_event)
        self.connect('key-press-event', self.on_key_press)

        self.tag = None

    def on_leave_notify_event(self, *args):
        # args: gtk.Window, gtk.gdk.Event
        if not self.tag and not self.closed and \
            args[1].detail != gtk.gdk.NOTIFY_INFERIOR:
            self.tag = timeout_add(500, self.hide)

    def on_enter_notify_event(self, *args):
        if (self.tag):
            source_remove(self.tag)
            self.tag = None

    def on_delete_event(self, *args):
        self.hide()
        self.closed = True
        return True

    def on_key_press(self, widget, event):
        if gtk.keysyms.Escape == event.keyval:
            self.hide()

    def clicked(self, button, smilie):
        self.hide()
        self.callback(smilie)

    def event(self, button, event, smilie):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:

            # -- Custom Emoticon Menu --
            self.emoMenu = gtk.Menu()
            self.emoMenu.connect('enter-notify-event', self.on_enter_notify_event)

            self.shortcutItem = gtk.ImageMenuItem(_("Change shortcut"))
            self.shortcutItem.connect('enter-notify-event', self.on_enter_notify_event)
            self.shortcutItem.set_image(gtk.image_new_from_stock(
                gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
            self.shortcutItem.connect("activate", self.onEditShortcut,
                smilie)

            self.deleteItem = gtk.ImageMenuItem(_("Delete"))
            self.deleteItem.connect('enter-notify-event', self.on_enter_notify_event)
            self.deleteItem.set_image(gtk.image_new_from_stock(
                gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU))
            self.deleteItem.connect("activate", self.onDeleteEmo, smilie)

            self.emoMenu.add(self.shortcutItem)
            self.emoMenu.add(self.deleteItem)

            self.emoMenu.show_all()
            # -----

            self.emoMenu.popup(None, None, None, event.button, event.time)

    def onDeleteEmo(self, button, shortcut):
        self.customEmoticons.delete(shortcut)
        self.fillCETable()

    def onEditShortcut(self, button, shortcut):
        self.hide()

        def _on_ce_edit_cb(response, text=''):
            '''method called when the edition is done'''

            if response == stock.ACCEPT:
                if text:
                    ret, msg = self.customEmoticons.chageShortcut(shortcut,
                        text)
                    if not ret:
                        dialog.error(msg)

                else:
                    dialog.error(_("Empty shortcut"))

        window = dialog.entry_window(_("New shortcut"), shortcut,
            _on_ce_edit_cb, _("Change shortcut"))
        window.show()

    def clickedAdd(self, button, *args):
        self.hide()

    def show(self):
        self.fillCETable()
        gtk.Window.show(self)
        self.tag = None
        self.closed = False

    def hide(self):
        gtk.Window.hide(self)
        if (self.tag):
            source_remove(self.tag)
            self.tag = None
        self.closed = True

    def fillCETable(self):
        try:
            self.vbox.remove(self.ceTable)
            self.vbox.remove(self.scroll)
            self.vbox.remove(self.buttonBox)
        except:
            pass

        if not self.customEmoticons:
            print "self.customEmoticons is None"
            return

        self.ceTable = gtk.Table()
        x = 0
        y = 0

        list = self.customEmoticons.list

        items = list.items()
        items.sort()

        for shortcut, filename in items:

            if x == 15:
                x = 0
                y += 1
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
                pixbuf = resizePixbuf(pixbuf, 24, 24)
                button = gtk.Button()
                button.set_relief(gtk.RELIEF_NONE)
                button.set_tooltip_text(shortcut)
                smilieImage = gtk.Image()
                smilieImage.set_from_pixbuf(pixbuf)
                button.set_image(smilieImage)
                button.connect('clicked', self.clicked, shortcut)
                button.connect('event', self.event, shortcut)
                button.connect('enter-notify-event', self.on_enter_notify_event)
                self.ceTable.attach(button, x, x+1, y, y+1,False)
            except:
                print 'Error in smiley', shortcut, filename
                x -= 1
            x += 1

        #Scroll
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_size_request(400, 90)
        self.scroll.set_policy(gtk.POLICY_NEVER , gtk.POLICY_ALWAYS)
        self.scroll.set_shadow_type(gtk.SHADOW_IN)

        #Add button
        self.buttonBox = gtk.HButtonBox()

        button = gtk.Button(None)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,
            gtk.ICON_SIZE_BUTTON))
        button.connect('clicked', self.addClicked, self.controller)
        button.connect('enter-notify-event', self.on_enter_notify_event)

        self.buttonBox.pack_start(button)

        if y == 0:
            self.vbox.pack_start(self.ceTable)
            self.vbox.pack_start(self.buttonBox)
        else:
	        self.scroll.add_with_viewport(self.ceTable)
	        self.vbox.pack_start(self.scroll)
	        self.vbox.pack_start(self.buttonBox)

        self.vbox.show_all()

    def addClicked(self, button, controller):
        self.hide()

        def _on_ce_choosed(response, path, shortcut, size):
            '''method called when the ce is selected'''

            if response != stock.ACCEPT:
                return

            self.config.user['emoticonDir']= os.path.dirname(path)

            if size == dialog.CEChooser.SMALL:
                size = 0
            else:
                size = 1

            ret,msg =  self.customEmoticons.create(shortcut, path, size)
            if not ret:
                dialog.error(msg)

        #Let's create the list of customs emoticons for dialog.CEChooser. \
        #  _on_changed
        #Arielj: -why is this method getting config from controller? there's a self.config attribute
        #        -I've add a self.controller attribute to call this method when add is clicked
        #        -we shouldn't need to pass a controller as a parameter with that new attribute
        #        -CustomEmoticons should receive only the controller and get the from that controller inside.
        config = controller.config
        ce = CustomEmoticons.CustomEmoticons(config, controller)
        smilie_list = ce.loadMap()

        dialog.set_custom_emoticon(self.config.user['emoticonDir'],
            _on_ce_choosed, smilie_list)

