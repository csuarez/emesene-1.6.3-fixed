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
import time
import gobject
import pango
import os

import Plugin
import dialog
import desktop

import paths
from emesenelib.common import escape
from emesenelib.common import unescape
from Theme import resizePixbuf

growFactor = 20 # the number of pixels to grow every iteration

# This code is used only on Windows to get the location on the taskbar
taskbarOffsety = 0
taskbarOffsetx = 0
if os.name == "nt":
    import ctypes
    from ctypes.wintypes import RECT, DWORD
    user = ctypes.windll.user32
    MONITORINFOF_PRIMARY = 1
    HMONITOR = 1

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', DWORD),
            ('rcMonitor', RECT),
            ('rcWork', RECT),
            ('dwFlags', DWORD)
            ]

    taskbarSide = "bottom"
    taskbarOffset = 30
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(info)
    info.dwFlags =  MONITORINFOF_PRIMARY
    user.GetMonitorInfoW(HMONITOR, ctypes.byref(info))
    if info.rcMonitor.bottom != info.rcWork.bottom:
        taskbarOffsety = info.rcMonitor.bottom - info.rcWork.bottom
    if info.rcMonitor.top != info.rcWork.top:
        taskbarSide = "top"
        taskbarOffsety = info.rcWork.top - info.rcMonitor.top
    if info.rcMonitor.left != info.rcWork.left:
        taskbarSide = "left"
        taskbarOffsetx = info.rcWork.left - info.rcMonitor.left
    if info.rcMonitor.right != info.rcWork.right:
        taskbarSide = "right"
        taskbarOffsetx = info.rcMonitor.right - info.rcWork.right



