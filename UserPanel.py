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

import gc
import re
import gtk
import pango
import subprocess

import desktop
import Widgets
import StatusMenu
from SmileyRenderer import SmileyLabel
from Parser import PangoDataType

import dialog

DOMAIN_REGEXP = re.compile('^windowslive(\.[a-zA-Z]{2,3})?\.[a-zA-Z]{2,3}$|'
                           '^live(\.[a-zA-Z]{2,3})?\.[a-zA-Z]{2,3}$|'
                           '^msn(\.[a-zA-Z]{2,3})?\.[a-zA-Z]{2,3}|'
                           '^hotmail(\.[a-zA-Z]{2,3})?\.[a-zA-Z]{2,3}')
class UserPanel(gtk.HBox):
    '''this class is the panel that will contain the user photo, his nick and his status'''

    def __init__(self, controller):
        '''Constructor'''
        gtk.HBox.__init__(self)

        self.controller = controller
        self.theme = controller.theme
        self.config = controller.config

        self.set_border_width(2)

        self.smileysCache = {}
        self.hasSmilies = True

        self.tNick = gtk.Entry(max=129)
        self.tNick.set_text(self.controller.msn.nick.replace('\n', ' '))
        self.tNick.set_no_show_all(True)
        
        self.lNick = SmileyLabel('', self.controller.widget_style)
        self.lNick.set_ellipsize(pango.ELLIPSIZE_END)

        self.bNick = gtk.Button()
        self.bNick.set_relief(gtk.RELIEF_NONE)
        self.bNick.set_alignment(0, 0)
        self.bNick.add(self.lNick)

        iconMail = self.theme.getSmiley("(e)") #email icon

        self.mailButton = ImageButton(iconMail, '(0)')
        self.mailButton.set_relief(gtk.RELIEF_NONE)
        self.mailButton.set_tooltip_text(_('Click here to access your mail'))

        self.statusIcon = self.theme.statusToPixbuf(self.controller.msn.status)
        self.statusButton = ImageButton(self.statusIcon)
        self.controller.msn.connect('self-status-changed',\
                                          self.update_status_icon)
        self.statusButton.set_relief(gtk.RELIEF_NONE)
        self.statusButton.set_tooltip_text(_('Click here to change your status'))

        self.statusMenu = StatusMenu.StatusMenu(self.controller)

        self.tPersonalMessage = gtk.Entry(max=129)
        self.tPersonalMessage.set_text(self.controller.contacts.get_message())
        self.tPersonalMessage.set_no_show_all(True)
        self.lPersonalMessage = SmileyLabel('',
            self.controller.widget_style)
        self.lPersonalMessage.set_ellipsize(pango.ELLIPSIZE_END)
        self.bPersonalMessage = gtk.Button()
        self.bPersonalMessage.set_relief(gtk.RELIEF_NONE)
        self.bPersonalMessage.set_alignment(0, 0)
        self.bPersonalMessage.add(self.lPersonalMessage)

        mediaIcon = self.theme.getSmiley("(8)") #media icon
        # at the bottom is the code to handle starting toggled
        self.mediaButton = ImageToggleButton(mediaIcon)
        self.mediaButton.set_relief(gtk.RELIEF_NONE)
        
        try: # why, oh why, gtk must be so angry?
            self.mediaButton.set_tooltip_text(_('Toggle sending current playing song'))
        except:
            pass
            
        self.lMedia = gtk.Label(_("No media playing"))
        self.lMedia.set_ellipsize(pango.ELLIPSIZE_END)
        self.bMedia = gtk.Button()
        self.bMedia.set_relief(gtk.RELIEF_NONE)
        self.bMedia.set_alignment(0, 0)
        self.bMedia.add(self.lMedia)
        self.bMedia.connect('clicked', self.onMediaClicked)
        self.lMedia.set_no_show_all(True)
        self.bMedia.set_no_show_all(True)

        self.bNick.set_tooltip_text(_('Click here to set your nick name'))
        self.bPersonalMessage.set_tooltip_text(_('Click here to set your personal message'))
        self.bMedia.set_tooltip_text(_('Your current media'))

        self.image = Widgets.avatarHolder(cellDimention = 48)
        self.imageEventBox = gtk.EventBox()
        self.imageEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.imageEventBox.connect('button-press-event', self.avatarClicked)
        self.imageEventBox.add(self.image)
        self.imageEventBox.set_tooltip_text(_('Click here to set your avatar'))
        #frame = gtk.AspectFrame()
        #frame.add(self.imageEventBox)
        if self.controller.avatar:
            self.image.set_from_pixbuf(self.controller.avatar.getThumb())
        else:
            self.pixbuf = self.controller.theme.getImage('userPanel')
            self.image.set_from_pixbuf(self.pixbuf)

        self.tNick.connect('activate', self.on_nick_changed, None, False)
        self.tNick.connect('focus-out-event', self.on_nick_changed, True)
        self.bNick.connect('clicked', self.on_nick_clicked)
        self.tPersonalMessage.connect('activate', self.on_pm_changed, None, False)
        self.tPersonalMessage.connect('focus-out-event', self.on_pm_changed, True)
        self.bPersonalMessage.connect('clicked', self.on_pm_clicked)
        self.mediaButton.connect("toggled", self.onToggleMedia)

        self.mailButton.connect('clicked', self.onMaiButtonClicked)

        self.controller.msn.connect('self-personal-message-changed',
            self.personalMessageChanged)
        self.controller.msn.connect('self-nick-changed', self.selfNickChanged)
        self.controller.msn.connect('self-current-media-changed',
            self.currentMediaChanged)

        self.mailButton.setText('('+str(self.controller.getUnreadMails()) +')')
        self.controller.msn.connect('initial-mail-notification',
            self.updateMailCount)
        self.controller.msn.connect('new-mail-notification',
            self.updateMailCount)
        self.controller.msn.connect('mail-movement-notification',
            self.updateMailCount)

        self.statusButton.connect('button-press-event', self.pop_up_status_menu)

        self.hbox = gtk.HBox()
        self.pack_start(self.imageEventBox, False, False)

        self.vbox1 = gtk.VBox()
        self.vbox2 = gtk.VBox(True)
        self.hbox1 = gtk.HBox()
        self.hbox2 = gtk.HBox()

        self.hbox1.pack_start(self.tNick, True, True)
        self.hbox1.pack_start(self.bNick, True, True)

        self.hbox2.pack_start(self.tPersonalMessage, True, True)
        self.hbox2.pack_start(self.bPersonalMessage, True, True)
        self.hbox2.pack_start(self.bMedia, True, True)

        self.vbox2h1 = gtk.HBox()
        self.vbox2h1.pack_end(self.mailButton, True, False)
        self.vbox2h1aligned = gtk.Alignment(1, 0, 0, 0)
        self.vbox2h1aligned.add(self.vbox2h1)

        self.vbox2h2 = gtk.HBox()
        self.vbox2h2.pack_start(self.mediaButton, True, False)
        self.vbox2h2.pack_end(self.statusButton, True, False)
        self.vbox2h2aligned = gtk.Alignment(1, 0, 0, 0)
        self.vbox2h2aligned.add(self.vbox2h2)
        
        self.vbox2.pack_start(self.vbox2h1aligned, True, False)
        self.vbox2.pack_start(self.vbox2h2aligned, True, False)

        self.vbox1.pack_start(self.hbox1, True, False, 1)
        self.vbox1.pack_start(self.hbox2, True, False, 1)

        self.hbox.pack_start(self.vbox1, True, True)
        self.hbox.pack_start(self.vbox2, False, False)
        self.pack_start(self.hbox)

        self.show_all()

        # if in the config is active we activate it emitting the toggled signal
        if controller.config.user['mediaEnabled']:
            self.mediaButton.set_active(True)

        self.mediaButton.hide()

        try:
            if not DOMAIN_REGEXP.match(self.controller.userEmail.split("@")[1]):
                self.mailButton.hide()
        except Exception, e:
            print "error! " + str(e)
        
        self.personalMessageChanged(None, None, self.controller.contacts.get_message())

    def isEditing(self):
        if self.tNick.get_property('has-focus') or \
            self.tPersonalMessage.get_property('has-focus'):
            return True
        return False

    def stopEditing(self):
        if self.tNick.get_property('has-focus'):
            self.tNick.emit('focus-out-event', None)
        if self.tPersonalMessage.get_property('has-focus'):
            self.tPersonalMessage.emit('focus-out-event', None)

    def onMediaClicked(self, *args):
        self.controller.pluginManager.getPlugin('CurrentSong').configure()

    def avatarClicked(self, widget, event):
        self.controller.set_picture_dialog()

    def updateMailCount(self, *args):
        self.mailButton.setText('('+str(self.controller.getUnreadMails()) +')')

    def selfNickChanged(self, msnp, oldNick, nick):
        '''method called when the user change his nick in other part'''
        self.tNick.set_text(nick.replace('\n', ' '))
        parser = self.controller.unifiedParser.getParser(nick, \
             PangoDataType)
        nick = parser.get(self.hasSmilies, self.smileysCache)
        self.lNick.set_markup(nick)
        self.nickRefresh()

    def on_nick_activate(self, *args):
        self.controller.contacts.set_nick(self.tNick.get_text())

    def on_nick_changed(self, entry, event, update):
        if update:
            self.controller.contacts.set_nick(self.tNick.get_text())

        self.tNick.hide()
        self.bNick.show()
        self.lNick.show()

    def on_nick_clicked(self, *args):
        self.tNick.show()
        self.bNick.hide()
        self.lNick.hide()
        self.tNick.grab_focus()

    def nickRefresh(self):
        self.on_nick_changed(None, None, False)
        self.bNick.grab_focus()
        
    def nick_parse_hack(self):
        ''' me exists because until nickname is get from server, it
            mightn't be parsed, or if it's equal to local nick, it 
            won't be parsed at all. i live for the plusplus plugin only
                                                        XOXO PlusPlus Girl'''
        self.selfNickChanged(None, None, self.tNick.get_text())
        self.personalMessageChanged(None, None, self.tPersonalMessage.get_text())

    def on_pm_changed(self, entry, event, update) :
        if update:
            self.controller.contacts.set_message(self.tPersonalMessage.get_text())

        self.bMedia.hide()
        self.lMedia.hide()
        self.tPersonalMessage.hide()
        self.bPersonalMessage.show()
        self.lPersonalMessage.show()

    def on_pm_clicked(self, *args):
        self.bMedia.hide()
        self.lMedia.hide()
        self.tPersonalMessage.show()
        self.bPersonalMessage.hide()
        self.lPersonalMessage.hide()
        self.tPersonalMessage.grab_focus()

    def personalMessageRefresh(self):
        self.controller.contacts.set_message(\
            self.tPersonalMessage.get_text())

        if not self.mediaButton.get_active():
            self.bMedia.hide()
            self.lMedia.hide()
            self.tPersonalMessage.hide()
            self.bPersonalMessage.show()
            self.lPersonalMessage.show()
            self.bPersonalMessage.grab_focus()

    def personalMessageChanged(self, msnp, user, pm):
        '''method called when the pm is changed in other place'''
        self.tPersonalMessage.set_text(pm.replace('\n', ' '))
        if pm == '':
            self.lPersonalMessage.set_text('<i>&lt;' + _('Click here to set your personal message') + '&gt;</i>')
        else:
            parser = self.controller.unifiedParser.getParser(pm, PangoDataType)
            pm = parser.get(self.hasSmilies, self.smileysCache)
            self.lPersonalMessage.set_markup(pm)

    def currentMediaChanged(self, msnp, user, cm, dict):
        '''method called when the current media is changed in other place'''

        if cm != '':
            cm = cm[cm.find('\\0Music\\01\\0')+12:]
            cmargs = cm.split('\\0')
            cm = cmargs[0]
            for args in range(1, len(cmargs)):
                cm = cm.replace('{%s}' %str(args-1), cmargs[args])

            self.lMedia.set_text('♫ ' + cm)
        else:
            self.lMedia.set_text(_("No media playing"))

    def on_personal_activate(self, *args):
        self.controller.contacts.set_message(\
            self.tPersonalMessage.get_text())

    def nickChanged(self, nick):
        self.tNick.set_text(nick.replace('\n', ' '))
        
    def setAvatar(self, pixbuf):
        if pixbuf:
            self.image.set_from_pixbuf(pixbuf)

    def onToggleMedia(self, widget, *args):
        if widget.get_active():
            self.bPersonalMessage.hide()
            self.lPersonalMessage.hide()
            self.tPersonalMessage.hide()
            self.bMedia.show()
            self.lMedia.show()
            self.config.user['mediaEnabled'] = True
        else:
            self.bMedia.hide()
            self.lMedia.show()
            self.tPersonalMessage.hide()
            self.bPersonalMessage.show()
            self.lPersonalMessage.show()

            self.config.user['mediaEnabled'] = False
            self.controller.msn.changeCurrentMedia('')

    def onMaiButtonClicked(self, *args):
        if self.config.glob['overrideMail'] == '':
            try:
                desktop.open(self.controller.hotmail.getLoginPage())
            except OSError:
                dialog.error(_('Couldn\'t launch the default browser'))
        else:
            try:
                subprocess.Popen(self.config.glob['overrideMail'])
            except:
                dialog.error(_('Couldn\'t launch the e-mail client'))

    def pop_up_status_menu(self, widget, event):
        self.statusMenu.show_all()
        self.statusMenu.popup(None, None, None, event.button, event.time)

    def update_status_icon(self, msnp, status):
        self.statusButton.setIcon(self.theme.statusToPixbuf(status))

    def hide_status_icon(self):
        self.statusButton.hide()

    def show_status_icon(self):
        self.statusButton.show()

