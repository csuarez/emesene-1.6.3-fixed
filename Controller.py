#!/usr/bin/env python
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
# needed for osx #
import pygtk
pygtk.require('2.0')
##################
import gtk
import sys
import time
import thread
import gobject
import gettext
import weakref
import traceback

import paths

if os.path.exists("default.mo"):
    gettext.GNUTranslations(open("default.mo")).install()
elif os.path.exists(paths.LANG_PATH):
    gettext.install('emesene', paths.LANG_PATH)
else:
    gettext.install('emesene')

import Theme
import Avatar
import Config
import desktop
import TrayIcon
import MainWindow
import StatusMenu
import SlashCommands
import Sound
import PluginManager
import ConversationManager
import ConversationLayoutManager
from Parser import UnifiedParser
from CustomEmoticons import CustomEmoticons

import emesenelib.common
from emesenelib import core
from emesenelib import Socket
from emesenelib import Hotmail

import stock
import dialog
import abstract.stock as stock
import GroupManager
import ContactManager
from AvatarHistory import AvatarHistoryViewer

from SingleInstance import SingleInstance

SERVER_HOST = 'messenger.hotmail.com'

class Controller(gobject.GObject):
    '''The Controller class concentrate all the logic of the program
    leaving the other classes to only implement the GUI.
    All the classes with GUI should receive a Controller instance to
    be able to do things.'''

    # suprise, most of these signals should be refactored
    __gsignals__ = {
        #'font-changed', font, bold, italic, pangoDesc.get_size() / pango.SCALE
        'font-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN,
            gobject.TYPE_INT)),
        #'color-changed', '#%02X%02X%02X' % (red, green, blue)
        'color-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_STRING,)),
        'input-format-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,)),
        'avatar-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ()),
        'preferences-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ()),
        'usermenu-item-add' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,)),
        
        'message-read' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),
    }

    def __init__(self, username, minimized, leakdebug, iconified, badroot, singleinstance):
        '''Constructor'''
        gobject.GObject.__init__(self)

        self.NAME = 'emesene'
        self.VERSION = '1.6.3 - "Uberlândia"'
        self.COPYRIGHT = 'Luis Mariano Guerra, dx, C10uD, arielj'
        self.COMMENT = _('A client for the WLM%s network') % u'\u2122'
        self.LICENSE_FALLBACK = 'GNU General Public License'
        self.WEBSITE = 'http://www.emesene.org'
        self.BUGTRACKER = 'http://forum.emesene.org/index.php/board,19.0.html'
        self.AUTHORS = [
            'Luis Mariano \'wariano\' Guerra (emesene and emesenelib)', \
            'dequis \'dx\' (emesene and emesenelib)', \
            'Horacio Duran (emesene and emesenelib)', \
            'Alberto Talavera (emesene)', \
            'Linan Wang (MsnOIM)', \
            'Roberto Salas & Jakub Steiner (tango theme)', \
            'Vinicius Depizzol (default theme)', \
            'Yguaratã C. Cavalcanti (emesene)', \
            'Roger \'roger\' Duran (emesene)', \
            'Alen \'alencool\' (emesene and cairo wizzard :P)', \
            'Mattia \'MaTz\' Pini (emesene)', \
            '\'mg\' (emesene)', \
            'Jan \'jandem\' de Mooij (emesene and emesenelib)', \
            'j0hn \'juan\' (emesene)', \
            'Luis \'JoinTheHell\' Nell (emesene)', \
            'nopersona (in the margins theme)', \
            'Stéphane \'kjir\' Bisinger  (webcam)', \
            'Kevin Campbell (pyisf)', \
            'Riccardo \'C10uD\' (emesene)', \
            'Giuseppe Bagnato (proxy)', \
            'Orfeo \'Otacon\' (emesene)', \
            'Davide \'Boyska\' (plugins)', \
            '\'x1sc0\' (emesene)', \
            'Nicolas \'nicolaide\' Espina Tacchetti (emesene)', \
            'Emilio \'pochu\' Pozuelo Monfort (debian)', \
            'Bartłomiej Jerzy \'bjfs\' Stobiecki (ppa)', \
            'Pablo \'pablo\' Mazzini (emesene and emesenelib)', \
            'scyx (emesene)', \
            'arielj (emesene)', \
            'Victor C. (gnome-colors theme)', \
            'GrinningArmor (emesene)', \
            'x-warrior (emesene)', \
            'Tom \'ukblackknight\' (emesene)', \
            'Stefano \'Cando\' Candori (emesene)', \
            'All the fantastic emesene community (all)', \
            ]
        
        # this statuses are not available in wlm anymore
        self.bad_statuses = [ 'BRB', 'PHN', 'LUN', 'FLN' ]

        self.status_ordered = [
            [ 'NLN', 'AWY', 'BSY', 'BRB', 'PHN', 'LUN', 'HDN', 'IDL', 'FLN' ],

            [ 'online', 'away', 'busy', 'away', 'busy',
             'away', 'invisible', 'idle', 'offline' ],

            [ _('Online'), _('Away'), _('Busy'), _('Away'),
             _('Busy'), _('Away'), _('Invisible'),
             _('Idle'), _('Offline') ],

            [ _('_Online'), _('_Away'), _('_Busy'), _('_Away'),
             _('_Busy'), _('_Away'), _('_Invisible'),
             _('I_dle'), _('O_ffline') ]
        ]

        self.connected = False
        self.userEmail = None
        self.userStatus = None
        self.reconnectTimerId = None

        self.config = Config.Config()
        self.config.connect('change::debug', self.updateDebug)
        self.config.connect('change::binary', self.updateDebug)
        desktop.override = self.config.glob['overrideDesktop']

        self.theme = Theme.Theme(self.config, 'default', 'default')
        self.mainWindow = MainWindow.MainWindow(self)
        self.mainWindow.set_wmclass('emesene', 'emesene')
        self.gtk_screen = self.mainWindow.get_screen()

        use_rgba_colormap = (gtk.gtk_version >= (2, 10, 0) and
                             self.config.glob['rgbaColormap'])

        if use_rgba_colormap:
            colormap = self.gtk_screen.get_rgba_colormap()
            if colormap:
                gtk.widget_set_default_colormap(colormap)

        self.mainWindow.realize()
        # ####################################### #
        # we use this crap in our awesome bars :D #
        # this is assigned as soon as our colors  #
        # are ready in                            #
        # mainwindow.userlist.tooltips            #
        self.tooltipColor = None
        self.niceBarWarningColor=gtk.gdk.Color(57600,23040,19712)
        # ####################################### #
        self.widget_style = self.mainWindow.get_style()
        self.unifiedParser = UnifiedParser(self.theme)

        self.conversationLayoutManager = \
            ConversationLayoutManager.ConversationLayoutManager(self)
        self.conversationManager = \
            ConversationManager.ConversationManager(self)

        self.contacts = ContactManager.ContactManager(dialog, None, None)
        self.groups = GroupManager.GroupManager(dialog, None)

        # "with" would be interesting here
        if use_rgba_colormap:
            gtk.widget_push_colormap(self.gtk_screen.get_rgb_colormap())
        if not TrayIcon.disabled:
            self.trayIcon = TrayIcon.TrayIcon(self)
        if use_rgba_colormap:
            gtk.widget_pop_colormap()

        if TrayIcon.disabled or not (minimized or self.config.glob['startup'] == 'minimize'):
            if iconified or self.config.glob['startup'] == 'iconify' and not self.config.glob['disableTrayIcon']:
                self.mainWindow.iconify()
            else:
                self.mainWindow.show()
        if minimized or self.config.glob['startup'] == 'minimize':
            self.mainWindow.show()
            self.mainWindow.iconify()

        self.pluginManager = None

        gtk.gdk.set_program_class('emesene')
        gtk.window_set_default_icon_list(\
            self.theme.getImage('icon16'), self.theme.getImage('icon32'),
            self.theme.getImage('icon48'), self.theme.getImage('icon96'))

        self.msn = None
        self.lastILN = 0
        self.pendingAvatars = {}

        self.trayDisconnect = None
        self.traySeparator = None
        self.trayStatusMenu = None

        self.avatar = None
        self.cancel = False
        self.reconnecting = False
        self.preference_open = False
        self.addBuddy = None

        self.leakdebug = leakdebug

        if username in self.mainWindow.login.users.getUsers():
            user = username
            self.mainWindow.login.getPreferences(user)
            pwd = self.mainWindow.login.getPass()
            status = self.mainWindow.login.getStatus()
        elif self.config.glob['autoLogin']:
            user = self.mainWindow.login.getUser()
            pwd = self.mainWindow.login.getPass()
            status = self.mainWindow.login.getStatus()
        else:
            user = ''
            pwd = ''

        if user != '' and pwd != '':
            self.login(user, pwd, status)

    def login(self, user, password, status):
        '''do the login'''

        self.reconnecting = (self.mainWindow.currentInterface == 'reconnect')
        self.cancel = False
        self.userEmail = user
        self.userStatus = status
        self.mainWindow.buildInterface('loading')
        self.config.setCurrentUser(user)

        if not self.config.glob['debug']:
            print "If you are reading this, you may want to enable debug"
            print "It's the first option in the advanced page in preferences"

        server = SERVER_HOST
        proxy = None

        if self.config.glob['useProxy']:
            proxy = Socket.Proxy(self.config.glob['proxyHost'], \
                self.config.glob['proxyPort'], \
                self.config.glob['proxyUsername'], \
                self.config.glob['proxyPassword'])
        else:
            if self.config.glob['httpMethod']:
                proxy = Socket.Proxy()


        # messenger.hotmail.com
        self.msn = core.Msnp(server, 1863, user, password,\
             self.config.getUserConfigPath(), proxy, \
             self.config.user['receiveP4context'], self.config) # ugly, but i'm lazy
                    
        self.msn.setDebug(self.config.glob['debug'],
            self.config.glob['binary'])

        self.msn.connect('login-error', self.on_login_error, password)
        self.msn.connect('login-successful', self.on_login_successful)
        gobject.timeout_add(2000, self.trayicon_effect)

        self.contacts = ContactManager.ContactManager(
                                dialog, self.msn, self.userEmail)
        self.groups = GroupManager.GroupManager(
                                dialog, self.msn)

        self.msn.login()

    def trayicon_effect(self):
        '''Create an animation effect in the trayicon'''
        if not TrayIcon.disabled and (self.msn and not self.msn.connected):
            if self.trayIcon.status == 'login':
                self.trayIcon.update('disconnected')
            else:
                self.trayIcon.update('login')
        else:
            return False

    def on_login_error(self, msn, message, password):
        '''Callback to login-error signal'''
        if not self.msn:
            return False
        if not self.reconnecting:
            if self.config.glob['autoLogin']:
                self.autoReconnect(self.userEmail, password, self.userStatus)
            else:    
                text = _('Error during login, please retry') + \
                '\n(' + message + ')'
                self.goToLoginWindow()
                self.mainWindow.showNiceBar(text,self.niceBarWarningColor, gtk.STOCK_DIALOG_WARNING)
        else:
            self.autoReconnect(self.userEmail, password, self.userStatus)

    def cancelLogin(self):
        try:
            self.msn.logout()
        except Exception, e:
            print "Exception at logout", e
        self.goToLoginWindow()
        if self.reconnectTimerId is not None:
            gobject.source_remove(self.reconnectTimerId)
            self.reconnectTimerId = None

    def goToLoginWindow(self):
        self.config.setCurrentUser('')
        self.mainWindow.buildInterface('login')
        self.msn = None
        self.pluginManager = None

    def on_login_successful(self, msn):
        if self.reconnectTimerId is not None:
            gobject.source_remove(self.reconnectTimerId)
            self.reconnectTimerId = None
        self.connected = True
        self.pendingAvatars = {}
        self.idleTimeout = 0

        if not (self.theme.setTheme(self.config.user['theme'],
                                    self.config.user['smallIcons']) and
                self.theme.smilies.setTheme(self.config.user['smilieTheme'])):
            self.config.user['theme'] = 'default'
            self.config.user['smilieTheme'] = 'default'
            dialog.error(_("Error loading theme, falling back to default"))
        else:
            self.mainWindow.rebuild()
            if self.trayStatusMenu:
                self.trayStatusMenu.set_submenu(StatusMenu.StatusMenu(self))
                self.trayIcon.menu.show_all()
                self.trayIcon.update(self.msn.status)

        self.msn.changeStatus(self.userStatus)

        self.msn.connect('disconnected', self.disconnected)
        self.msn.connect('connection-closed', self.on_connection_closed)
        self.msn.connect('error', self.on_msnp_error)
        self.msn.connect('exception', self.on_msnp_exception)
        sys.excepthook = self.except_hook_dialog

        # FIXME: strange issue with avatars
        self.changeAvatar(self.config.user['avatarPath'],initial=True)
        self.mainWindow.buildInterface('userlist')
        self.changeAvatar(self.config.user['avatarPath'],initial=True)
        
        layout = self.config.user['conversationLayout']
        if not self.conversationLayoutManager.load(layout):
            self.conversationLayoutManager.setDefault()

        # menu items only available when connected
        if not self.trayStatusMenu and not TrayIcon.disabled:
            statusMenuItem = gtk.MenuItem(_('_Status'))
            statusMenu = StatusMenu.StatusMenu(self)
            statusMenuItem.set_submenu(statusMenu)
            separator = gtk.SeparatorMenuItem()
            secondSeparator = gtk.SeparatorMenuItem()
            plugins = self.mainWindow.menu.newImageMenuItem('P_lugins',gtk.STOCK_EXECUTE)
            plugins.connect('activate', self.mainWindow.menu.on_plugin_activate)
            preferences = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
            preferences.connect('activate', self.mainWindow.menu.on_preferences_activate)
            about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
            about.connect('activate', self.mainWindow.menu.on_about_activate)
            disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
            disconnect.connect('activate', self.on_tray_disconnect)

            self.trayDisconnect = disconnect
            self.traySeparator = separator
            self.trayPlugins = plugins
            self.trayPreferences = preferences
            self.trayAbout = about
            self.trayStatusMenu = statusMenuItem
            self.traySecondSeparator = secondSeparator

        #Slash Command Handler
        self.Slash = SlashCommands.SlashCommands(self)

        # add here
        if self.config.user['enableSounds'] == True:
            self.sound = Sound.SoundHandler(self, self.msn, action='start')
        else:
            self.sound = Sound.SoundHandler(self, self.msn, action=None)

        if not TrayIcon.disabled:
            # REMEMBER to remove them when disconnect
            self.trayIcon.menu.prepend(self.trayDisconnect)
            self.trayIcon.menu.prepend(self.traySecondSeparator)
            self.trayIcon.menu.prepend(self.trayAbout)
            self.trayIcon.menu.prepend(self.trayPreferences)
            self.trayIcon.menu.prepend(self.trayPlugins)
            self.trayIcon.menu.prepend(self.traySeparator)
            self.trayIcon.menu.prepend(self.trayStatusMenu)
            self.trayIcon.menu.show_all()
            self.trayIcon.update(self.msn.status)
            
        self.pluginManager = PluginManager.PluginManager(self)
        gobject.idle_add(self.pluginManager.startActivePlugins)

        self.msn.connect('initial-status-change', self.onInitialStatusChange)
        self.msn.connect('display-picture-changed',
            self.on_display_picture_changed)
        self.msn.connect('new-conversation', self.newConversation)
        self.msn.connect('user-attr-changed', self.on_user_attr_changed)
        self.msn.connect('self-status-changed', self.on_self_status_changed)
        self.msn.connect('self-dp-changed', self.on_change_avatar)
        self.msn.connect('group-attr-changed', self.on_group_attr_changed)
        self.msn.connect('add-notification', self.addNotification)
        self.msn.connect('user-list-change', self.refreshUserList)
        self.msn.connect('user-disconnected', self.userDisconnected)
        self.msn.connect('connection-problem', self.connectionProblem)

        self.msn.connect('offline-message-waiting', self.offlineMessageWaiting)
        self.msn.connect('offline-message-received',
            self.offlineMessageReceived)

        self.msn.connect('send-message-error', self.messageError)
        self.msn.connect('msnobj-changed', self.msnobjChanged)

        self.hotmail = Hotmail.Hotmail(self.msn, self.config)
        self.customEmoticons = CustomEmoticons(self.config, self)

        self.conversationManager.handleLogin(self.userEmail)

        gobject.idle_add(self.checkPending)
        self.cancel = False
        self.reconnecting = False

    def disconnected(self, msnp):
        '''called when a error occurs and we cant keep connected.'''
        self.logout(False, True)

    def on_connection_closed(self, msnp):
        '''called when a connection error happens'''
        self.logout(False, True)

    def on_msnp_error(self, msnp, error, description):
        '''called when there is an error during some msnp operation'''
        dialog.error(description)

    def on_msnp_exception(self, msnp, exception):
        '''called when there is an error in msn.process'''
        lines = traceback.format_exception(*exception)

        message = _('%(1)sException%(2)s' \
            'You are using %(name)s %(version)s so you\'re free to complain here:\n%(bugtracker)s\n' \
            'Check already existing tickets for duplicates first, please.'\
            % {'1': '<span weight="bold" size="larger">', '2': '\n</span>', \
               'name': self.NAME, 'version': self.VERSION, 'bugtracker': self.BUGTRACKER})

        for line in lines:
            message += '\n' + emesenelib.common.escape(line)

        dialog.exception(message)

    def except_hook_dialog(self, *exception):
        '''replaces sys.excepthook displaying a dialog
        this is only for unhandled exceptions'''

        traceback.print_exception(*exception)
        if exception[0] != KeyboardInterrupt:
            gobject.idle_add(self.on_msnp_exception, None, exception)

    def on_user_attr_changed(self, userlist, contact):
        self.mainWindow.userList.updateContact(contact)

    def on_display_picture_changed(self, msnp, switchboard, msnobj, email):
        contact = self.getContact(email)
        if contact:
            self.mainWindow.userList.updateContact(contact)
        else:
            debug('contact not found on contact list!')

    def on_group_attr_changed(self, msnp, oldGroup, newGroup):
        self.mainWindow.userList.updateGroup(oldGroup, newGroup)
        # canhastestsirkthxbai
        # self.refreshUserList()

    def removeGroup(self, group):
        #asks the user before removing the group
        def remove_cb(response, group):
            if response == stock.YES:
                if not isinstance(group, basestring):
                    group = group.name
                self.groups.remove(group)

        message = _('Are you sure you want to remove this group?')
        dialog.yes_no(message,remove_cb, group)

    def autoReconnect(self, user, password, status):
        self.mainWindow.buildInterface('reconnect')
        self.mainWindow.login.setFieldValues(user, password, status)

        self.reconnectAfter = 30
        if self.reconnectTimerId is None:
            self.reconnectTimerId = gobject.timeout_add(1000, \
                self.updateReconnectTimer)

        self.updateReconnectTimer()

    def updateReconnectTimer(self):
        ''' updates reconnect label and launches login if counter is 0 '''
        self.reconnectAfter -= 1
        
        if self.mainWindow.login is not None: #fixes n fucking messages after n failed reconnects
            self.mainWindow.login.setReconnectCounter(self.reconnectAfter)

        if self.reconnectAfter <= 0:
            gobject.source_remove(self.reconnectTimerId)
            self.reconnectTimerId = None
            self.mainWindow.login.login()
            return False
        else:
            return True

    def cancelReconnect(self):
        gobject.source_remove(self.reconnectTimerId)
        self.reconnectTimerId = None
        self.reconnectAfter = None
        self.mainWindow.buildInterface('login')

    def logout(self, closeConversations = True, autoReconnect = False):
        '''do the logout'''

        if closeConversations:
            self.conversationManager.closeAll()
        else:
            self.conversationManager.disableAll()

        if self.pluginManager:
            self.pluginManager.destroy()
        self.pluginManager = None

        # cleanup modules that require msn
        self.hotmail = None
        self.customEmoticons = None
        if self.Slash:
            self.Slash.unregister_slash()
            self.Slash = None

        self.mainWindow.buildInterface('login')

        if autoReconnect and self.msn:
            status = emesenelib.common.reverse_status[self.msn.status]
            self.autoReconnect(self.msn.user, self.msn.password, status)

        self.connected = False
        self.contacts = ContactManager.ContactManager(dialog, None, None)
        self.groups = GroupManager.GroupManager(dialog, None)
        self.groups = None
        self.lastILN = 0

        if not TrayIcon.disabled:
            try:
                self.trayIcon.menu.remove(self.trayDisconnect)
                self.trayIcon.menu.remove(self.traySeparator)
                self.trayIcon.menu.remove(self.traySecondSeparator)
                self.trayIcon.menu.remove(self.trayStatusMenu)
                self.trayIcon.menu.remove(self.trayPlugins)
                self.trayIcon.menu.remove(self.trayPreferences)
                self.trayIcon.menu.remove(self.trayAbout)
                self.trayIcon.menu.remove(self.sound.checkBox)
                self.trayIcon.update('disconnected')
            except:
                pass

        if self.msn:
            self.msn.logout()
            weakmsn = weakref.ref(self.msn)
            self.msn = None
        else:
            return

        if weakmsn():
            print "warning: there are still some references to emesenelib"
            print "references to msn:", sys.getrefcount(weakmsn()) -1
        else:
            print "yay msn got gc'd"

        if self.leakdebug:
            print "cheat sheet: r(o) == gc.get_referrers(o)"
            print "  to create a msn reference: weakmsn()"
            print
            import code, readline, gc
            r = gc.get_referrers
            code.InteractiveConsole(locals()).interact(\
                "Entering controller.msn leak debug console")

        hotmail_file = os.path.join(paths.CONFIG_DIR, \
            self.config.getCurrentUser(), "cache", "login.htm")

        if os.path.isfile(hotmail_file):
            try:
                os.remove(hotmail_file)
            except:
                pass

    def quit(self, status):
        '''close the window, and do all the things needed...'''

        # makes it more responsive to the user by effectively hiding the
        # the window before disconnecting and quitting
        #self.mainWindow.connect('unmap-event', self.on_main_hidden, status)
        self.mainWindow.hide()
        if not TrayIcon.disabled:
            self.trayIcon.remove()

        try:
            self.mainWindow.saveToQuit()
        except:
            pass

        if self.connected:
            self.logout()
            #self.msn.logout()
            self.config.writeUserConfig()

        self.config.writeGlobalConfig()
        sys.exit(status)

    def checkPending(self):
        '''Check for users pending to be added'''

        if self.msn is None:
            return False

        if self.addBuddy is None:
            self.addBuddy = dialog.AddBuddy(self)

        users = self.msn.checkPending()
        if len(users) > 0:
            for mail in users:
                nick = self.msn.getUserDisplayName(mail)
                self.addBuddy.append(nick, mail)
        return False

    def set_picture_dialog(self):
        ''' Shows a dialog to change personal avatar '''
        def _on_picture_selected(response, path):
            '''method called on avatar selected'''
            if response == stock.ACCEPT:
                self.changeAvatar(path)
            elif response == stock.CLEAR:
                self.changeAvatar('')

        avatar_cache = self.config.getAvatarsCachePath()
        path_current = self.config.user['avatarPath']
        dialog.set_picture(self, path_current, avatar_cache, _on_picture_selected)

    def change_profile_dialog(self):
        '''shows a dialog to change nick, personal message and avatar'''

        def responseProfile(response, nick, psm, avatarPath):
            '''response if user accepts or denys the profile dialog'''
            if response == stock.ACCEPT:
                self.contacts.set_nick(nick)
                self.contacts.set_message(psm)
                if avatarPath != self.config.user['avatarPath']:
                    self.changeAvatar(avatarPath)

        nick=self.msn.nick.replace('\n', ' ')
        psm=self.msn.personalMessage.replace('\n', ' ')
        currentAvatarPath = self.config.user['avatarPath']
        dialog.show_profile(self, nick, psm, currentAvatarPath, responseProfile)

    def on_change_avatar(self, msnp, filename, initial=False):
        '''control if the avatar already exists or save the new avatar'''
        if os.path.exists(filename):
            self.changeAvatar(filename, initial)
            return
        else:
            return

    def changeAvatar(self, filename, initial=False):
        if not self.msn:
            return

        if not filename or not os.path.exists(filename):
            filename = ''
        try:
            self.avatar = Avatar.Avatar(self, filename,
                self.config.getAvatarsCachePath())
            filename = self.avatar.getImagePath()
        except:  # may be GError
            return

        if filename == '':
            self.mainWindow.setAvatar(self.theme.getImage('userPanel'))
            self.config.user['avatarPath'] = ''
        else:
            self.mainWindow.setAvatar(self.avatar.getThumb())
            self.config.user['avatarPath'] = self.avatar.getImagePath()

        # if not initial, update avatar on Msn's servers
        if not initial:
            self.msn.setDisplayPicture(filename)

        self.emit('avatar-changed')

    def on_self_status_changed(self, msn, status):
        '''called when our status changes'''
        if not TrayIcon.disabled:
            self.trayIcon.update(self.msn.status)

    def addUserDialog(self, toGroup=None):
        '''show a dialog requesting the email of the ser to be added'''
        def add_contact_cb(response, account='', group='', alias=''):
            '''callback for the add_contact dialog'''
            if response == stock.ACCEPT:
                account = account.strip()
                if len(account.split('@')) == 2:
                    if group != '' and not group in self.groups.groups.keys():
                        self.groups.add(group)
                    self.contacts.add(account, group, *(self.delayedAlias, account, alias))
                else:
                    dialog.warning(_("Invalid account"))

        dialog.add_contact(self.groups.groups.keys(), None, add_contact_cb, self.theme.getImage('login'))

    def delayedAlias(self, account, alias):
        self.contacts.set_alias(account, alias)
        return False

    def addNotification(self, msnp, command, tid, params, email, nick):
        '''this method is called when a user adds you'''

        if self.addBuddy is None:
            self.addBuddy = dialog.AddBuddy(self)

        self.addBuddy.append(nick, email)

    def refreshUserList(self, *args):
        '''call to refreshUserList on MainWindow that calls refresh on userList
        userList get the values of showOffline etc from config, so if you want
        to change something, change it on config.
        if it's loading contacts (ILN), don't do anything'''
        if self.lastILN == 0 or (time.time() - self.lastILN) > 1:
            self.mainWindow.refreshUserList()
            self.lastILN = 0

    # signal handlers
    def connectionProblem(self, msnp):
        '''called when a PNG is not answered'''
        self.logout(False, True)

    def onInitialStatusChange(self, msnp, command, tid, params):
        '''callback for ILN messages. saves the timestamp to speed up login'''
        self.lastILN = time.time()

    def onStatusChange(self, msnp, command, tid, params):
        '''callback for the status change event'''
        self.refreshUserList()

    def on_tray_disconnect(self, *args):
        self.logout()

    def msnobjChanged(self, msnp, msnobj, wasOffline):
        '''callback called when the user change his msnobj'''
        #if msnobj and not wasOffline:
        if msnobj:
            creator = msnobj.getCreator()
            contact = self.getContact(creator)
            if (not creator or not contact) or \
               self.theme.hasUserDisplayPicture(contact):
                return

            self.pendingAvatars[msnobj.getCreator()] = msnobj

            if not self.idleTimeout:
                self.idleTimeout = gobject.timeout_add(5000, \
                    self.idleadd, priority=gobject.PRIORITY_LOW)

    def idle(self):
        '''called when the gobject mainloop is idle
        gobjects thinks that it means "all the time" so we add a
        five-second non-blocking delay'''

        stop = True

        if len(self.pendingAvatars.keys()) > 0 and self.msn:

            # pop a pending avatar
            creator = self.pendingAvatars.keys().pop(0)
            msnobj = self.pendingAvatars[creator]
            contact = self.getContact(creator)

            requested = False

            # get a switchboard connection
            if contact and not self.theme.hasUserDisplayPicture(contact):
                # TODO: not a switchboard method
                sb = self.msn.getSwitchboard(creator)
                sb.getDisplayPicture(creator)
                requested = True
            elif contact:
                self.msn.emit("display-picture-changed", None, msnobj, creator)

            # delete from pending
            del self.pendingAvatars[creator]

            # if there are no more avatars left, stop
            stop = len(self.pendingAvatars.keys()) == 0
            if not stop and not requested:
                return self.idle()

        if not stop:
            # wait 20 seconds without blocking
            self.idleTimeout = gobject.timeout_add(20000, \
                self.idleadd, priority=gobject.PRIORITY_LOW)
        return False

    def idleadd(self, *args):
        '''called 5 seconds after last idle call'''
        self.idleTimeout = 0
        gobject.idle_add(self.idle, priority=gobject.PRIORITY_LOW)
        return False

    def newConversation(self, msnp, mail, switchboard=None, weStarted=False):
        '''This method is called when the user want to initiate a new
        conversation with someone, or when a switchboard has been created
        and we want to give a window to it.
        (callback for 'new conversation' signal emmited by msnp)
        weStarted is a boolean that indicate if we started the conversation or
        a friend'''

        return self.conversationManager.newConversation(self.msn, mail, \
            switchboard, weStarted)

    def seeAvatarHistory(self, email):
       '''opens a dialog with all user's avatars'''

       avatar_cache = self.config.getCachePath()
       AvatarHistoryViewer(self,avatar_cache, email).show()

    def seeProfile(self, email):
        '''opens the profile url in a browser'''
        desktop.open('http://members.msn.com/' + email)

    def offlineMessageWaiting(self, msnp, msnOIM):
        '''process the OIM messages'''
        msnOIM.retrieve()

    def offlineMessageReceived(self, msnp, oim):
        '''process the OIM message'''
        user, date, message = oim
        window, conv = self.newConversation(msnp, user['addr'], None, False)
        self.conversationManager.newest_message_conv = conv
        conv.receiveOIM(user['name'], message, date)

    def messageError(self, msnp, to, message, error):
        window, conv = self.newConversation(self.msn, to, None, True)
        conv.receiveError(msnp, to, message, error)

    def userDisconnected(self, msnp, tid, params):
        '''method called when the server disconnect us'''
        if tid == 'OTH':
            message = _('Logged in from another location.')
        else:
            message = _('The server has disconnected you.')

        self.logout(False, False)
        self.mainWindow.showNiceBar(message,self.tooltipColor)

    def getMenuData(self):
        return self.mainWindow.userList.getMenuData()

    # TODO: getters
    def getUnreadMails(self):
        if self.msn:
            return self.msn.inboxUnreadMessages
        else:
            return 0

    def getContact(self, mail):
        '''return a contact object'''
        if not self.msn:
            return None

        return self.msn.contactManager.getContact(mail)

    def updateDebug(self, *args):
        if self.msn:
            self.msn.setDebug(self.config.glob['debug'], \
                self.config.glob['binary'])