class PixmapDialog(gtk.Dialog):
    '''a dialog to set Notification Pixmap'''
    def __init__(self, filename, font, color, online, offline, \
                newMsg, typing, newMail, started, idle, position, scroll):

        gtk.Dialog.__init__(self , _('Notification Config'), None, \
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, \
            gtk.STOCK_CANCEL, gtk.RESPONSE_CLOSE))
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)
        self.vbox.set_spacing(4)

        self.filename = filename
        self.fontdesc = font
        self.FColor = color

        self.set_property('can-focus', False)
        self.set_property('accept-focus', False)

        self.hbox = gtk.HBox()
        self.lbox = gtk.HBox()

        self.image = gtk.Image()

        self.sample = gtk.Label()
        self.sample.set_label('<span foreground="%s">%s</span>' % \
            (self.FColor, _('Sample Text')))
        self.sample.set_use_markup(True)

        try:
            self.sample.modify_font(pango.FontDescription(self.fontdesc))
        except:
            print 'Font Error'

        self.fontlabel = gtk.Label(_("Font: "))

        self.fonttype = gtk.ToolButton()
        self.fonttype.set_stock_id(gtk.STOCK_SELECT_FONT)

        self.fontColor = gtk.ToolButton()
        self.fontColor.set_stock_id(gtk.STOCK_SELECT_COLOR)

        self.updateImage()

        self.button = gtk.Button(_('Image'))

        self.hbox.pack_start(self.image)
        self.hbox.pack_start(self.button)

        self.lbox.pack_start(self.fontlabel, False, False, 5)
        self.lbox.pack_start(self.fonttype, False, False)
        self.lbox.pack_start(self.fontColor, False, False)
        self.lbox.pack_start(self.sample, True, True)

        self.vbox.pack_start(self.hbox)
        self.vbox.pack_start(self.lbox)

        self.button.connect('clicked', self.clickPixmap)
        self.fonttype.connect('clicked', self.clickFont)
        self.fontColor.connect('clicked', self.clickColor)

        self.chbuOnline = gtk.CheckButton(_('Notify when someone gets online'))
        self.chbuOnline.set_active(online)
        self.chbuOffline = gtk.CheckButton(_('Notify when someone gets offline'))
        self.chbuOffline.set_active(offline)
        self.chbuNewMail = gtk.CheckButton(_('Notify when receiving an email'))
        self.chbuNewMail.set_active(newMail)
        self.chbuTyping = gtk.CheckButton(_('Notify when someone starts typing'))
        self.chbuTyping.set_active(typing)
        self.chbuNewMsg = gtk.CheckButton(_('Notify when receiving a message'))
        self.chbuNewMsg.set_active(newMsg)
        self.chbuStarted = gtk.CheckButton(_('Don`t notify if conversation is started'))
        self.chbuStarted.set_active(started)
        self.chbuIdle = gtk.CheckButton(_('Disable notifications when busy'))
        self.chbuIdle.set_active(idle)

        self.lblPos = gtk.Label()
        self.lblPos.set_label(_('Position'))
        self.coboPosition = gtk.combo_box_new_text()
        self.coboPosition.append_text(_('Top Left'))
        self.coboPosition.append_text(_('Top Right'))
        self.coboPosition.append_text(_('Bottom Left'))
        self.coboPosition.append_text(_('Bottom Right'))
        self.coboPosition.set_active(position)

        self.pbox = gtk.HBox()
        self.pbox.pack_start(self.lblPos)
        self.pbox.pack_start(self.coboPosition)

        self.lblScr = gtk.Label()
        self.lblScr.set_label(_('Scroll'))
        self.coboScroll = gtk.combo_box_new_text()
        self.coboScroll.append_text(_('Horizontal'))
        self.coboScroll.append_text(_('Vertical'))
        self.coboScroll.set_active(scroll)

        self.sbox = gtk.HBox()
        self.sbox.pack_start(self.lblScr)
        self.sbox.pack_start(self.coboScroll)

        self.vbox.pack_start(self.chbuOnline)
        self.vbox.pack_start(self.chbuOffline)
        self.vbox.pack_start(self.chbuNewMail)
        self.vbox.pack_start(self.chbuTyping)
        self.vbox.pack_start(self.chbuNewMsg)
        self.vbox.pack_start(self.chbuStarted)
        self.vbox.pack_start(self.chbuIdle)
        self.vbox.pack_start(self.pbox)
        self.vbox.pack_start(self.sbox)

        self.show_all()
        
    def updateImage(self):
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.filename)
            pixbuf = resizePixbuf(pixbuf, 128, 200)
            self.image.set_from_pixbuf(pixbuf)
            self.image.show()
        except:
            self.filename = None
            self.image.hide()

    def clickPixmap(self, arg):
        def _on_image_selected(response, path):
            if response == gtk.RESPONSE_ACCEPT:
                self.filename = path
                self.updateImage()

        dialog.ImageChooser(paths.HOME_DIR, _on_image_selected).run()

    def clickFont(self, arg):
        fontDialog = gtk.FontSelectionDialog(_('Choose a font'))
        if self.fontdesc != None:
            fontDialog.set_font_name(self.fontdesc)
        response = fontDialog.run()
        if response == gtk.RESPONSE_OK:
            pangoDesc = pango.FontDescription(fontDialog.get_font_name())
            self.sample.modify_font(pangoDesc)
            self.fontdesc = pangoDesc.to_string()
        fontDialog.destroy()

    def clickColor(self, arg):
        colorDialog = gtk.ColorSelectionDialog(_('Choose a color'))
        colorDialog.colorsel.set_has_palette(True)
        response = colorDialog.run()
        if response == gtk.RESPONSE_OK:
            color = colorDialog.colorsel.get_current_color()
            red = color.red >> 8
            green = color.green >> 8
            blue = color.blue >> 8
            self.FColor = '#%02X%02X%02X' % (red, green, blue)
            self.sample.set_label('<span foreground="%s">%s</span>' % \
                    (self.FColor, _('Sample Text')))
            self.sample.set_use_markup(True)
        colorDialog.destroy()

    def get_config_values(self):
        return [self.filename, self.fontdesc, self.FColor, \
                 int(self.chbuOnline.get_active()), \
                 int(self.chbuOffline.get_active()), \
                 int(self.chbuNewMsg.get_active()), \
                 int(self.chbuTyping.get_active()), \
                 int(self.chbuNewMail.get_active()), \
                 int(self.chbuStarted.get_active()), \
                 int(self.chbuIdle.get_active()), \
                 self.coboPosition.get_active(), \
                 self.coboScroll.get_active()]

