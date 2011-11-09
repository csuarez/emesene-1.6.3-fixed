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
import pango
import shutil
import gobject
import FilterEntry

# for drag and drop
import os
import urllib
import re
# for webcam errors
import dialog

import UserList
import SmilieWindow
import FontStyleWindow
import FileTransferUI
from Theme import resizePixbuf
from Parser import PangoDataType
from Parser import UserListDataType
from SmileyRenderer import SmileyLabel

import emesenelib.ContactData

import Widgets

from htmltextview import HtmlTextView

class OurStatusBar(gtk.Statusbar):
    def __init__(self, ui):    
        gtk.Statusbar.__init__(self)
        self.ui = ui
        self.genericID = 1
        self.message_id = None
    def set_text(self, text):
        if self.message_id is not None:
            self.pop(self.genericID)
            self.message_id = None
        if text != "":
            self.message_id = self.push(self.genericID, text)

class ConversationUI(gtk.VBox):
    '''this class represent all the widgets that are inside a tab
    also hold the tab widget because there is no better place than
    this to hold it...'''

    def __init__(self, controller, parentConversation):
        gtk.VBox.__init__(self, spacing=3)
        self.set_border_width(0)

        self.parentConversation = parentConversation
        self.controller = controller
        self.config = self.controller.config
        self.parser = controller.unifiedParser
        self.offlineBarIsShowed = False

        # the header that contains the nick, the PM, status etc
        self.header = Header(self, controller)
        # the widget that contains the tabs and the conversations
        self.tabWidget = TabWidget(self, controller)
        self.tabWidget.show()
        # where do you want to put the avatars? l/r
        avatarRight = self.config.user['avatarsOnRight']
        # the input widget (includes the toolbar and avatar)
        self.input = InputWidget(self, controller, \
            parentConversation.isCurrent, avatarRight)
        self.input.show()
        # the status bar
        self.status = OurStatusBar(self)

        # the list of users when we are on a group chat
        self.listOfUsers = UserList.UserList(self.controller, \
            self.controller.theme, self.config, False)

        # the scroll for the list of users
        self.scrollList = gtk.ScrolledWindow()
        self.scrollList.set_shadow_type(gtk.SHADOW_IN)
        self.scrollList.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrollList.add(self.listOfUsers)

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_shadow_type(gtk.SHADOW_IN)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        # the widget where the conversation is shown
        self.textview = HtmlTextView(controller, \
            self.parentConversation.textBuffer, self.scroll)
        self.textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.textview.set_left_margin(6)
        self.textview.set_right_margin(6)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.connect('key-press-event', self.onTextviewKeyPress)

        # nice status bar for the scroll area
        # TODO: move this to a new class so we can benefit in 1.5+
        self.eventBox = gtk.EventBox()
        box = gtk.HBox(False, 0)
        self.eventBox.set_size_request(0, 30)
        self.eventBox.add(box)
        self.eventBox.modify_bg(gtk.STATE_NORMAL, self.controller.tooltipColor)
        self.eventBox.connect("button-press-event", self.hideEventBox)
        self.label = gtk.Label(_("Connecting..."))
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        image = gtk.Image()
        image.set_from_stock (gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_LARGE_TOOLBAR)
        box.pack_start(image, False, False, 5)
        box.pack_start(self.label, True, True, 5)
        self.hiddenByUser = False #user can "close" the event box by clicking the bar
                                  #this should prevent the bar from reappearing everytime
                                  #that the window is redraw

        # pack the scroll with the status bar
        self.mainBox = gtk.VBox(False, 0)
        self.mainBox.pack_end(self.scroll, True, True, 0)
        self.mainBox.pack_start(self.eventBox, False, False, 0)
        self.mainBox.show_all()   

        self.scroll.add(self.textview)
        self.scroll.show_all()

        # pack the output textview with the scrollList to allow resizing
        self.mainPaned = gtk.HPaned()
        if avatarRight:
            self.mainPaned.pack1(self.mainBox, True, False)
            self.mainPaned.pack2(self.scrollList, False, True)
        else:
            self.mainPaned.pack1(self.scrollList, False, True)
            self.mainPaned.pack2(self.mainBox, True, False)
        self.mainPaned.connect('button-release-event', self.onListResizeCompleted)
        self.mainPaned.show()

        # Friends avatar
        self.remoteAvatar = AvatarHBox(self, controller,
            self.parentConversation.switchboard.firstUser)
        self.remoteAvatar.show()

        # main hbox with output textview, userlist and remote avatar
        self.hbox = gtk.HBox(spacing=2)
        self.hbox.set_border_width(2)
        if avatarRight:
            self.hbox.pack_start(self.mainPaned, True, True)
            self.hbox.pack_start(self.remoteAvatar, False, False, padding = 1)
        else:
            self.hbox.pack_start(self.remoteAvatar, False, False, padding = 1)
            self.hbox.pack_start(self.mainPaned, True, True)
        self.hbox.set_size_request(-1,40)
        self.hbox.show()

        # the vertical panel that divides the textview and the input
        # (toolbar and input)
        vpaned = gtk.VPaned()
        vpaned.pack1(self.hbox, True, False)
        vpaned.pack2(self.input, False, True)
        # connect the notify signal to catch dragging of the seperator, as
        # suggested in http://faq.pygtk.org/index.py?req=show&file=faq19.013.htp
        vpaned.connect('notify', self.onInputResize)
        vpaned.connect('button-release-event', self.onInputResizeCompleted)
        vpaned.show()

        self.transfers = FileTransferUI.FtBarWidget(self.controller, self,
                                        parentConversation)
        self.transfers.set_no_show_all(True)

        self.pack_start(self.header, False, False)
        self.pack_start(vpaned, True, True)
        self.pack_start(self.transfers, False, False)
        self.pack_start(self.status, False, False)

        self.messageWaiting = {}
        self.contactTyping = {}

        self.typingTimeoutID = 0
        self.closed = False

        self.last_mark = None
        self.lastTimestamp = 0

        self.show()
        self.update()

    def onInputResize(self, pane, gparamspec, *args):
        # If the position of the seperator changed, scroll to bottom
        if gparamspec.name == 'position':
            self.scrollToBottom(force=True)

    def onInputResizeCompleted(self, widget, event, *args):
        # save the height of the input box to config
        alloc = self.input.get_allocation()
        self.config.user['convInputHeight'] = alloc.height

    def onListResizeCompleted(self, widget, event, *args):
        # save the width of the userlist to config
        alloc = self.scrollList.get_allocation()
        self.config.user['convListWidth'] = alloc.width

    def onTextviewKeyPress(self, widget, event):
        # don't focus inputbox if Control is pressed (Ctrl-C etc.)
        if event.keyval == gtk.keysyms.Control_L or \
                event.keyval == gtk.keysyms.Control_R or \
                event.state & gtk.gdk.CONTROL_MASK:
            return

        self.input.input.emit('key-press-event', event)
        self.input.grabFocus()

    def hideEventBox(self, widget, event):
        self.hiddenByUser = True
        self.eventBox.hide_all()

    def close(self):
        self.closed = True
        self.remoteAvatar.close()

    def setInputEnabled(self, enable):
        self.input.input.set_sensitive(enable)

    def noneIsTyping(self):
        try:
            for contact in self.email_list:
                if self.contactTyping[contact] == True:
                    return False
            return True
        except:
            return False

    def update(self):
        self.header.update()
        self.tabWidget.update()
        self.input.update()
        self.email_list = [mail.email for mail in self.parentConversation.getMembersDict().values()]

        # add new user in conversation
        for email in self.email_list:
            if email not in self.contactTyping.keys():
                self.contactTyping[email] = False
            if email not in self.messageWaiting.keys():
                self.messageWaiting[email] = False

        for email in self.contactTyping.keys():
            if self.contactTyping[email]:
                self.setTyping(email)
            elif self.messageWaiting[email]:
                self.setMessageWaiting(email)
            else:
                self.setDefault(email)

        isGroupChat = len(self.parentConversation.getMembers()) > 1
        # updates local and remote avatars or contact list
        if isGroupChat:
            members = self.parentConversation.getMembersDict()
            d = {'members' : emesenelib.ContactData.Group(_('Members'))}
            for member in members.values():
                d['members'].setUser(member.email, member)

            self.listOfUsers.fill(d)

        # if you want to show the avatar and hide the grouplist or
        # viceversa first do the hide and then the show, because this methods
        # also hide the container vbox to not let an empty widget there
        if isGroupChat:
            # XXXDX
            self.showUserList()
            self.remoteAvatar.hide()
        elif self.config.user['showAvatars']:
            self.hideUserList()

            # Fix for wrong DP after your contacts leave the 
            # groupchat and you get returned to a single chat
            contactMail = self.parentConversation.getMembers()[0]
            if self.remoteAvatar.mail != contactMail:
                self.remoteAvatar.mail = contactMail
                self.remoteAvatar.updateDPnoCrossfade()

            self.remoteAvatar.show_all()
            self.remoteAvatar.update()
        else:
            self.hideUserList()
            self.remoteAvatar.hide()

        if not self.config.user['showHeader']:
            self.header.hide()
        else:
            self.header.show()

        if not self.config.user['showTabCloseButton']:
            self.tabWidget.closeButton.hide()
        else:
            self.tabWidget.closeButton.show()

        if not self.config.user['showStatusBar']:
            self.status.hide()
        else:
            self.status.show()

        inputHeight = self.config.user['convInputHeight']
        self.input.set_size_request(0, inputHeight)
        
        scrollListWidth = self.config.user['convListWidth']
        self.scrollList.set_size_request(scrollListWidth, 0)

        self.update_eventbox()

	    # Fixes the focus bug in Karmic, i know it's ugly but..
        # http://www.daa.com.au/pipermail/pygtk/2007-December/014660.html
        gobject.timeout_add(0, self.grabInputFocus)        

    def grabInputFocus(self, args=None):
        ''' grabs the focus only if the conversation is "active" '''
        if self.input.get_property('has_focus'): return False
        cw = self.parentConversation.parentConversationWindow
        if not cw: return False
        tabs = cw.tabs
        if tabs.get_current_page() == tabs.page_num(self):
            self.input.grabFocus()
        return False
        
    def update_eventbox(self):
        if self.parentConversation.switchboard.status == 'error' and not self.hiddenByUser:
            self.label.set_text(\
                _("User is offline, messages will be sent as offline messages"))
            self.eventBox.show_all()
        elif self.parentConversation.switchboard.status == 'closed':
            pass
        elif self.parentConversation.switchboard.status != 'established':
            # we should be connecting, we show the stuff only if
            # this connection is way looooooong
            gobject.timeout_add(5000, self.set_label_as_connecting)
        else: # self.parentConversation.switchboard.status == 'established'
            self.hiddenByUser = False
            self.eventBox.hide()
    
    def set_label_as_connecting(self):
        if self.parentConversation.switchboard.status == 'connected':
            self.hiddenByUser = False
            self.label.set_text(_("Connecting..."))
            self.eventBox.show_all()        
        return False

    #method to set a label on the event bar that dissapear after 3 seconds
    #if the closing prevention option is activated
    def set_label_closingPrevention(self, message):
        self.label.set_text(message)
        self.eventBox.show_all()
        preventTime = 0
        if self.config.user['preventClosingTime']:
            preventTime = 3000
        gobject.timeout_add(preventTime, self.update_eventbox)

    def scrollToBottom(self, force=False):
        '''scroll to the end of the conversation'''
        self.textview.scrollToBottom(force)

    def showUserList(self):
        self.scrollList.show_all()
        self.listOfUsers.show()

    def hideUserList(self):
        self.scrollList.hide()
        self.listOfUsers.hide()

    def rebuildStatusText(self):
        '''Builds the text displayed in the statusbar, based in
        self.contactTyping. The "output" is a comma separated list
        of (full) mails and "is/are typing a message..." '''

        mails = [x for x in self.contactTyping.keys() \
                  if self.contactTyping[x] == True]

        string = ''

        if len(mails) > 0:
            comma = ', ' # TODO: gettext?
            for mail in mails:
                if self.config.user['showMailTyping']:
                    string += str(mail)
                else:
                    contact = self.controller.getContact(mail)
                    if contact:
                        parts = self.parser.getParser(contact.nick).get(escaped=False)
                        for part in parts:
                            string += str(part)
                    else:
                        string += str(mail)
                string += comma

            # yes, i know we don't need to deal with utf-8 here, but...
            string = str(unicode(string)[:-len(comma)])

            if len(mails) == 1:
                string += ' ' + _('is typing a message...')
            else:
                string += ' ' + _('are typing a message...')

            try:
                self.status.set_text(string)
            except: # and this is a hack because now we kill conversation.ui
                pass# and sometimes this gets called somehow random.
            
    def setMessageWaiting(self, mail):
        if self.parentConversation.isCurrent:
            self.tabWidget.hasMessageWaiting = True
            #self.tabWidget.setDefault()
            return self.setDefault(mail)

        self.tabWidget.setMessageWaiting()
        self.header.setDefault()
        if mail:
            self.contactTyping[mail] = False
            self.messageWaiting[mail] = True
            self.rebuildStatusText()

    def setTyping(self, mail):
        if self.messageWaiting.has_key(mail) and self.messageWaiting[mail]: return
        self.header.setTyping()
        self.tabWidget.setTyping()

        self.contactTyping[mail] = True
        self.rebuildStatusText()

        if self.typingTimeoutID > 0:
            gobject.source_remove(self.typingTimeoutID)

        self.typingTimeoutID = gobject.timeout_add(8000, \
            self.clearTyping, mail)

    def clearTyping(self, mail):
        if mail in self.messageWaiting and self.messageWaiting[mail]:
            self.setMessageWaiting(mail)
        else:
            self.setDefault(mail)
        self.contactTyping[mail] = False

        self.typingTimeoutID = 0
        if self.config.user['showLastMessageReceivedAt']:
            self.setTimestampStatusText()
        else: # clean "user is typing" stuff, if timestamp isn't wanted
            try: 
                self.status.set_text("")
            except:
                pass        
        return False

    def lastMessageReceivedAt(self):
        self.lastTimestamp = time.strftime('%X', time.localtime())
        if self.config.user['showLastMessageReceivedAt']:
            self.setTimestampStatusText()
        else:# clean "user is typing" stuff, if timestamp isn't wanted
            try: 
                self.status.set_text("")
            except:
                pass

    def setTimestampStatusText(self):
        # see other occurence of this in this code, it's hacky
        if self.lastTimestamp == 0: return
        string = (_('Last message received at: %s') % self.lastTimestamp)
        try:
            self.status.set_text(string)
        except: # and this is a hack because now we kill conversation.ui
            pass# and sometimes this gets called somehow random.

    def setDefault(self, mail):
        self.tabWidget.setDefault()
        self.header.setDefault()
        if mail:
            self.contactTyping[mail] = False
            self.messageWaiting[mail] = False
            self.rebuildStatusText()

    def addOfflineBar(self):
        if self.eventBox is None:
            self.mainBox.pack_start(self.getOfflineBar(), False, False, 0)
            self.eventBox.show_all()
            
    def removeOfflineBar(self,widget):
        self.mainBox.remove(self.eventBox)
        self.eventBox = None