class BaseImageButton:
    def __init__(self, icon, string=None):
        self.icon = icon
        self.image = gtk.Image()
        hbox = gtk.HBox()
        self.setIcon(icon)
        hbox.pack_start(self.image, True, True, 3)

        if string:
            self.label = gtk.Label(string)
            hbox.pack_start(self.label, False, False, 3)

        self.add(hbox)

    def setText(self, string):
        self.label.set_text(string)

    def getText(self):
        return self.label.get_text()

    def setIcon(self, icon):
        if type(icon) == gtk.gdk.PixbufAnimation:
            self.image.set_from_pixbuf(self.scaleImage(icon.get_static_image()))
        elif type(icon) == gtk.gdk.Pixbuf:
            self.image.set_from_pixbuf(self.scaleImage(icon))
        else:
            self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE ,gtk.ICON_SIZE_SMALL_TOOLBAR)

    def getIcon(self):
        return self.icon

    def scaleImage(self, image):
        h,w = image.get_height(), image.get_width()
        width_max, height_max = 18, 16
        width=float(image.get_width())
        height=float(image.get_height())
        if (width/width_max) > (height/height_max):
            height=int((height/width)*width_max)
            width=width_max
        else:
            width=int((width/height)*height_max)
            height=height_max

        image = image.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        gc.collect() # Tell Python to clean up the memory
        return image

class ImageButton(gtk.Button, BaseImageButton):
    def __init__(self, icon, string=None):
        gtk.Button.__init__(self)
        BaseImageButton.__init__(self, icon, string)

class ImageToggleButton(gtk.ToggleButton, BaseImageButton):
   def __init__(self, icon, string=None):
        gtk.ToggleButton.__init__(self)
        BaseImageButton.__init__(self, icon, string)

# the __main__ code went obsolete
