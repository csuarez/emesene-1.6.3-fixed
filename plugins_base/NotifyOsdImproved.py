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
import TrayIcon

import Plugin
import desktop
from emesenelib.common import escape
from emesenelib.common import unescape
from Parser import PangoDataType

ERROR = ''
try:
    import pynotify
    if not pynotify.init("emesene"):
        raise
except:
    ERROR = _('there was a problem initializing the pynotify module, install python-notify')

class MainClass(Plugin.Plugin):
    '''Main plugin class'''

    description = _('Notifies various events using the new system notifications')
    authors = {'Mariano Guerra': 'luismarianoguerra at gmail dot com',
        'Nicolas Espina Tacchetti': 'nicolasespina at gmail dot com',
        'Panagiotis Koutsias': 'pkoutsias at gmail dot com',}
    website = 'http://emesene-msn.blogspot.com'
    displayName = _('NotifyOsdImproved')
    name = 'NotifyOsdImproved'
    require = ['pynotify']
    def __init__(self, controller, msn):
        '''Contructor'''

        Plugin.Plugin.__init__(self, controller, msn)

        self.description = _('Notifies various events using the new system notifications')
        self.authors = {'Mariano Guerra': 'luismarianoguerra at gmail dot com',
        'Nicolas Espina Tacchetti': 'nicolasespina at gmail dot com',
        'Panagiotis Koutsias': 'pkoutsias at gmail dot com',}
        self.website = 'http://emesene-msn.blogspot.com'
        self.displayName = _('NotifyOsdImproved')
        self.name = 'NotifyOsdImproved'

        self.config = controller.config
        self.config.readPluginConfig(self.name)
        self.controller = controller

        self.notifyOnline = int(self.config.getPluginValue(self.name, 'notifyOnline', '1'))
        self.notifyOffline = int(self.config.getPluginValue(self.name, 'notifyOffline', '1'))
        self.notifyNewMail = int(self.config.getPluginValue(self.name, 'notifyMail', '1'))
        self.notifyTyping = int(self.config.getPluginValue(self.name, 'typing', '0'))
        self.notifyFTInvite = int(self.config.getPluginValue(self.name, 'notifyFTInvite', '0'))
        self.notifyFTFinished = int(self.config.getPluginValue(self.name, 'notifyFTFinished', '0'))
        self.notifyNewMsg = int(self.config.getPluginValue(self.name, 'notifyMessage', '1'))
        #self.notifyStarted = int(self.config.getPluginValue(self.name, 'notifyStarted', '0'))
        self.notifyBusy = int(self.config.getPluginValue(self.name, 'notifyBusy', '0'))
        self.showNotification = int(self.config.getPluginValue(self.name, 'showNotification', '0'))

        #Disable Notification on Systray
        if not TrayIcon.disabled:
            self.checkBox = gtk.CheckMenuItem(_('Disable Notifications'))
            self.checkBox.set_active(self.showNotification)
            self.checkBox.connect('activate', self.on_showNotification_activate)
            self.tray = self.controller.trayIcon.getNotifyObject()
        self.pixbuf = self.controller.theme.getImage('userPanel')

        self.parser = controller.unifiedParser
        self.contacts = controller.contacts  # ref..

        self.notifications = []

        # callbacks ids
        self.onlineId = None
        self.offlineId = None
        self.newMsgId = None
        self.offMsgId = None
        self.typingId = None
        self.fTInviteId = None
        self.fTFinishedId = None
        self.newMailId = None
        self.initMailId = None
        if Plugin.module_require(self.require, globals()):
            global error
            ERROR = _('there was a problem initializing the pynotify module')

    def on_showNotification_activate(self, *args):
        self.showNotification = self.checkBox.get_active()
        self.config.setPluginValue(self.name, 'showNotification', str(int(self.showNotification)))

    def connect_onoff(self, *args):
        self.onlineId = self.connect('user-online', self.online)
        self.offlineId = self.connect('user-offline', self.offline)
        if self.notifyId is not None: self.disconnect(self.notifyId)
        self.notifyId = None
    
    def start(self):
        '''start the plugin'''
        global ERROR

        if not ERROR and not pynotify.init('emesene'):
            ERROR = _('there was a problem initializing the pynotify module')

        self.notifyId = None
        self.onlineId = None
        self.offlineId = None
        if self.msn.canNotify:
            self.connect_onoff()
        else:
            self.notifyId = self.connect('enable-notifications', self.connect_onoff)
        self.newMsgId = self.connect('switchboard::message', self.newMsg)
        self.offMsgId = self.connect('offline-message-received', self.offMsg)
        self.typingId = self.connect('switchboard::typing', self.receiveTyping)
        self.fTInviteId = self.connect('new-file-transfer', self.notifyFileTransferInvite)
        self.fTFinishedId = self.connect('finished-file-transfer', self.notifyFileTransferFinished)
        self.newMailId = self.connect('new-mail-notification', self.newMail)
        self.initMailId = self.connect('initial-mail-notification', \
                self.initMail)
        self.enabled = True
        self.updateTrayIconMenuList();


    def stop(self):
        ''' stop the plugin '''

        # closes remaining notifications
        for i in self.notifications:
            i.close()

        self.notifications = []

        if self.onlineId is not None: self.disconnect(self.onlineId)
        if self.offlineId is not None: self.disconnect(self.offlineId)
        if self.notifyId is not None: self.disconnect(self.notifyId)
        self.disconnect(self.newMsgId)
        self.disconnect(self.offMsgId)
        self.disconnect(self.typingId)
        self.disconnect(self.fTInviteId)
        self.disconnect(self.fTFinishedId)
        self.disconnect(self.newMailId)
        self.disconnect(self.initMailId)
        self.enabled = False
        if not TrayIcon.disabled:
            self.controller.trayIcon.menu.remove(self.checkBox);
            self.controller.trayIcon.menu.show_all()
            self.controller.trayIcon.update(self.controller.msn.status)

    def check(self):
        '''check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> ( True , 'some message' )
        else -> ( False , 'error message' )'''
        global ERROR

        if ERROR != '':
            return (False, ERROR)

        return (True, 'Ok')

    def updateTrayIconMenuList(self):
     	if not TrayIcon.disabled:
     		#Generates the Systray list with the new feature
     		#when the TrayIcon is enabled
            self.controller.trayIcon.menu.prepend(self.checkBox)
            self.controller.trayIcon.menu.show_all()
            self.controller.trayIcon.update(self.controller.msn.status)
        
    def configure(self):
        '''display a configuration dialog'''
        l = []

        l.append(Plugin.Option('notifyOnline', bool, \
                _('Notify when someone comes online'), '', self.config.\
                getPluginValue(self.name, 'notifyOnline', '1') == '1'))
        l.append(Plugin.Option('notifyOffline', bool, \
                _('Notify when someone goes offline'), '', self.config.\
                getPluginValue(self.name, 'notifyOffline', '1') == '1'))
        l.append(Plugin.Option('notifyMail', bool, \
                _('Notify when receiving an email'), '', self.config.\
                getPluginValue(self.name, 'notifyMail', '1') == '1'))
        l.append(Plugin.Option('typing', bool, \
                _('Notify when someone starts typing'), '', self.config.\
                getPluginValue(self.name, 'typing', '1') == '1'))
        l.append(Plugin.Option('notifyFTInvite', bool, \
                _('Notify when someone starts a file transfer'), '', self.config.\
                getPluginValue(self.name, 'notifyFTInvite', '1') == '1'))
        l.append(Plugin.Option('notifyFTFinished', bool, \
                _('Notify when a file transfer finish'), '', self.config.\
                getPluginValue(self.name, 'notifyFTFinished', '1') == '1'))
        l.append(Plugin.Option('notifyMessage', bool, \
                _('Notify when receiving a message'), '', self.config.\
                getPluginValue(self.name, 'notifyMessage', '1') == '1'))
        #l.append(Plugin.Option('notifyStarted', bool, \
        #        _('Don`t notify if conversation is started'), '', self.config.\
        #        getPluginValue(self.name, 'notifyStarted', '1') == '1'))
        l.append(Plugin.Option('notifyBusy', bool, \
                _('Disable notifications when busy'), '', self.config.\
                getPluginValue(self.name, 'notifyBusy', '1') == '1'))
        
        response = Plugin.ConfigWindow(_('Config LibNotify Plugin'), l).run()
        if response != None:
            def check(event):
                if response.has_key(event):
                    self.config.setPluginValue(self.name, event, \
                            str(int(response[event].value)))

            check('notifyOnline')

            if response.has_key('notifyOffline'):
                self.config.setPluginValue(self.name, 'notifyOffline', \
                    str(int(response['notifyOffline'].value)))
            if response.has_key('notifyMail'):
                self.config.setPluginValue(self.name, 'notifyMail', \
                    str(int(response['notifyMail'].value)))
            if response.has_key('typing'):
                self.config.setPluginValue(self.name, 'typing', \
                    str(int(response['typing'].value)))
            if response.has_key('notifyFTInvite'):
                self.config.setPluginValue(self.name, 'notifyFTInvite', \
                    str(int(response['notifyFTInvite'].value)))
            if response.has_key('notifyFTFinished'):
                self.config.setPluginValue(self.name, 'notifyFTFinished', \
                    str(int(response['notifyFTFinished'].value)))
            if response.has_key('notifyMessage'):
                self.config.setPluginValue(self.name, 'notifyMessage', \
                    str(int(response['notifyMessage'].value)))
            #if response.has_key('notifyStarted'):
            #    self.config.setPluginValue(self.name, 'notifyStarted', \
            #        str(int(response['notifyStarted'].value)))
            if response.has_key('notifyBusy'):
                self.config.setPluginValue(self.name, 'notifyBusy', \
                    str(int(response['notifyBusy'].value)))
            
        self.notifyOnline = (self.config.getPluginValue \
                (self.name, 'notifyOnline', '1') == '1')
        self.notifyOffline = (self.config.getPluginValue \
                (self.name, 'notifyOffline', '1') == '1')
        self.notifyNewMail = (self.config.getPluginValue \
                (self.name, 'notifyMail', '1') == '1')
        self.notifyTyping = (self.config.getPluginValue \
                (self.name, 'typing', '1') == '1')
        self.notifyFTInvite = (self.config.getPluginValue \
                (self.name, 'notifyFTInvite', '1') == '1')
        self.notifyFTFinished = (self.config.getPluginValue \
                (self.name, 'notifyFTFinished', '1') == '1')
        self.notifyNewMsg = (self.config.getPluginValue \
                (self.name, 'notifyMessage', '1') == '1')
        #self.notifyStarted = (self.config.getPluginValue \
        #        (self.name, 'notifyStarted', '1') == '1')
        self.notifyBusy = (self.config.getPluginValue \
                (self.name, 'notifyBusy', '1') == '1')
        self.updateTrayIconMenuList();
        return True

    def notifyEnabled(self, contact = None):
        '''checks if notifications are enabled'''
        if not self.enabled:
            return False
        if self.notifyBusy and self.msn.status == 'BSY':
            return False
        if self.showNotification:
            return False
        if contact != None:
            if self.contacts.get_blocked(contact):
                return False
        return True

    def notify(self, contact, title, text, execute = '', data = None):

        notification = pynotify.Notification(title, text)#, attach = self.tray)
        # both "append" and "x-canonical-append" work fine.
        notification.set_hint_string ("x-canonical-append", "allowed")

        if contact != '':
            if self.controller.theme.hasUserDisplayPicture(contact):
                self.pixbuf = self.controller.theme.getUserDisplayPicture( \
                    contact, 48, 48)

        notification.set_icon_from_pixbuf(self.pixbuf)

        if contact != '':
            self.pixbuf = self.controller.theme.getImage('userPanel')


        if not TrayIcon.disabled and \
           isinstance(self.controller.trayIcon.tray, gtk.StatusIcon):
            tray = self.controller.trayIcon.tray
            try:
                notification.attach_to_status_icon(tray)
                #notification.set_hint("x", tray.get_geometry()[1].x)
                #notification.set_hint("y", tray.get_geometry()[1].y)
            except:
                print "cant set geometry hints on libnotify plugin"

        try:
            notification.show()
        except gobject.GError:
            print "can't display notification" # TODO, retry?
            return
        notification.connect('closed', self.on_notify_close)
        self.notifications.append(notification)

    def getNickPM(self, email, name = ''):
        ''' returns the nick and pm of the contact '''

        contact = self.msn.contactManager.getContact(email)  # :(:(

        if not self.contacts.exists(email):
            text = name + ' &lt;' + email + '&gt;'
        else:
            # @roger, this is ugly
            nick = self.parser.getParser(
                self.contacts.get_display_name(email)).get()
            text = unescape(nick)

        return contact, text

    def online(self, msnp, email, oldStatus):
        '''called when someone gets online'''

        if not (self.notifyOnline and self.notifyEnabled(email)):
            return

        if oldStatus != 'FLN':
            return

        contact, text = self.getNickPM(email)
        status = _("is online")
        self.notify(contact, text, status, 'conversation', (email, None))

    def offline(self, msnp, email):
        '''called when someone gets offline'''

        if not (self.notifyOffline and self.notifyEnabled(email)):
            return

        contact, text = self.getNickPM(email)
        status = _("is offline")
        self.notify(contact, text, status)

    def newMsg(self, msn, switchboard, signal, args, stamp=None):

        '''called when someone sent a message'''

        email, nick, text, format, charset, p4c = args
        if not (self.notifyNewMsg and self.notifyEnabled(email)):
            return
        result = self.controller.conversationManager.getOpenConversation(email)
        if result != None:
            #if self.notifyStarted:
            #    return

            window, conversation = result
            windowFocus = window.is_active()
            tabFocus = (window.conversation == conversation)
            if windowFocus and tabFocus:
                return

            contact, title = self.getNickPM(email)
            status = _("has sent a message")
            self.notify(contact, title, text, 'conversation', (email, None))

    def offMsg(self, msnp, oim):
        '''called when someone sent an offline message'''
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

        contact, title = self.getNickPM(email)
        status = _("sent an offline message")
        self.notify(contact, title, status, 'conversation', (email, None))

    def receiveTyping(self, msn, switchboard, signal, args):
        '''called when someone starts typing'''
        email = args[0]

        if not (self.notifyTyping and self.notifyEnabled(email)):
            return

        if self.controller.conversationManager.getOpenConversation \
                (email, switchboard) != None:
            return

        contact, title = self.getNickPM(email)
        status = _('starts typing...')
        self.notify(contact, title, status, 'conversation', \
                (email, switchboard))

    def notifyFileTransferInvite(self, msnp,email,fileName):
        '''called when someone starts a file transfer'''
        if not (self.notifyFTInvite and self.notifyEnabled):
            return

        contact, text = self.getNickPM(email)
        title = _('File transfer petition')
        content = text + _(' wants to share ') + fileName
        self.notify(contact, title, content, 'conversation', (email, None))

    def notifyFileTransferFinished(self, msnp, email,fileName):
        '''called when someone starts a file transfer'''
        if not (self.notifyFTFinished and self.notifyEnabled):
            return

        contact, text = self.getNickPM(email)
        title = _('File transfer complete')
        content = fileName + _(' has been completly transfered')
        self.notify(contact, title, content, 'conversation', (email, None))

    def newMail(self, msnp, From, FromAddr, Subject, MessageURL, PostURL, id):
        ''' called when receiving mail '''

        if not (self.notifyNewMail and self.notifyEnabled(FromAddr)):
            return

        contact, text = self.getNickPM(FromAddr, From)
        text = _('From: ') + text + '\n' + _('Subj: ') + escape(Subject) \
                + '\n\n<span foreground="#AAAAAA">emesene</span>'

        self.notify(contact, _('New email'), text, 'mail', \
                (MessageURL, PostURL, id))

    def initMail(self, msnp):
        if self.notifyNewMail:
            unread = self.controller.getUnreadMails()

            try:
                unread = int(unread)
            except ValueError, TypeError:
                unread = 0

            if unread > 0:
                if unread == 1:
                    s = ''
                else:
                    s = 's'
                self.notify('', "emesene", \
                        _('You have %(num)i unread message%(s)s') % \
                        {'num': unread, 's': s}, 'mail', (None, None, '2'))

    def on_notify_close(self, n, fedora_wtf=None):
        if n in self.notifications:
            self.notifications.remove(n)