class Header(gtk.HBox):
    '''the header of the conversation'''

    def __init__(self, parentUI, controller):
        '''Contructor'''
        gtk.HBox.__init__(self)
        self.parentUI = parentUI
        self.controller = controller
        self.config = controller.config
        self.set_border_width(2)
        self.set_spacing(2)
        self.parser = controller.unifiedParser

        self.smileysCache = {}
        self.parseSmilies = self.config.user['parseSmilies']

        self.statusImage = gtk.Image()
        self.statusImage.set_from_pixbuf(self.controller.theme.getImage('groupChat'))

        camicon = gtk.Image()
        camicon.set_from_pixbuf(self.controller.theme.getImage('cam'))
        self.btn_ask_webcam = gtk.Button()
        self.btn_ask_webcam.set_image(camicon)
        self.btn_ask_webcam.set_relief(gtk.RELIEF_NONE)
        self.btn_ask_webcam.connect('clicked', self.ask_webcam_clicked)
        self.user = self.controller.getContact(\
            self.parentUI.parentConversation.getMembers()[0])
        self.btn_ask_webcam.set_tooltip_text(_('View webcam'))

        if self.user.shares_webcam():
            self.btn_ask_webcam.show()

        self.text = ''
        self.label = SmileyLabel('', self.controller.widget_style)
        self.label.unset_flags(gtk.CAN_FOCUS)
        self.label.set_wrap(True)
        self.label.set_ellipsize(pango.ELLIPSIZE_END)

        self.eventBox = gtk.EventBox()
        self.menu = gtk.Menu()
        copynick = self.newImageMenuItem(_('Copy nick to clipboard'), gtk.STOCK_COPY)
        copypm = self.newImageMenuItem(_('Copy personal message to clipboard'), gtk.STOCK_COPY)
        copymail = self.newImageMenuItem(_('Copy mail to clipboard'), gtk.STOCK_COPY)
        self.menu.append(copynick)
        self.menu.append(copypm)
        self.menu.append(copymail)
        copynick.connect('activate', self.copy_nick)
        copypm.connect('activate', self.copy_pm)
        copymail.connect('activate', self.copy_mail)
        copynick.show()
        copypm.show()
        copymail.show()
        
        self.eventBox.set_visible_window(False)
        self.eventBox.add(self.label)
        self.eventBox.connect('button-press-event', self.button_clicked)

        self.pack_start(self.statusImage, False, False)
        self.pack_start(self.eventBox)
        self.pack_start(self.btn_ask_webcam, False, False)
        self.statusImage.show()
        self.show_all()
        
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
        
    def button_clicked(self, widget, event):
        if len(self.parentUI.parentConversation.getMembersDict()) == 1:
            self.menu.popup(None, None, None, event.button, event.time, None)
            
    def copy_nick(self, w):
        conversation = self.parentUI.parentConversation
        members = conversation.getMembersDict()
        contact = members.values()[0]
        
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(contact.nick)
        
    def copy_pm(self, w):
        conversation = self.parentUI.parentConversation
        members = conversation.getMembersDict()
        contact = members.values()[0]
        
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(contact.personalMessage)
        
    def copy_mail(self, w):
        conversation = self.parentUI.parentConversation
        members = conversation.getMembersDict()
        contact = members.values()[0]
        
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(contact.email)
        
    def reconnectClicked(self, *args):
        self.parentUI.parentConversation.reconnect()
        
    def update(self):
        conversation = self.parentUI.parentConversation
        if self.config.user['showTabImageStatus']:
            self.statusImage.hide()
            return
        self.statusImage.set_from_pixbuf(conversation.getStatusIcon())
        if conversation.switchboard.status == 'error':
            self.setLabel()
            # TODO wtf is this doing here?
            self.parentUI.parentConversation.\
                parentConversationWindow.menu.update()
            return
            
    def setLabel(self, styleOpen='<b>', styleClose='</b>'):
        '''Sets the header label, the one that often includes bold nick,
           gray psm and mail. It also checks the switchboard status.'''
        conversation = self.parentUI.parentConversation
        members = conversation.getMembersDict()
        personalMessageColor = self.config.user['personalMessageColor']
        switchboard = conversation.switchboard

        if switchboard.status == 'error':
            self.btn_ask_webcam.hide()
            return

        if self.user.shares_webcam():
            self.btn_ask_webcam.show()

        if len(members) == 1:
            contact = members.values()[0]
            status = self.controller.status_ordered[0].index(contact.status)
            status = self.controller.status_ordered[2][status]

            # btw, styleOpen/styleClose is ignored, didn't find a good way to handle it
            args = {'email' : contact.email, 
                    'status' : status,
                    'nick' : contact.nick.replace('\n', ' '),
                    'pm' : contact.personalMessage.replace('\n', ' '),
                    'color' : personalMessageColor}

            try:
                # load the template from config
                template = list(eval(self.config.user['convHeaderTemplate']))
                if not [str,str] == [type(x) for x in template]:
                    raise Exception
                if not template[0].count('%s')-1 == template[1].count(';'):
                    raise Exception

                # remove parts enclosed in $ when the contact has no pm
                if not contact.personalMessage:
                    template[0] = ''.join(x if i % 2 == 0 else '' for i,x in enumerate(template[0].split("$")))

                # split string and prepare for parser
                template[0] = template[0].replace('\\n','\n').replace('$','')
                template = tuple([template[0]]+[args[x] for x in template[1].split(';')])
            except Exception:
                print 'convHeaderTemplate malformed, using default.'
                template = ('<span foreground="'+personalMessageColor+'">%s</span>\n'+
                            '<span foreground="'+personalMessageColor+'">%s</span>',args['pm'],args['email'])

            self.output = self.parser.getParser(template, UserListDataType).get(self.parseSmilies, self.smileysCache)
            # hack to remove the &#173; from the color tags
            self.output = [x.replace('&#173;#','#') if isinstance(x,basestring) else x for x in self.output]

        elif len(members) > 1:
            self.output = styleOpen + _('Group chat') + styleClose + \
                "\n<span foreground='%s'>" % personalMessageColor + \
                str(len(members)) + ' ' + _('members') + "</span>"

            self.statusImage.set_from_pixbuf(
                self.controller.theme.getImage('groupChat') )

        self.label.set_markup(self.output)
                
    def setTyping(self):
        typingColor = self.config.user['typingColor']
        styleOpen = "<b><span foreground='" + typingColor + "'>"
        styleClose = "</span></b>"
        self.setLabel(styleOpen, styleClose)

    def ask_webcam_clicked(self, *args):
        ret = self.parentUI.parentConversation.view_webcam()
        if ret == 1:
            dialog.error(\
                _('You don\'t have libmimic, so you can\'t send or receive webcam'))
        
    def setDefault(self):
        self.setLabel()