class NotificationManager:
    ''' This class manages the creation display and destruction of the notifications. '''

    def __init__(self, defaultHeight = 128, defaultWidth = 200):
        ''' Contructor '''

        self.defaultHeight = defaultHeight
        self.defaultWidth = defaultWidth

        self.offset = 0

        #[[Notification, timestamp], [Notification, timestamp]]
        self.list = []

        self.animate = None

    def newNotification(self, string, pos, scroll, pixmap = None, \
                closePixmap = None, callback = None, params = None, \
                userPixbuf = None, font = None, color = None):
        '''
        create a new notification, pixmap is the background image (as a pixbuf),
        closepixmap is a pixbuf for the close button.
        callback is the method that will be called when the message in the Notification
        is clicked
        '''
        if pixmap != None:
            width, height = pixmap.get_size()
        else:
            width = self.defaultWidth
            height = self.defaultHeight

        rgb = gtk.gdk.screen_get_default().get_rgb_colormap()
        gtk.widget_push_colormap(rgb)
        g = Notification(pos, scroll, self.offset, string, height, width, \
                pixmap, closePixmap, callback, params, userPixbuf, font, color)
        g.show()
                
        gtk.widget_pop_colormap()

        self.offset = g.getOffset()

        self.list.append([g, int(time.time())])

        if len(self.list) <= 1:
            self.animate = gobject.timeout_add(100, self.refresh)

    def refresh(self):
        '''
        check which notifications should be closed
        resize and move notifications
        '''

        self.offset = 0

        if self.list == []:
            return False
        else:
            timestamp = int(time.time())
            count = 0
            for i in self.list:

                if not i[0].get_property('visible'):
                    del self.list[count]
                elif i[1] + 7 <= timestamp:
                    i[0].hide()
                    del self.list[count]
                else:
                    self.list[count][0].grow(self.offset)
                    self.offset = self.list[count][0].getOffset()

                count += 1

            return True

    def closeAll(self):
        ''' close all the notifications '''

        if self.animate:
            gobject.source_remove(self.animate)

        for i in range(len(self.list)):
            self.list[i][0].hide()

        self.offset = 0
        self.list = []

