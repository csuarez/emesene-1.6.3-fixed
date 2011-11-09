# -*- coding: utf-8 -*-

import Plugin
import gtk
import TrayIcon
import PluginManager
from Parser import TAGS_NONE

DIALOG_TYPE_SET = 0
DIALOG_TYPE_CONFIG = 1


class MainClass(Plugin.Plugin):
    '''
    Main class of the plugin. It listens for self-status-changed event,
    connects to unifiedParser, and provide a configuration dialog.
    '''

    description = _('Hide Emesene with a keyboard shortcut (CTRL + SPACE)')
    authors = {'Daniele S.' : 'oppifjellet@gmail.com',
               'arielj' : 'arieljuod@gmail.com'}
    website = ''
    displayName = _('Ninja Mode (Anti Boss Plugin)')
    name = 'NinjaMode'
    def __init__(self, controller, msn):
        '''Constructor'''

        Plugin.Plugin.__init__(self, controller, msn)
        self.config = controller.config
        self.config.readPluginConfig(self.name)
        self.antiBoss = AntiBoss(controller, msn, self.config, self)
        self.enabled = False

    def start(self):
        print "AntiBoss started"
        '''self.controller.emit('preferences-changed')  '''
        self.convOpen = self.controller.conversationManager.\
                  connect_after('new-conversation-ui', self.newConversation)

        self.convClose = self.controller.conversationManager.connect(\
                             'close-conversation-ui',self.closeConversation)

        self.mainActv = self.controller.mainWindow.connect(\
                             'show', self.winRestored)

        self.receivemessageId = self.controller.conversationManager.connect_after( \
                             'receive-message', self.onReceivedMessage)

        self.antiBoss.hookKeyboard(self.controller.mainWindow)

        for conversation in self.getOpenConversations():
            self.antiBoss.hookKeyboard(conversation.parentConversationWindow)

        self.enabled = True

    def stop(self):
        print "AntiBoss stopped";
        self.antiBoss.unhookKeyboard(self.controller.mainWindow)

        for conversation in self.getOpenConversations():
            self.antiBoss.unhookKeyboard(conversation.parentConversationWindow)

        # clean up everything
        self.controller.conversationManager.disconnect(self.convOpen)
        self.controller.conversationManager.disconnect(self.convClose)
        self.controller.conversationManager.disconnect(self.receivemessageId)
        self.controller.mainWindow.disconnect(self.mainActv)

        self.enabled = False

    def check(self):
        if TrayIcon.disabled:
            return (False, _("TrayIcon disabled"))
        return (True, 'Ok')

    def newConversation(self, conversationManager=None, conversation=None, window=None):
        self.antiBoss.hookKeyboard(window)
        if self.antiBoss.ninjamode:
            window.hide()

    def closeConversation(self, conversationManager=None, conversation=None, window=None):
        self.antiBoss.unhookKeyboard(window)

    def winRestored(self, *args):
        self.antiBoss.restore()

    def onReceivedMessage(self, cm, conversation, mail, nick, message, format, charset, p4c):
        if self.antiBoss.ninjamode:
            conversation.parentConversationWindow.hide()

class AntiBoss:
    '''
    This is the core class of the plugin. It gives methods to parse the custom
    statuses of users, to change or remove custom status of current user, and
    to save and remove custom statuses.
    '''

    def __init__ (self, controller, msn, config, plugin):
        '''Constructor'''
        self.controller = controller
        self.msn = msn
        self.config = config
        self.plugin = plugin
        self.ninjamode = False
        # Create an accelerator group
        self.ag = gtk.AccelGroup()
        self.ag.connect_group(gtk.keysyms.space, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.accelRaised)

    def hookKeyboard(self, window):
        # Add the accelerator group to the window
        window.add_accel_group(self.ag)

    def unhookKeyboard(self, window):
        window.remove_accel_group(self.ag)

    def accelRaised(self, accel_group, acceleratable, keyval, modifier):

        #hack: disable Custom Status Plugin
        self.wasCustomStatusActive = self.controller.pluginManager.stopPlugin('CustomStatus')

        #hack: disable Old Notification Plugin
        self.wasOldNotificationActive = self.controller.pluginManager.stopPlugin('OldNotifications')

        #hack: disable New Notification Plugin
        self.wasNotificationActive = self.controller.pluginManager.stopPlugin('NotifyOsdImproved')

        #hack: disable TrayIcon in order to block updates on status change
        self.has_tray = not TrayIcon.disabled
        if self.has_tray:
            TrayIcon.disabled = True

        self.oldSoundConfig = self.config.user['enableSounds'] 
        self.config.user['enableSounds'] = False
        self.oldHideNewConfig = self.config.user['hideNewWindow']
        self.config.user['hideNewWindow'] = True

        # remember the old status to restore later
        self.oldStatus = self.msn.status
        self.oldTip = self.controller.trayIcon.tray.set_tooltip('x)')
        if self.msn.connected and self.msn.status != 'BSY' and self.msn.status != 'HDN' and self.msn.status != 'FLN':
            self.msn.changeStatus('BSY')

        # change the tray image
        pixbuf = self.controller.theme.getImage('brush-small')
        self.controller.trayIcon.tray.set_from_pixbuf( pixbuf )

        # nascondi anche tutte le conversazioni aperte
        for conversation in self.plugin.getOpenConversations():
            if conversation.parentConversationWindow.get_property("visible"):
                conversation.parentConversationWindow.hide()

        # restore the trayicon
        if self.has_tray:
            TrayIcon.disabled = False

        # hides or closes the application
        self.controller.mainWindow.hideOrClose()

        self.ninjamode = True

    def restore(self):
        if self.ninjamode:
            #if self.msn.status != self.oldStatus:
            self.msn.changeStatus(self.oldStatus)
            for conversation in self.plugin.getOpenConversations():
                conversation.parentConversationWindow.present()

            #restore Old Notifications Plugin
            if self.wasOldNotificationActive:
                self.controller.pluginManager.startPlugin('OldNotifications')

            #restore New Notifications Plugin
            if self.wasNotificationActive:
                self.controller.pluginManager.startPlugin('NotifyOsdImproved')

            #restore CustomStatus Plugin
            if self.wasCustomStatusActive:
                self.controller.pluginManager.startPlugin('CustomStatus')

            self.config.user['enableSounds'] = self.oldSoundConfig
            self.config.user['hideNewWindow'] = self.oldHideNewConfig

            self.ninjamode = False

    def loadSavedHotkey(self):
        '''Method that loads saved accelerator.'''

        accel = self.config.getPluginValue(self.name,\
                                                'accelerator_group', 0)
        return accel

    def saveHotkey(self, accel):
        '''Method that saves the custom statuses saved list to config file.'''

        # We need to update custom statuses count
        self.config.setPluginValue(self.name, 'accelerator_group', accel)