class TabWidget(gtk.HBox):
    '''this class represent the widget that is inside the tab
    it contains a label and a close button'''

    def __init__(self, parentUI, controller):
        '''Contructor'''
        gtk.HBox.__init__(self)

        self.parentUI = parentUI
        self.controller = controller
        self.config = controller.config

        self.text = ''
        self.markup = ''
        self.hasMessageWaiting = False
        self.updateText()
        
        self.label = gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_markup(self.markup)
        self.label.set_ellipsize(pango.ELLIPSIZE_END)

        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)

        self.closeButton = gtk.Button()
        self.closeButton.set_image(img)
        self.closeButton.set_relief(gtk.RELIEF_NONE)

        self.statusImage = gtk.Image()

        self.pack_start(self.statusImage, False, False)
        self.pack_start(self.label)
        self.pack_start(self.closeButton, False, False)

        self.closeButton.connect('clicked', self.onCloseClicked)
        self.show_all()

    def onCloseClicked(self, button):
        self.parentUI.parentConversation.close()

    def update(self):
        self.updateText()
        #if not self.config.user['showTabImageStatus']:
        #    return
        members = self.parentUI.parentConversation.getMembersDict()

        if len(members) == 1:
            contact = members.values()[0]
            basepixbuf = self.controller.theme.statusToPixbuf(contact.status)
        else:
            basepixbuf = self.controller.theme.getImage('userPanel')

        self.statusImage.set_from_pixbuf(resizePixbuf(basepixbuf, 16, 16))

    def updateText(self):
        title = self.parentUI.parentConversation.getTitle()
        parts = self.controller.unifiedParser.getParser(title,
            PangoDataType).get()
        self.markup = ''.join([str(x) for x in parts])
        self.text = self.controller.unifiedParser.getParser(title).get()

    def setDefault(self):
        self.label.set_markup(self.markup)
        preventTime = 0
        if self.config.user['preventClosingTime']:
            preventTime = 1000
        gobject.timeout_add(preventTime, self.setNoMessageWaiting)

    def setNoMessageWaiting(self):
        self.hasMessageWaiting = False
        return False

    def setTyping(self):
        typingColor = self.config.user['typingColor']
        self.label.set_markup('<span foreground="%s">%s</span>' % (typingColor, self.text))

    def setMessageWaiting(self):
        messageWaitingColor = self.config.user['messageWaitingColor']
        self.label.set_markup('<span foreground="%s">%s</span>' % (messageWaitingColor, self.text))
        self.hasMessageWaiting = True