class Notification(gtk.Window):
    def __init__(self, corner, scroll, offset, string, height = 128, \
                width = 200, pixmap = None, closePixmap = None, \
                callback = None, params = None, userPixbuf = None, \
                font = None, color = None):

        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)

        if corner == 0:
            self.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        elif corner == 1:
            self.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
        elif corner == 2:
            self.set_gravity(gtk.gdk.GRAVITY_SOUTH_WEST)
        else:
            self.set_gravity(gtk.gdk.GRAVITY_SOUTH_EAST)

        #self.set_accept_focus(False)
        #self.set_decorated(False)
        #self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)

        self.corner = corner
        self.scroll = scroll

        if scroll == 0:
            self.height = height
            self.max = width
            self.width = 1
        else:
            self.width = width
            self.max = height
            self.height = 1

        self.callback = callback

        self.set_geometry_hints(None, min_width=-1, min_height=-1, \
                max_width=width, max_height=height)

        if pixmap != None:
            self.set_app_paintable(True)
            self.realize()
            self.window.set_back_pixmap(pixmap, False)

        messageLabel = gtk.Label('<span foreground="' + color +'">' \
                + escape(str(string)) + '</span>')
        messageLabel.set_use_markup(True)
        messageLabel.set_justify(gtk.JUSTIFY_CENTER)
        messageLabel.set_ellipsize(pango.ELLIPSIZE_END)
        try:
            messageLabel.modify_font(pango.FontDescription(font))
        except e:
            print e

        if closePixmap == None:
            close = gtk.Label()
            close.set_label("<span background=\"#cc0000\" foreground=" \
                    + color + "\"> X </span>")
            close.set_use_markup(True)
        else:
            close = gtk.Image()
            close.set_from_pixbuf(closePixmap)

        closeEventBox = gtk.EventBox()
        closeEventBox.set_visible_window(False)
        closeEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        closeEventBox.connect("button_press_event", self.close)        
        closeEventBox.add(close)

        hbox = gtk.HBox()
        vbox = gtk.VBox()
        lbox = gtk.HBox()
        title = gtk.Label("")
        title.set_use_markup(True)

        avatarImage = gtk.Image()
        if userPixbuf != None:
            userPixbuf = resizePixbuf(userPixbuf, 48, 48)
            avatarImage.set_from_pixbuf(userPixbuf)

        lboxEventBox = gtk.EventBox()
        lboxEventBox.set_visible_window(False)
        lboxEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        lboxEventBox.connect("button_press_event", self.onClick, params)
        lboxEventBox.add(lbox)
        
        self.connect("button_press_event", self.onClick, params)

        hbox.pack_start(title, True, True)
        hbox.pack_end(closeEventBox, False, False)
        lbox.pack_start(avatarImage, False, False, 10)
        lbox.pack_start(messageLabel, True, True, 5)

        vbox.pack_start(hbox, False, False)
        vbox.pack_start(lboxEventBox, True, True)

        self.grow(offset, False)
        self.add(vbox)

        vbox.show_all()

    def onClick(self, widget, event, params):
        if event.button == 1 and self.callback != None:
            self.callback(params)
        self.close()

    def _resize(self):
        ''' change the size and position '''

        if self.offset == 0:
            sumx = taskbarOffsetx
            sumy = taskbarOffsety
        else:
            sumx = 0
            sumy = 0
        if self.scroll == 0:
            if self.corner == 0 or self.corner == 2:
                l = self.offset + sumx
            else:
                l = gtk.gdk.screen_width() - self.offset - self.width - sumx

            if self.corner == 0 or self.corner == 1:
                t = 0 + taskbarOffsety
            else:
                t = gtk.gdk.screen_height() - self.height - taskbarOffsety
        else:
            if self.corner == 0 or self.corner == 2:
                l = 0 + taskbarOffsetx
            else:
                l = gtk.gdk.screen_width() - self.width - taskbarOffsetx

            if self.corner == 0 or self.corner == 1:
                t = self.offset + sumy
            else:
                t = gtk.gdk.screen_height() - self.offset - self.height - sumy

        self.move(l, t)
        self.resize(self.width, self.height)

    def show(self):
        ''' show it '''
        self.show_all()

    def close(self , *args):
        ''' hide the Notification '''
        self.hide()

    def grow(self, offset, animate=True):
        ''' increase the size of the notification and position '''

        if animate and offset < self.offset:
            self.offset -= growFactor
            if offset < self.offset:
                self.offset = offset
        else:
            self.offset = offset

        if self.scroll == 0:
            if self.width < self.max:
                if self.width > self.max:
                    self.width = self.max
                else:
                    self.width += growFactor
        else:
            if self.height < self.max:
                if self.height + growFactor > self.max:
                    self.height = self.max
                else:
                    self.height += growFactor

        self._resize()

    def getOffset(self):
        ''' returns next notifications offset '''

        if self.scroll == 0: 
            if self.corner == 0 or self.corner == 2:
                return self.get_position()[0] + self.width
            else:
                return gtk.gdk.screen_width() - self.get_position()[0]
        else:
            if self.corner == 0 or self.corner == 1:
                return self.get_position()[1] + self.height
            else:
                return gtk.gdk.screen_height() - self.get_position()[1]