def parseArgs():
    '''parses sys.argv with getopt, returns tuple with Controller args'''
    username = ''
    minimized = False
    leakdebug = False
    iconified = False
    badroot = False
    singleinstance = False

    # parse arguments
    try:
        import getopt
    except ImportError:
        #getopt is disabled in emesene py2exe
        return ('', False, False, False, False, False)

    shortArgs = 'm,i,f,s'
    longArgs = ['iconified', 'minimized', 'user=', 'fast-login', 'leakdebug', 
                'i-know-that-running-emesene-as-root-is-bad', 'single-instance']
    try:
        args = getopt.getopt(sys.argv[1:], shortArgs, longArgs)
    except getopt.GetoptError, e:
        # wrong input, display usage
        print e
        print 'Usage:', sys.argv[0], '[-m|--minimized] | [-i | --iconified] [--user=mail@address]'
        print 'Advanced options: [-f|--fast-login], --leakdebug, --i-know-that-running-emesene-as-root-is-bad, [-s|--single-instance]'
        sys.exit(1)

    # parse getopt output
    for key, value in args[0]:
        if key == '--user':
            username = value
        if key == '-m' or key == '--minimized':
            minimized = True
        else:
            if key == '-i' or key == '--iconified':
                iconified = True
        if key == '--leakdebug':
            leakdebug = True
        if key == '--i-know-that-running-emesene-as-root-is-bad':
            badroot = True
        if key == '-s' or key == '--single-instance':
            singleinstance = True

    return (username, minimized, leakdebug, iconified, badroot, singleinstance)