class AvatarHBox(gtk.HBox):
    def __init__(self, parentUI, controller, mail='', localavatar=False):
        gtk.HBox.__init__(self)

        self.parentUI = parentUI
        self.controller = controller
        self.config = controller.config
        self.mail = mail

        self.hidebutton = gtk.Button()
        self.hidebutton.connect('clicked', self.hideShowButton)
        self.hidebutton.set_relief(gtk.RELIEF_NONE)
        if self.config.user['avatarsOnRight']:
            self.hidebuttonArrow = gtk.Arrow(gtk.ARROW_RIGHT,gtk.SHADOW_NONE)
            self.hidebuttonArrow.set_alignment(1,0.5)
            self.hidebuttonArrow.set_size_request(-1,10)
        else:
            self.hidebuttonArrow = gtk.Arrow(gtk.ARROW_LEFT,gtk.SHADOW_NONE)
            self.hidebuttonArrow.set_alignment(0,0.5)
            self.hidebuttonArrow.set_size_request(-1,10)
        self.hidebutton.add(self.hidebuttonArrow)

        self.image = Widgets.avatarHolder(cellKeyPosition=gtk.ANCHOR_SOUTH)
        self.imageEventBox = gtk.EventBox()
        self.imageEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.imageEventBox.set_visible_window(False)
        self.imageEventBox.add(self.image)

        self.updateDisplayPicture()
        self.menu = gtk.Menu()                                  
        setAvatarMenuItem = self.newImageMenuItem(_("Set as your _avatar"), \
            gtk.STOCK_ADD)                                                 
        saveAsMenuItem = self.newImageMenuItem(_("_Save image as"), \
            gtk.STOCK_SAVE_AS)                                             
        self.menu.append(setAvatarMenuItem)                                
        self.menu.append(saveAsMenuItem)                                   
        setAvatarMenuItem.connect("activate", self.on_set_yours)           
        saveAsMenuItem.connect("activate", self.on_save_as)                
        setAvatarMenuItem.show()                                           
        saveAsMenuItem.show()   
        
        # if we have an email, this is our contact's avatar
        self.dpid = None
        self.atchangeid = None
        self.avchangeid = None
        if mail:
            self.dpid = self.controller.msn.connect('display-picture-changed',
                self.onDisplayPictureChanged)
            self.atchangeid = self.controller.msn.connect('user-attr-changed',
                self.onDisplayPictureChanged)
            self.imageEventBox.connect('button-press-event', \
                self.button_clicked)  
                
            self.key = 'showAvatarOther'
        else:
            # we don't have an email, so this is our avatar
            self.avchangeid = self.controller.connect('avatar-changed',
                self.onDisplayPictureChanged)

            self.imageEventBox.connect('button-press-event',
                lambda w, e: self.controller.set_picture_dialog())

            self.key = 'showAvatarMine'

        self.filler = gtk.VBox()

        self.vboxButtonFrame = gtk.VBox()
        self.vboxButtonFrame.pack_start(self.hidebutton, False, False)
        self.vboxButtonFrame.pack_start(self.filler, True, True)

        self.filler2 = gtk.VBox()

        self.vboxAvatarFrame = gtk.VBox()
        self.vboxAvatarFrame.pack_start(self.imageEventBox, False, False)
        self.vboxAvatarFrame.pack_start(self.filler2, True, True)

        self.container = gtk.VBox()

        if localavatar:
            self.container.pack_start(self.vboxButtonFrame, False, False)
            self.container.pack_start(self.vboxAvatarFrame, False, False)
        else:
            self.container.pack_start(self.vboxAvatarFrame, False, False)
            self.container.pack_start(self.vboxButtonFrame, False, False)

        self.pack_start(self.container, False, False)
        self.update()

    def close(self):
        if self.controller.msn is not None:
            if self.dpid is not None: self.controller.msn.disconnect(self.dpid)
            if self.atchangeid is not None: self.controller.msn.disconnect(self.atchangeid)
        if self.avchangeid is not None: self.controller.disconnect(self.avchangeid)

    def update(self):
        avatarRight = self.config.user['avatarsOnRight']
        if not self.config.user[self.key]:
            self.imageEventBox.hide()
            if avatarRight:
                self.hidebuttonArrow.set(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
            else:
                self.hidebuttonArrow.set(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
        else:
            self.imageEventBox.show()
            if avatarRight:
                self.hidebuttonArrow.set(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
            else:
                self.hidebuttonArrow.set(gtk.ARROW_LEFT, gtk.SHADOW_NONE)

    def button_clicked(self, widget, event):                                         
        if len(self.parentUI.parentConversation.getMembersDict()) == 1:              
            self.menu.popup(None, None, None, event.button, event.time, None)        
                                                                                     
    def on_set_yours(self, *args):                                                   
        contact = self.controller.getContact(self.mail)                              
        imagePath = os.path.join(self.config.getCachePath(), \
            contact.displayPicturePath)                                              
        self.controller.changeAvatar(imagePath)                                      
                                                                                     
    def on_save_as(self, *args):                                                     
        contact = self.controller.getContact(self.mail)                              
        imagePath = os.path.join(self.config.getCachePath(), \
            contact.displayPicturePath)                                              
                                                                                     
        dialog = gtk.FileChooserDialog(_('Save image as'),action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))    
        dialog.set_current_name(os.path.split(imagePath)[1]+".png")                           
        if dialog.run() == gtk.RESPONSE_OK:                                                   
            shutil.copy2(imagePath, dialog.get_filename())                                    
        dialog.destroy()                                                                      

    def updateDisplayPicture(self):
        if self.mail:
            contact = self.controller.getContact(self.mail)
            if contact:
                pixbuf = self.controller.theme.getUserDisplayPicture(contact)
                self.image.set_from_pixbuf(pixbuf)
        else:
            # sets an avatar if there is one, otherwise defaults to icon96
            if self.controller.config.user['avatarPath'] != '':
                self.image.set_from_pixbuf(self.controller.avatar.getImage())
            else:
                pixbuf = self.controller.theme.getImage('login')
                self.image.set_from_pixbuf(pixbuf)

    def updateDPnoCrossfade(self):
        self.image.set_property('crossFade', False)
        self.updateDisplayPicture()
        self.image.set_property('crossFade', True)

    def onDisplayPictureChanged(self, *args):
        self.updateDisplayPicture()
        self.parentUI.update()

    def hideShowButton(self, *args):
        if self.config.user['showAvatars']:
            self.config.user[self.key] = not self.config.user[self.key]
        self.update()
        
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

class InputWidget(gtk.HBox):
    '''This class represents the input widgets (text entry) and avatar (if enabled)'''

    TARGET_TYPE_URI_LIST = 80
    TARGET_TYPE_PLAIN_TEXT = 81
    DND_LIST = [ ('text/uri-list', 0, TARGET_TYPE_URI_LIST),
                ('text/plain', 0, TARGET_TYPE_PLAIN_TEXT) ]

    def __init__(self, parentUI, controller, setFocus=True, avatarRight=True):
        gtk.HBox.__init__(self)
        self.set_border_width(2)
        self.parentUI = parentUI
        self.controller = controller
        self.config = controller.config
        self.lastKeyPressed = 0
        self.history = []
        self.historyIndex = -1

        # the local avatar
        self.localAvatar = AvatarHBox(self, controller, localavatar=True)
        # the toolbar
        self.toolbar = ToolbarWidget(self.parentUI, controller)
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.set_small(self.config.user['smallIcons'])

        self.input = Widgets.inputBox()
        self.input.set_left_margin(6)
        self.input.set_right_margin(6)
        self.input.set_wrap_mode(gtk.WRAP_WORD_CHAR)

        self.sendbutton = gtk.Button(_('Send'))
        self.sendbutton.show()
        self.sendbuttonwin = gtk.EventBox()
        self.sendbuttonwin.add(self.sendbutton)

        self.input.add_child_in_window(
            self.sendbuttonwin, gtk.TEXT_WINDOW_TEXT, 0, 0)

        self.sendbutton.connect('clicked', self.message_send)
        self.sendbuttonwin.connect('realize', self.change_cursor)

        self.inputBuffer = self.input.get_buffer()

        self.scrollInput = gtk.ScrolledWindow()
        self.scrollInput.set_policy(gtk.POLICY_AUTOMATIC,
                                    gtk.POLICY_AUTOMATIC)
        self.scrollInput.add(self.input)

        frameInput = gtk.Frame()
        frameInput.set_shadow_type(gtk.SHADOW_IN)

        avatar_frame = gtk.AspectFrame(xalign=0.0, yalign=1.0)
        avatar_frame.add(self.localAvatar)
        avatar_frame.set_shadow_type(gtk.SHADOW_NONE)

        self.vbox = gtk.VBox()

        self.vbox.pack_start(self.toolbar, False)
        self.vbox.pack_start(self.scrollInput, True, True)
        frameInput.add(self.vbox)
        if avatarRight:
            self.pack_start(frameInput, True, True)
            self.pack_start(avatar_frame, False, False)
        else:
            self.pack_start(avatar_frame, False, False)
            self.pack_start(frameInput, True, True)
            
        self.inputBuffer.connect('changed', self.on_changed_event)
        self.input.connect('key-press-event', self.on_key_press_event)
        
        self.input.drag_dest_set(gtk.DEST_DEFAULT_MOTION | \
            gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, \
            InputWidget.DND_LIST, gtk.gdk.ACTION_COPY)
        self.input.connect('drag_motion', self.drag_callback)
        self.input.connect('drag_drop', self.drop_callback)
        self.input.connect('drag-data-received', self.drag_data_received)

        self.input.connect_after('message-send', self.message_send)
        self.input.connect_after('escape-pressed',
                                    self.on_escape_pressed_event)

        self.input.connect_after('map-event', self.on_input_map_event)
        self.input.connect('size-allocate', self.move_sendbtn)
        self.scrollInput.get_vadjustment().connect('value-changed',
            self.move_sendbtn)

        self.input.connect_after('copy-clipboard', self._on_copy_clipboard)

        if setFocus:
            self.input.grab_focus()

        self.tag = None
        self.id_timeout = None
        self.parse_off = 0
        self.applyAttrsToInput()
        self.show_all()

    def update(self):
        '''update the inner componnents if needed'''

        if self.config.user['showAvatars']:
            self.localAvatar.show()
            self.localAvatar.update()
        else:
            self.localAvatar.hide()

        self.toolbar.update()

        if not self.config.user['showToolbar']:
            self.toolbar.hide()
        else:
            self.toolbar.show()

        if not self.config.user['showSendButton']:
            self.sendbutton.hide()
        else:
            self.sendbutton.show()

    def transformEmo(self, *args):
        ''' transform smiley shorcuts in pixbuf '''
        if not self.controller or not self.controller.customEmoticons:
            return

        if not self.controller.config.user['parseSmilies']:
            return

        theme = self.controller.theme
        customEmo = self.controller.customEmoticons
        
        def get_smilie_pixbuf(code, filename=None):
            if filename is not None:
                pixbuf = resizePixbuf(gtk.gdk.pixbuf_new_from_file(filename),
                                      24, 24)
            else:
                pixbuf = theme.getSmiley(code, False)
            return pixbuf

        def replace_shortcuts(code, filename):
            iter_start = self.inputBuffer.get_start_iter()
            iter_start.set_offset(self.parse_off)
            while iter_start.forward_search(code,
                                gtk.TEXT_SEARCH_VISIBLE_ONLY):
                iter_pos, iter_end = iter_start.forward_search(code, \
                    gtk.TEXT_SEARCH_VISIBLE_ONLY)

                mark1 = self.inputBuffer.create_mark(None, iter_pos)
                mark2 = self.inputBuffer.create_mark(None, iter_end)
                
                self.inputBuffer.delete(iter_pos, iter_end)
                
                pixbuf = get_smilie_pixbuf(code, filename)

                img = gtk.Image()
                img.set_from_pixbuf(pixbuf)
                img.show()
                img.shortcut = code

                iterStart = self.inputBuffer.get_iter_at_mark(mark1)
                anchor = self.inputBuffer.create_child_anchor(iterStart)
                self.input.add_child_at_anchor(img, anchor)

                iter_start = self.inputBuffer.get_iter_at_mark(mark2)
                self.inputBuffer.delete_mark(mark1)
                self.inputBuffer.delete_mark(mark2)

        for code in theme.getSmileysList():
            replace_shortcuts(code, None)

        for code, filename in customEmo.list.iteritems():
            replace_shortcuts(code, filename)

        iter_off = self.inputBuffer.get_end_iter()
        if iter_off.inside_word() or iter_off.ends_word():
            iter_off.backward_word_start()
        self.parse_off = iter_off.get_offset()

    def grabFocus(self):
        self.input.grab_focus()
        
    def clearMessageInput(self):
        self.setInputText('')
        return True

    def sendMessage(self):
        if self.getInputText(True) != '':
            # Message size is limited so we must truncate it to send
            # it in several parts
            message = self.getInputText()

            self.parentUI.parentConversation.sendMessage(message)
            self.setInputText('')
            if self.historyIndex == -1:
                self.history.append(message)
            else:
                self.history[len(self.history)-1] = message
            self.historyIndex = -1
        return True

    def setInputText(self, string, tag=None):
        if tag == None:
            self.inputBuffer.set_text(string)
        else:
            pass
    
    def getInputText(self, fast=False, selection=False):
        '''return the text in the input textview'''
        if selection:
            iterStart, iterEnd = self.inputBuffer.get_selection_bounds()
        else:
            iterStart, iterEnd = self.inputBuffer.get_bounds()
        text = self.inputBuffer.get_slice(iterStart, iterEnd)

        if fast:
            return text
        emos = []

        #TODO: magic string '\xef\xbf\xbc'
        while iterStart.forward_search('\xef\xbf\xbc', \
            gtk.TEXT_SEARCH_VISIBLE_ONLY):

            iterPos, iterEnd = iterStart.forward_search('\xef\xbf\xbc', \
                gtk.TEXT_SEARCH_VISIBLE_ONLY)
            anchor = iterPos.get_child_anchor()
            if anchor and anchor.get_widgets():
                emos.append(anchor.get_widgets()[0].shortcut)
            elif anchor is None:
                emos.append('')

            iterStart = iterEnd

        for emo in emos:
            text = text.replace('\xef\xbf\xbc', emo, 1)

        return text

    def appendInputText(self, text, tag = None):
        '''append the given text to the inputBuffer, if tag insert
        with the given tag'''
        self.inputBuffer.insert_at_cursor(text)

    def on_changed_event(self, *args):
        '''Method called when text is inserted in the textbuffer (typing)
        First, it checks if the message length is >= 5 or if
        the message is a slash command ("^\/[^\/]" is confusing)
        Then, checks the last key pressed time, and if it's more
        than 5 seconds, send a typing message'''
        
        self.updateInputFormat()
        
        if self.inputBuffer.get_start_iter().get_offset() < self.parse_off:
            self.parse_off = 0
        if self.id_timeout:
            gobject.source_remove(self.id_timeout)

        text = self.getInputText(True)
        if len(text) > 1 and not (text[0] == '/' and text[1] != '/'):
            self.id_timeout = gobject.timeout_add(200, self.transformEmo)

        if not len(text) > 5:
            #don't send start typing notification
            return

        # sents user typing notification
        actualTime = int(time.time())

        if (actualTime - self.lastKeyPressed) > 5 and \
           self.config.user['sendTyping']:
            self.lastKeyPressed = actualTime

            try:
                self.parentUI.parentConversation.sendIsTyping()
            except Exception , e:
                print str(e)

    def _on_copy_clipboard(self, textview):
        try:
            start_sel, end_sel = self.inputBuffer.get_selection_bounds()
            text = self.getInputText(False, True)
            clipboard = gtk.clipboard_get()
            clipboard.set_text(text, -1)
            clipboard.store()
        except ValueError: #if the user just press ctrl+c with nothing selected
            return

    def applyAttrsToInput(self):
        '''apply the current attributes to the text in input'''

        tag = gtk.TextTag()

        if self.config.user['disableFormat']:
            return tag

        tag.set_property('font', self.config.user['fontFace'])
        tag.set_property('size-points', self.config.user['fontSize'])
        tag.set_property("foreground", self.config.user['fontColor'])

        if self.config.user['fontBold']:
            tag.set_property("weight", pango.WEIGHT_BOLD)

        if self.config.user['fontItalic']:
            tag.set_property("style", pango.STYLE_ITALIC)

        if self.config.user['fontUnderline']:
            tag.set_property("underline-set", True)
            tag.set_property("underline" , pango.UNDERLINE_SINGLE)
        else:
            #XXX: wtf is that underline-set=True?
            tag.set_property("underline-set", True)
            tag.set_property("underline", pango.UNDERLINE_NONE)

        self.tag = tag
        self.tag.set_property("strikethrough", self.config.user['fontStrike'])

        self.inputBuffer.get_tag_table().add(self.tag)
        self.tag.set_property('left-margin', 6)
        self.tag.set_priority(self.inputBuffer.get_tag_table().get_size() - 1)
        self.updateInputFormat()

        self.controller.emit('input-format-changed', self.input)

    def updateInputFormat(self):
        if self.tag:
            self.inputBuffer.apply_tag(self.tag,
                                       self.inputBuffer.get_start_iter(),
                                       self.inputBuffer.get_end_iter())


    def message_send(self, widget):
        if self.id_timeout:
            gobject.source_remove(self.id_timeout)
            self.id_timeout = None

        return self.sendMessage()

    def on_input_map_event(self, widget, event):
        if self.parentUI.parentConversation.isCurrent:
            self.input.grab_focus()

    def on_escape_pressed_event(self, widget):
        #if the Esc key is not disable
        if not self.parentUI.closed and not self.config.user['disableEsc']:
            #if the closing prevention is activated
            if self.config.user['preventClosingTime']:
                if self.parentUI.tabWidget.hasMessageWaiting \
		            or self.parentUI.parentConversation.hasMessageWaiting:
                    esc_message = _('Messages has just arrived, maybe they were not read')
                    self.parentUI.set_label_closingPrevention(esc_message)
                else:
                    self.parentUI.parentConversation.close()
            else:
                self.parentUI.parentConversation.close()

    def on_key_press_event(self , widget, event):
        if event.keyval == gtk.keysyms.space:
            if self.id_timeout:
                gobject.source_remove(self.id_timeout)
                self.id_timeout = None
            if not self.getInputText(True).startswith('/'):
                self.transformEmo()

        # scrollback
        elif event.keyval in (gtk.keysyms.Up, gtk.keysyms.Down) and \
            (event.state & gtk.gdk.CONTROL_MASK):
            up = event.keyval == gtk.keysyms.Up

            if len(self.history) > 0:
                if up and self.historyIndex == -1:
                    self.history.append(self.getInputText())
                    self.historyIndex = len(self.history)-2

                elif self.historyIndex > -1:
                    self.history[self.historyIndex] = self.getInputText()
                    if up and self.historyIndex > 0:
                        self.historyIndex -= 1
                    if not up and self.historyIndex < len(self.history)-1:
                        self.historyIndex += 1

            if self.historyIndex > -1 and self.historyIndex < len(self.history):
                self.setInputText(self.history[self.historyIndex])

    def drag_callback(self, wid, context, x, y, time):
        context.drag_status(gtk.gdk.ACTION_COPY, time)    
        return True
        
    def drop_callback(self, wid, context, x, y, time):
        context.finish(True, False, time)
        return True

    def drag_data_received(self, widget, context, x, y, selection,
                              target_type, timestamp):
        '''Callback to drag_data_received'''
        if target_type == InputWidget.TARGET_TYPE_URI_LIST:
            uri = selection.data.strip()
            uri_splitted = uri.split()
            for uri in uri_splitted:
                path = self.get_file_path_from_dnd_dropped_uri(uri)
                if os.path.isfile(path):
                    self.parentUI.parentConversation.sendFile(path)
        
        elif target_type == InputWidget.TARGET_TYPE_PLAIN_TEXT:
            # TODO: find out the DND handler that copies the text from the
            #       htmltextview to the input widget automagically,
            #       kill the pass and decomment the following line
            #self.appendInputText(selection.data.decode('raw_unicode_escape'))
            pass
            
        return True
            
    def get_file_path_from_dnd_dropped_uri(self, uri):
        '''Parses an URI received from dnd and return the real path'''

        if os.name != 'nt':
            path = urllib.url2pathname(uri) # escape special chars
        else:
            path = urllib.unquote(uri) # escape special chars
        path = path.strip('\r\n\x00') # remove \r\n and NULL

        # get the path to file
        if re.match('^file:///[a-zA-Z]:/', path): # windows
            path = path[8:] # 8 is len('file:///')
        elif path.startswith('file://'): # nautilus, rox
            path = path[7:] # 7 is len('file://')
        elif path.startswith('file:'): # xffm
            path = path[5:] # 5 is len('file:')
        return path

    def move_sendbtn(self, *args):
        '''update sendbutton position'''

        allocation = self.input.get_allocation()
        x = allocation.x
        y = allocation.y
        w = allocation.width
        h = allocation.height

        sendwin_alloc = self.sendbutton.get_allocation()
        xswin = sendwin_alloc.x
        yswin = sendwin_alloc.y
        wswin = sendwin_alloc.width
        hswin = sendwin_alloc.height

        space = 2

        self.input.set_right_margin(wswin + space)
        self.input.move_child(self.sendbuttonwin, w - wswin - space, h / 2 -
                                                                hswin / 2)
        self.input.queue_draw()

    def change_cursor(self, *args):
        self.sendbuttonwin.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))

