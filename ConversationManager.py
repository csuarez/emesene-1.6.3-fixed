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

import gobject

import Conversation
import ConversationWindow

class ConversationManager(gobject.GObject):
    '''This class handle a collection of conversations'''

    __gsignals__ = {
        # conversation, window
        'new-conversation-ui' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # conversation, window
        'close-conversation-ui' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # send conversation, message
        'send-message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)),
        # receive conversation, (message params)
        'receive-message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,gobject.TYPE_STRING,gobject.TYPE_STRING, \
         gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, \
         gobject.TYPE_BOOLEAN)),
    }

    def __init__(self, controller):
        '''Contructor'''

        gobject.GObject.__init__(self)

        self.controller = controller
        self.theme = controller.theme
        self.config = controller.config

        #list of (ConversationWindow, Conversation) tuples
        self.conversations = []
        self.newest_message_conv = None

        self.user = ''

        self.signals = []
        sap = self.signals.append
        sap(self.config.connect('change::showHeader', self.updateUI))
        sap(self.config.connect('change::showToolbar', self.updateUI))
        sap(self.config.connect('change::showAvatars', self.updateUI))
        sap(self.config.connect('change::showAvatarMine', self.updateUI))
        sap(self.config.connect('change::showAvatarOther', self.updateUI))
        sap(self.config.connect('change::showStatusBar', self.updateUI))
        sap(self.config.connect('change::showTabCloseButton', self.updateUI))
        sap(self.config.connect('change::showSendButton', self.updateUI))
        sap(self.config.connect('change::hideNewWindow', self.updateUI))

        self.controller.connect('preferences-changed', self.updateUI)

    def handleLogin(self, user):
        '''handle a new user login (close conversations or reconnect them, etc.)'''
        if self.user == user:
            # same user as previous, enable all open conversations
            self.enableAll()
        else:
            # another user logged in, close open conversations
            self.user = user
            self.closeAll()

    def updateUI(self, *args):
        for window, conversation in self.conversations:
            conversation.ui.update()

    def getOpenConversation(self, mail, switchboard = None):
        '''return (ConversationWindow, conversation) for this contact,
        or return None if there isn't a conversation open yet'''

        self.removeClosedWindows()
        for window, conversation in self.conversations:
            members = conversation.getMembers()
            if len(members) == 1 and members[0] == mail:
                return (window, conversation)
            elif len(members) > 1 and mail in members:
                # groupchat, check if it's with the same contacts
                if switchboard and len(switchboard.members) == len(members) and \
                    sorted(switchboard.members.keys()) == sorted(members):
                        return (window, conversation)
        return None

    def removeClosedWindows(self):
        '''remove conversations for closed windows'''
        for window, conversation in self.conversations[:]:
            if window.closed or conversation.closed or \
               (window.notOpen and conversation.getStatus() == 'closed'):
                self.conversations.remove((window, conversation))

    def openConversation(self, msnp, mail, weStarted, switchboard=None):
        '''opens a new conversation and a new window or tab'''

        # create new switchboard if needed
        if switchboard is None:
            switchboard = msnp.newSwitchboard()
            switchboard.invite(mail)

        conversation = Conversation.Conversation(self.controller, switchboard)

        # add a tab if we use tabs and if there is a window open already
        useTabs = not self.config.user['windows']
        if useTabs and len(self.conversations) > 0:
            # open a new tab
            window = self.conversations[0][0]
            window.openTab(conversation)
            if weStarted:
                window.present()
        else:
            # open a new window
            window = ConversationWindow.ConversationWindow(self.controller, conversation)
            window.show()
            if self.config.user['hideNewWindow'] and not weStarted:
                window.iconify()


        conversation.setWindow(window)
        window.set_icon(conversation.getWindowIcon())
        self.conversations.append((window, conversation))
        self.emit('new-conversation-ui', conversation, window)

        return window, conversation

    def newConversation(self, msnp, mail, switchboard, weStarted):
        '''Open a new conversation, or open an existing window or tab
        if switchboard is None we create the switchboard'''

        window = conversation = None
        result = self.getOpenConversation(mail, switchboard)

        if result is not None:
            # conversation open already
            window, conversation = result

            # set new switchboard
            if switchboard:
                conversation.setSwitchboard(switchboard)

            # show the current window and tab
            if weStarted:
                if not self.config.user['windows']:
                    window.showTab(window.tabs.page_num(conversation.ui))
                window.present()
        else:
            # open new conversation with this contact
            window, conversation = self.openConversation(msnp, mail,
                                weStarted, switchboard)

        return window, conversation

    def do_send_message(self, conversation, message):
        '''Send message to conversation'''
        conversation.do_send_message(message)

    def do_receive_message(self, conversation, mail, nick, message, format,
      charset, p4c):
        '''Receive a message from'''
        self.newest_message_conv = conversation
        conversation.do_receive_message(mail, nick, message, format, charset, p4c)

    def closeAll(self):
        '''close all the conversations'''

        for window, conversation in self.conversations:
            window.hide()

        self.conversations = []

    def disableAll(self):
        '''close conversations and disable text input of conversation windows'''

        for window, conversation in self.conversations:
            conversation.ui.setInputEnabled(False)
            conversation.switchboard.leaveChat()

    def enableAll(self):
        '''reconnect conversations and re-enable text input'''

        for window, conversation in self.conversations:
            conversation.reconnect()
            conversation.ui.setInputEnabled(True)