def debug(msg):
    '''print a debug message'''
    print 'Controller: ' + msg

def main():
    args = parseArgs()

    if (os.name == 'posix') and (os.getuid() == 0) and (args[4] == False):
        print "I refuse to run as root. " \
              "If you know the risks and still want to do it," \
              " just add the --i-know-that-running-emesene-as-root-is-bad option."
        return

    single_instance = SingleInstance()

    if args[5] and single_instance.is_running():
        print "Another instance of emesene is already running. Quitting."
        # try to show instance already running
        single_instance.show()
        sys.exit(0)
    
    if (os.name != 'nt'):
        try:
            path = os.path.dirname(__file__) or sys.path[0]
        except NameError:
            path = sys.path[0]
    else:
        path = os.path.dirname(sys.path[0])

    gtk.settings_get_default().set_property("gtk-error-bell", False)
    originalPath = os.getcwd()
    os.chdir(path)
    sys.path.append(path)
    # start controller
    if (os.name == 'nt') and (hasattr(sys, "frozen")):
        controller = Controller('', *args)    
    else:
        controller = Controller(*args)
    gobject.threads_init()
    # this stuff is to interrupt blocking stuff safely.
    for i in range(5):
        try:
            gtk.gdk.threads_init()
            gtk.gdk.threads_enter()
            gtk.main()
            gtk.gdk.threads_leave()
            
        except KeyboardInterrupt:
            print 'Interrupt (%s more times to close)' % str(5 - i)
        else:
            break
    controller.quit(0)
    os.chdir(originalPath)

        

if __name__ == '__main__':
    main()