class ToolbarWidget(gtk.Toolbar):
    '''This represents a toolbar that contains text formatation,
    smilies button, do nudge button, and so on...'''

    def __init__(self, parentUI, controller):
        gtk.Toolbar.__init__(self)
        self.parentUI = parentUI
        self.controller = controller
        self.config = controller.config
        self.smilieWindow = SmilieWindow.SmilieWindow(self.controller, \
                                                       self.smilieSelected, \
                                                       None)
        self.FontStyleWindow = FontStyleWindow.FontStyleWindow( \
                                                        self.controller, \
                                                       self.parentUI)

        #font face
        separator = False
        if self.config.user['toolFontType']:
            self.fontFace = gtk.ToolButton(label=_('Font selection'))
            if self.controller.theme.getImage('fontface'):
                fontfaceicon = gtk.Image()
                fontfaceicon.set_from_pixbuf(self.controller.theme.getImage('fontface'))
                self.fontFace.set_icon_widget(fontfaceicon)
            else:
                self.fontFace.set_stock_id(gtk.STOCK_SELECT_FONT)
            self.fontFace.connect('clicked', self.on_font_face_clicked)
            self.insert(self.fontFace, -1)
            self.fontFace.set_tooltip_text(_('Font selection'))
            separator = True
        else:
            self.fontFace = None

        #font color
        if self.config.user['toolFontColor']:
            self.fontColor = gtk.ToolButton(label=_('Font color selection'))
            if self.controller.theme.getImage('fontcolor'):
                fontcoloricon = gtk.Image()
                fontcoloricon.set_from_pixbuf(self.controller.theme.getImage('fontcolor'))
                self.fontColor.set_icon_widget(fontcoloricon)
            else:
                self.fontColor.set_stock_id(gtk.STOCK_SELECT_COLOR)
            self.fontColor.connect('clicked', self.on_font_color_clicked)
            self.insert(self.fontColor, -1)
            self.fontColor.set_tooltip_text(_('Font color selection'))
            separator = True
        else:
            self.fontColor = None

        #font style button
        if self.config.user['toolFontStyle']:
            self.fontStyleButton = gtk.ToolButton(label=_('Fontstyle'))
            if self.controller.theme.getImage('fontstyle'):
                fonticon = gtk.Image()
                fonticon.set_from_pixbuf(self.controller.theme.getImage('fontstyle'))
                self.fontStyleButton.set_icon_widget(fonticon)
            else: 
                self.fontStyleButton.set_stock_id(gtk.STOCK_BOLD)
            self.fontStyleButton.connect('clicked', self.showFontStyleWindow)
            self.insert(self.fontStyleButton, -1)
            self.fontStyleButton.set_tooltip_text(_('Font styles'))
            separator = True
        else:
            self.fontStyleButton = None

        if separator:
            self.insert(gtk.SeparatorToolItem(), -1)
        separator = False

        #smilie button, fixed for mac4lin
        if self.config.user['toolSmilies']:
            smilieicon = gtk.Image()
            smilieicon.set_from_pixbuf(self.controller.theme.getImage('smilie'))
            self.smilieButton = gtk.ToolButton(smilieicon, _('Smilie'))
            self.smilieButton.connect('clicked', self.showSmilieWindow)
            self.insert(self.smilieButton, -1)
            self.smilieButton.set_tooltip_text(_('Insert a smilie'))
            separator = True
        else:
            self.smilieButton = None

        #nudge button, fixed for mac4lin
        if self.config.user['toolNudge']:
            nudgeicon = gtk.Image()
            nudgeicon.set_from_pixbuf(self.controller.theme.getImage('nudge'))
            self.nudgeButton = gtk.ToolButton(nudgeicon, _('Nudge'))
            self.nudgeButton.connect('clicked', self.doNudge)
            self.insert(self.nudgeButton, -1)
            self.nudgeButton.set_tooltip_text(_('Send nudge'))
            separator = True
        else:
            self.nudgeButton = None

        if separator:
            self.insert(gtk.SeparatorToolItem(), -1)
        separator = False

        #invite button
        if self.config.user['toolInvite']:
            self.inviteButton = gtk.ToolButton(label=_('Invite'))
            if self.controller.theme.getImage('invite'):
                inviteicon = gtk.Image()
                inviteicon.set_from_pixbuf(self.controller.theme.getImage('invite'))
                self.inviteButton.set_icon_widget(inviteicon)
            else:
                self.inviteButton.set_stock_id(gtk.STOCK_ADD)
            self.inviteButton.connect('clicked', self.showInviteDialog)
            self.insert(self.inviteButton, -1)
            self.inviteButton.set_tooltip_text( \
                _('Invite a friend to the conversation'))
            separator = True
        else:
            self.inviteButton = None

        #send a file
        if self.config.user['toolSendFile']:
            self.sendfileButton = gtk.ToolButton(label=_('Send File'))
            if self.controller.theme.getImage('sendfile'):
                imgsendfile = gtk.Image()
                imgsendfile.set_from_pixbuf(self.controller.theme.getImage('sendfile'))
                self.sendfileButton.set_icon_widget(imgsendfile)
            else:
                self.sendfileButton.set_stock_id(gtk.STOCK_GOTO_TOP)
            self.sendfileButton.connect('clicked', self.sendFileClicked)
            self.insert(self.sendfileButton, -1)
            self.sendfileButton.set_tooltip_text(_('Send a file'))
            separator = True
        else:
            self.sendfileButton = None

        # webcam send hax
        if self.config.user['toolWebcam']:
            camicon = gtk.Image()
            camicon.set_from_pixbuf(self.controller.theme.getImage('cam'))
            self.sendWebcamButton = gtk.ToolButton(camicon, _('Send Webcam'))
            self.sendWebcamButton.connect('clicked', self.sendWebcamClicked)
            self.insert(self.sendWebcamButton, -1)
            self.sendWebcamButton.set_tooltip_text(_('Send your Webcam'))
            separator = True
        else:
            self.sendWebcamButton = None

        if separator:
            self.insert(gtk.SeparatorToolItem(), -1)
        separator = False

        #clear conversation toolbar button
        if self.config.user['toolClear']:
            imgclear = gtk.Image()
            if self.controller.theme.getImage('clear'):
                imgclear.set_from_pixbuf(self.controller.theme.getImage('clear'))
            else:
                imgclear.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.clearButton = gtk.ToolButton(imgclear, _('Clear Conversation'))
            self.clearButton.connect('clicked', self.clearOutputText)
            self.insert(self.clearButton, -1)
            self.clearButton.set_tooltip_text(_('Clear conversation'))
            separator = True
        else:
            self.clearButton = None

        if separator:
            self.insert(gtk.SeparatorToolItem(), -1)
        separator = False

        #remove the last separator
        count = self.get_n_items()
        item = self.get_nth_item(count-1)
        if isinstance(item, gtk.SeparatorToolItem):
            self.remove(item)

        # ENABLE THIS IF YOU IMPLEMENT INKDRAW P2P STACK
        #self.inkdrawButton = gtk.ToolButton()
        #self.inkdrawButton.set_label(_('Send Ink'))
        #self.inkdrawButton.set_stock_id(gtk.STOCK_EDIT)
        #self.inkdrawButton.connect('clicked', self.inkDrawClicked)
        #self.insert(self.inkdrawButton, -1)

        self.show_all()

    def setFontBold(self, value):
        self.FontStyleWindow.buttonBold.set_active(value)

    def setFontUnderline(self, value):
        self.FontStyleWindow.buttonUnderline.set_active(value)

    def setFontStrike(self, value):
        self.FontStyleWindow.buttonStrike.set_active(value)

    def setFontItalic(self, value):
        self.FontStyleWindow.buttonItalic.set_active(value)

    def on_font_face_clicked(self, *args):
        '''Called when user clicks on the font selection button
        in the toolbar'''
        self.parentUI.parentConversation.parentConversationWindow.changeFont()

    def on_font_color_clicked(self, *args):
        ''' Called when user clicks on the color selection button in the toolbar'''
        self.parentUI.parentConversation.parentConversationWindow.changeColor()

    def set_small(self, value):
        '''sets the icons size to small if value is True'''

        if value:
                size = gtk.ICON_SIZE_MENU
                imgSmilie = gtk.Image()
                imgNudge = gtk.Image()

                nudge = self.controller.theme.getImage('nudge')
                grin = self.controller.theme.getSmiley(':D')
                if isinstance(grin, gtk.gdk.PixbufAnimation):
                    grin = grin.get_static_image()

                grin = resizePixbuf(grin, *gtk.icon_size_lookup(size))
                nudge = resizePixbuf(nudge, *gtk.icon_size_lookup(size))
                imgSmilie.set_from_pixbuf(grin)
                imgNudge.set_from_pixbuf(nudge)
                if self.smilieButton:
                    self.smilieButton.set_icon_widget(imgSmilie)
                if self.nudgeButton:
                    self.nudgeButton.set_icon_widget(imgNudge)
        else:
                size = gtk.ICON_SIZE_LARGE_TOOLBAR

        #set the global icons size
        settings = self.get_settings()
        settings.set_long_property('gtk-toolbar-icon-size', size, \
            'emesene:ConversationUI')

    def smilieSelected(self, smilie=None):
        '''this method is called when the user click a smilie in the
        smiliewindow'''

        if smilie:
            self.parentUI.input.appendInputText(smilie)
        self.parentUI.input.grabFocus()

    def showSmilieWindow(self, *args):
        '''this method is called when the user click the smilie button'''
        self.smilieWindow.show()

    def showFontStyleWindow(self, *args):
        '''this method calls the font styles window'''
        self.FontStyleWindow.show()

    def showInviteDialog(self, *args):
        '''this method is called when the user click the invite button'''
        if not self.controller or not self.controller.msn:
            return

        win = self.parentUI.parentConversation.parentConversationWindow
        if win is not None:
            win.show_invite_dialog()

    def clearOutputText(self, *args):
        self.parentUI.textview.clear()

    def doNudge(self, *args):
        '''this method is called when the user click the nudge button'''
        self.parentUI.parentConversation.doNudge()

    def sendFileClicked(self, *args):
        if not self.controller or not self.controller.msn:
            return

        win = self.parentUI.parentConversation.parentConversationWindow
        if win is not None:
            win.send_file_dialog()

    def sendWebcamClicked(self, *args):
        ret = self.parentUI.parentConversation.sendWebcam()
        if ret == 1:
            dialog.error(\
                _('You don\'t have libmimic, so you can\'t send or receive webcam'))
            
    def inkDrawClicked(self, *args):
        if not self.controller or not self.controller.msn:
            return

        win = self.parentUI.parentConversation.parentConversationWindow
        if win is not None:
            win.show_inkdraw_dialog()

    def update(self, *args):
        '''this method disables some buttons on switchboard error'''
        conversation = self.parentUI.parentConversation
        if conversation.switchboard.status == 'error' \
         or not self.controller or not self.controller.msn:
            if self.nudgeButton:
                self.nudgeButton.set_sensitive(False)
            if self.inviteButton:
                self.inviteButton.set_sensitive(False)
            if self.sendfileButton:
                self.sendfileButton.set_sensitive(False)
            if self.smilieButton:
                self.smilieButton.set_sensitive(False)
        else:
            if self.nudgeButton:
                self.nudgeButton.set_sensitive(True)
            if self.inviteButton:
                self.inviteButton.set_sensitive(True)
            if self.sendfileButton:
                self.sendfileButton.set_sensitive(True)
            if self.smilieButton:
                self.smilieButton.set_sensitive(True)