class MainClass(Plugin.Plugin):
    ''' The notification plugin '''
    description = _('Notifies various events with Messenger-like small windows')
    authors = { 'Mariano Guerra' : 'luismarianoguerra at gmail dot com' }
    website = 'http://emesene-msn.blogspot.com'
    displayName = _('OldNotifications')
    name = 'OldNotification'

    def __init__(self, controller, msn):
        ''' Constructor '''

        Plugin.Plugin.__init__(self, controller, msn, 1000)
        self.theme = controller.theme

        self.config = controller.config

        self.description = _('Notifies various events with Messenger-like small windows')
        self.authors = { 'Mariano Guerra' : 'luismarianoguerra at gmail dot com' }
        self.website = 'http://emesene-msn.blogspot.com'
        self.displayName = _('OldNotifications')
        self.name = 'OldNotifications'

        self.config.readPluginConfig(self.name)
        self.controller = controller

        self.filename = self.config.getPluginValue(self.name, 'filename',
            paths.DEFAULT_THEME_PATH + 'guif.png')
        self.fontname  = self.config.getPluginValue(self.name, 'fontname',
            'Sans')
        self.fontcolor = self.config.getPluginValue(self.name, 'fontcolor',
            '#000000')

        self.notifyOnline  = int(self.config.getPluginValue(self.name, 'online', '1'))
        self.notifyOffline = int(self.config.getPluginValue(self.name, 'offline', '1'))
        self.notifyNewMail = int(self.config.getPluginValue(self.name, 'newMail', '1'))
        self.notifyNewMsg = int(self.config.getPluginValue(self.name, 'newMsg', '1'))
        self.notifyTyping = int(self.config.getPluginValue(self.name, 'typing', '0'))
        self.notifyStarted = int(self.config.getPluginValue(self.name, 'started', '0'))
        self.notifyIdle = int(self.config.getPluginValue(self.name, 'idle', '1'))
        self.position = int(self.config.getPluginValue(self.name, 'position', '3'))
        self.scroll = int(self.config.getPluginValue(self.name, 'scroll', '1'))

        self.onlineId = None
        self.offlineId = None
        self.newMsgId = None
        self.offMsgId = None
        self.typingId = None
        self.newMailId = None
        self.initMailId = None

    def notifyEnabled(self, contact = None):
        '''checks if notifications are enabled'''

        if self.notifyIdle and self.msn.status == 'BSY':
            return False
        if contact != None:
            if self.controller.contacts.get_blocked(contact):
                return False
        return True

    def online(self, msnp, email, oldStatus):
        ''' called when someone get online '''

        if not (self.notifyOnline and self.notifyEnabled(email)):
            return

        if oldStatus != 'FLN':
            return

        nick = unescape(self.controller.unifiedParser.getParser\
                (self.msn.getUserDisplayName(email)).get())
        contact = self.msn.contactManager.getContact(email)
        userPixbuf = self.theme.getUserDisplayPicture(contact)

        self.notificationManager.newNotification(unicode(nick)[:20] \
                + "\n" + _("is online"), self.position, self.scroll, \
                self.pixmap, self.close, self.startConversation, \
                (email, None), userPixbuf, self.fontname, self.fontcolor)

    def offline(self, msnp, email):
        ''' called when someone get offline '''

        if not (self.notifyOffline and self.notifyEnabled(email)):
            return

        nick = unescape(self.controller.unifiedParser.getParser\
                (self.msn.getUserDisplayName(email)).get())
        contact = self.msn.contactManager.getContact(email)
        userPixbuf = self.theme.getUserDisplayPicture(contact)

        self.notificationManager.newNotification(unicode(nick)[:20] \
                + "\n" + _("is offline"), self.position, self.scroll, \
                self.pixmap, self.close, None, None, userPixbuf, \
                self.fontname, self.fontcolor)

    def newMsg(self, msnp, email):
        '''called when someone send a message'''

        if not (self.notifyNewMsg and self.notifyEnabled(email)):
            return

        result = self.controller.conversationManager.getOpenConversation(email)
        if result != None:
            if self.notifyStarted:
                return
            window, conversation = result
            windowFocus = window.is_active()
            tabFocus = (window.conversation == conversation)
            if windowFocus and tabFocus:
                return

        nick = unescape(self.controller.unifiedParser.getParser\
                (self.msn.getUserDisplayName(email)).get())
        contact = self.msn.contactManager.getContact(email)
        userPixbuf = self.theme.getUserDisplayPicture(contact)

        self.notificationManager.newNotification(unicode(nick)[:20] \
                + "\n" + _('has send a message'), self.position, self.scroll, \
                self.pixmap, self.close, self.startConversation, \
                (email, None), userPixbuf, self.fontname, self.fontcolor)

    def offMsg(self, msnp, oim):
        '''called when someone send an offline message'''
        email = oim[0]['addr']

        if not (self.notifyNewMsg and self.notifyEnabled(email)):
            return

        result = self.controller.conversationManager.getOpenConversation(email)
        if result != None:
            window, conversation = result
            windowFocus = window.is_active()
            tabFocus = (window.conversation == conversation)
            if windowFocus and tabFocus:
                return

        nick = unescape(self.controller.unifiedParser.getParser\
                (self.msn.getUserDisplayName(email)).get())
        contact = self.msn.contactManager.getContact(email)
        userPixbuf = self.theme.getUserDisplayPicture(contact)

        self.notificationManager.newNotification(unicode(nick)[:20] \
                + "\n" + _('sent an offline message'), self.position, \
                self.scroll, self.pixmap, self.close, self.startConversation, \
                (email, None), userPixbuf, self.fontname, self.fontcolor)

    def receiveTyping(self, msn, switchboard, signal, args):
        '''called when someone starts typing'''
        email = args[0]

        if not (self.notifyTyping and self.notifyEnabled(email)):
            return

        if self.controller.conversationManager.getOpenConversation\
                (email, switchboard) != None:
            return

        nick = unescape(self.controller.unifiedParser.getParser\
                (self.msn.getUserDisplayName(email)).get())
        contact = self.msn.contactManager.getContact(email)
        userPixbuf = self.theme.getUserDisplayPicture(contact)

        self.notificationManager.newNotification(unicode(nick)[:20] \
                + "\n" + _('starts typing...'), self.position, self.scroll, \
                self.pixmap, self.close, self.startConversation, \
                (email, switchboard), userPixbuf, self.fontname, self.fontcolor)

    def newMail(self, msnp, From, FromAddr, Subject, MessageURL, PostURL, id):
        ''' called when receiving mail '''

        if not (self.notifyNewMail and self.notifyEnabled(FromAddr)):
            return

        contact = self.msn.contactManager.getContact(FromAddr)
        if contact == None:
            text = _('From: ') + From +' &lt;' + FromAddr + '&gt;'
            userPixbuf = None
        else:
            text = _('From: ') + unescape(self.controller.unifiedParser.\
                getParser(self.msn.getUserDisplayName(FromAddr)).get())
            userPixbuf = self.theme.getUserDisplayPicture(contact)

        text += '\n' + _('Subj: ') + escape(Subject)

        self.notificationManager.newNotification(_('New email') \
                + "\n" + text, self.position, self.scroll, self.pixmap, \
                self.close, self.openMail, (MessageURL, PostURL, id), \
                userPixbuf, self.fontname, self.fontcolor)

    def initMail(self, msnp):
        ''' called when receiving initial mail count '''

        if self.notifyNewMail:
            unread = self.controller.getUnreadMails()
            if unread > 0:
                if unread == 1:
                    s = ''
                else:
                    s = 's'
                params = {'num': unread, 's': s}
                self.notificationManager.newNotification(
                        _('You have %(num)i unread message%(s)s') % params, \
                        self.position, self.scroll, self.pixmap, self.close, \
                        self.openMail, (None, None, '2'), None, \
                        self.fontname, self.fontcolor)

    def startConversation(self, params):
        self.controller.newConversation(None, params[0], params[1], True)

    def openMail(self, params):
        if self.config.glob['overrideMail'] == '':
            try:
                desktop.open(self.controller.hotmail.getLoginPage\
                    (params[0], params[1], params[2]))
            except OSError:
                dialog.error(_('Couldn\'t launch the default browser'))
        else:
            try:
                subprocess.Popen(self.config.glob['overrideMail'])
            except:
                dialog.error(_('Couldn\'t launch the e-mail client'))

    def connect_onoff(self, *args):
        self.onlineId = self.connect('user-online', self.online)
        self.offlineId = self.connect('user-offline', self.offline)
        if self.notifyId is not None: self.disconnect(self.notifyId)
        self.notifyId = None

    def start(self):
        ''' start the plugin '''

        self.notificationManager = NotificationManager(128, 200)
        self.notifyId = None
        self.onlineId = None
        self.offlineId = None
        if self.msn.canNotify:
            self.connect_onoff()
        else:
            self.notifyId = self.connect('enable-notifications', self.connect_onoff)
        self.newMsgId = self.connect('message-received', self.newMsg)
        self.offMsgId = self.connect('offline-message-received', self.offMsg)
        self.typingId = self.connect('switchboard::typing', self.receiveTyping)
        self.newMailId = self.connect('new-mail-notification', self.newMail)
        self.initMailId = self.connect\
                ('initial-mail-notification', self.initMail)

        try:
            self.pixmap, mask = gtk.gdk.pixbuf_new_from_file\
                    (self.filename).render_pixmap_and_mask()
        except:
            self.pixmap = None

        try:
            self.close = self.theme.getImage('close')
        except:
            self.close = None

        self.enabled = True

    def stop(self):    
        ''' stop the plugin '''

        if self.onlineId is not None: self.disconnect(self.onlineId)
        if self.offlineId is not None: self.disconnect(self.offlineId)
        if self.notifyId is not None: self.disconnect(self.notifyId)
        self.disconnect(self.newMsgId)
        self.disconnect(self.offMsgId)
        self.disconnect(self.typingId)
        self.disconnect(self.newMailId)
        self.disconnect(self.initMailId)
        self.enabled = False
        self.notificationManager.closeAll()

    def check(self):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> (True , 'some message')
        else -> (False , 'error message')
        '''

        return (True, 'Ok')

    def configure(self):
        dialog = PixmapDialog(self.filename, \
                self.fontname, self.fontcolor, self.notifyOnline, \
                self.notifyOffline, self.notifyNewMsg, self.notifyTyping, \
                self.notifyNewMail, self.notifyStarted, self.notifyIdle, \
                self.position, self.scroll)

        response = dialog.run()
        
        if response == gtk.RESPONSE_ACCEPT:
            values = dialog.get_config_values()
            self.filename = values[0]
            self.fontname = values[1]
            self.fontcolor = values[2]
            self.notifyOnline = values[3]
            self.notifyOffline = values[4]
            self.notifyNewMsg = values[5]
            self.notifyTyping = values[6]
            self.notifyNewMail = values[7]
            self.notifyStarted = values[8]
            self.notifyIdle = values[9]
            self.position = values[10]
            self.scroll = values[11]
            self.config.setPluginValue(self.name, 'filename', self.filename)
            self.config.setPluginValue(self.name, 'fontname', self.fontname)
            self.config.setPluginValue(self.name, 'fontcolor', self.fontcolor)
            self.config.setPluginValue(self.name, 'online', self.notifyOnline)
            self.config.setPluginValue(self.name, 'offline', self.notifyOffline)
            self.config.setPluginValue(self.name, 'newMsg', self.notifyNewMsg)
            self.config.setPluginValue(self.name, 'typing', self.notifyTyping)
            self.config.setPluginValue(self.name, 'newMail', self.notifyNewMail)
            self.config.setPluginValue(self.name, 'started', self.notifyStarted)
            self.config.setPluginValue(self.name, 'idle', self.notifyIdle)
            self.config.setPluginValue(self.name, 'position', self.position)
            self.config.setPluginValue(self.name, 'scroll', self.scroll)

            try:
                self.pixmap, mask = gtk.gdk.pixbuf_new_from_file\
                        (self.filename).render_pixmap_and_mask()
            except:
                self.pixmap = None
        dialog.destroy()
        return True