class InviteWindow(gtk.Dialog):
    '''This class represent a list where the user can pick wich users
    he want to invite to a conversation'''

    def __init__(self, controller, father, onlineUsers,
                    usersInConversation, theme, callback):
        '''Constructor callback is called when a user is selected with
        double click'''
        gtk.Dialog.__init__(self, _('Invite'), father,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, \
                     gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT))

        self.set_default_size(400, 300)
        self.callback = callback
        users = onlineUsers

        self.controller = controller

        for i in usersInConversation.keys():
            if users.has_key(i):
                del users[i]

        self.userList = UserList.UserList(self.controller, theme,
            self.controller.config, False)
        #self.userList.connect('item-selected', self.userListClicked)

        # hack to disable getMenuData
        self.userList.getMenuData = lambda: ('', '')

        self.selection = self.userList.get_selection()

        if gtk.gtk_version >= (2, 10, 0):
            self.userList.set_rubber_banding(True)
            self.userList.set_property("rubber-banding", True)

            self.selection.set_mode(gtk.SELECTION_MULTIPLE)

        group = emesenelib.ContactData.Group(_('Users'))

        for contact in controller.msn.contactManager.contacts.values():
            if contact and contact.status != 'FLN' and \
               contact.email not in usersInConversation:
                group.setUser(contact.email, contact)

        self.userList.fill({group.name : group})

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC , gtk.POLICY_AUTOMATIC)
        self.scroll.add(self.userList)

        self.connect('response', self.invite)
        self.connect('delete-event', self.close)

        tipText = _("For multiple select hold CTRL key and click")
        self.tipLabel = gtk.Label()
        self.tipLabel.set_markup("<small><i>" + tipText + "</i></small>")

        self.filterEntry = FilterEntry.FilterEntry(
            self.userList.setFilterText)

        self.vbox.set_spacing(3)
        self.vbox.pack_start(self.scroll)
        self.vbox.pack_start(self.tipLabel, False, False)
        self.vbox.pack_start(self.filterEntry, False, False)
        self.vbox.set_focus_child(self.filterEntry)
        self.vbox.show_all()

    def invite(self, dialog, response_id):
        '''get the user in the userlist and call the callback'''

        try:
            if response_id == gtk.RESPONSE_ACCEPT:
                #self.userListClicked(self.userList, self.userList.getSelected())

                model, iter = self.selection.get_selected_rows()
                for i in range(len(iter)):
                    print model[iter[i][0]][2]
                    self.callback(model[iter[i][0]][2])
                self.close()
                return True
            else:
                self.close()
                return False
        except Exception, e:
            print e

    def userListClicked(self, userList, t):

        if t and t[0] == 'user':
            self.callback(t[1].email)
            self.close()

    def close(self, *args):
        '''close the window'''

        self.hide()


