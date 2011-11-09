# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Eval plugin is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Eval plugin is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

VERSION = '0.2'
import os
import sys
import time
import socket
import commands

import emesenelib.common

import Plugin

class MainClass( Plugin.Plugin ):
    '''Main plugin class'''
    description = _('Make some useful commands available, try /help')
    authors = { 'marianoguerra' : 'luismarianoguerra gmail com' }
    website = 'http://emesene.org'
    displayName = _('Commands')
    name = 'Commands'

    def __init__( self, controller, msn ):
        '''Contructor'''

        Plugin.Plugin.__init__( self, controller, msn )

        self.description = _('Make some useful commands available, try /help')
        self.authors = { 'marianoguerra' : 'luismarianoguerra gmail com' }
        self.website = 'http://emesene.org'
        self.displayName = _('Commands')
        self.name = 'Commands'
        self.controller = controller
        self.Slash = controller.Slash

        self.vars = {}
    #    self.vars['%me%'] = self._me
        self.vars['%nick%'] = self._nick
        self.vars['%status%'] = self._status
        self.vars['%mail%'] = self._mail
        self.vars['%date%'] = self._date
        self.vars['%time%'] = self._time
        self.vars['%host%'] = self._host
        self.vars['%ip%'] = self._ip

    #def _me(self):
    #    return self.controller.msn.user.split('@')[0]

    def _nick(self):
        return self.controller.msn.nick

    def _status(self):
        return emesenelib.common.reverse_status[self.controller.msn.status]

    def _mail(self):
        return self.controller.msn.user

    def _date(self):
        return time.strftime('%d-%b-%y')

    def _time(self):
        return time.strftime( '%H:%M' )

    def _host(self):
        return socket.gethostname()

    def _ip(self):
        try:
            result = socket.getaddrinfo(self._host(), None, 0, socket.SOCK_STREAM)
            return ''.join([x[4][0] for x in result])
        except socket.gaierror:
            return '0.0.0.0'

    def start( self ):
        '''start the plugin'''
        self.Slash.register('repl', self.repl, _('Replaces variables'))
    #    self.Slash.register('me', self.slash_me,
    #        _('Replaces me with your username'))
        self.Slash.register('me', self.slash_action_message,
            _('Sends an action'))
        self.Slash.register('nudge', self.slash_nudge,
            _('Sends a nudge'))
        self.Slash.register('invite', self.slash_invite,
            _('Invites a buddy'))
        self.Slash.register('send', self.slash_send,
            _('Send a file'))
        self.Slash.register('add', self.slash_contact_actions,
            _('Add a contact'))
        self.Slash.register('remove', self.slash_contact_actions,
            _('Remove a contact'))
        self.Slash.register('block', self.slash_contact_actions,
            _('Block a contact'))
        self.Slash.register('unblock', self.slash_contact_actions,
            _('Unblock a contact'))
        self.Slash.register('clear', self.slash_clear,
            _('Clear the conversation'))
        self.Slash.register('nick', self.slash_nick_psm,
            _('Set your nick'))
        self.Slash.register('psm', self.slash_nick_psm,
            _('Set your psm'))
        self.Slash.register('amsg', self.slash_amsg,
            _('Send a message to your opened conversations'))
        self.Slash.register('exec', self.slash_exec,
            _('Executes a system command and sends it to current conversation'))
        self.Slash.register('offline', self.slash_offline,
            _('Change the status to offline'))
        self.Slash.register('online', self.slash_online,
            _('Change the status to online'))
        self.Slash.register('busy', self.slash_busy,
            _('Change the status to busy'))
        self.Slash.register('away', self.slash_away,
            _('Change the status to away'))
        self.Slash.register('idle', self.slash_idle,
            _('Change the status to idle'))
        self.Slash.register('logout', self.slash_logout,
            _('Logs you out'))

        self.enabled = True

    def repl(self, slash_action):
        data = slash_action.getParams()

        for (var,replacement) in self.vars.iteritems():
            data = data.replace(var, replacement())

        slash_action.outputText(data, True)

    #def slash_me(self, slash_action):
    #    data = slash_action.getParams()
    #
    #    slash_action.outputText(self._nick() + ' ' + data, True)

    def slash_nick_psm(self, slash_action):
        '''Set your nick or psm'''
        data = slash_action.params
        name = slash_action.name
        contact_manager = self.controller.contacts
        if name == 'nick':
            contact_manager.set_nick(data)
        elif name == 'psm':
            contact_manager.set_message(data)

    def slash_nudge(self, slash_action):
        slash_action.conversation.doNudge()

    def slash_invite(self, slash_action):
        slash_action.conversation.parentConversationWindow.show_invite_dialog()

    def slash_contact_actions(self, slash_action):
        contacts = self.controller.contacts
        data = slash_action.params
        name = slash_action.name
        if name == "add" and (data == "" or data.find("@") == -1):
            slash_action.outputText(_("Usage /%s contact_email" % name))
            return
        if name != "add":
            if data == "":
                slash_action.outputText(_("No user specified, applying action to current contact.\n Usage /%s contact_email" % name))
                data = slash_action.conversation.userMail
            elif data.find("@") == -1:
                slash_action.outputText(_("%1 is not a valid parameter. Usage /%2 contact_email") % (data, name))
                return

        if name == 'add':
            contacts.add(data, "")
        elif name == 'block':
            contacts.block(data)
        elif name == 'unblock':
            contacts.unblock(data)
        elif name == 'remove':
            contacts.remove(data)

    def slash_send(self, slash_action):
        '''Send a file'''
        conversation = slash_action.conversation
        file_path = slash_action.params
        if file_path:
            if os.path.exists(file_path):
                conversation.sendFile(file_path)
            else:
                slash_action.outputText(_("File doesn't exist"))
        else:
            conversation.parentConversationWindow.send_file_dialog()

    def slash_clear(self, slash_action):
        slash_action.conversation.parentConversationWindow.clearOutputText()

    def slash_action_message(self, slash_action):
        data = slash_action.getParams()

        slash_action.sendActionMessage(data)
        
    def slash_amsg(self, slash_action):
        """Sends a message to every opened conversation"""
        #Let's get parameters
        params = slash_action.getParams()
        if params :
            #if there are parameters
            for i, j in self.controller.conversationManager.conversations :
                j.sendMessage(params)
        else:
            #if there are not parameters
            slash_action.outputText(_('Error: missing text parameter'))
            slash_action.outputText(_('USAGE: /amsg <text>'))

    def slash_exec(self, slash_action):
        """Run shell command and send it to conversation"""
        params = slash_action.getParams()

        if params:
            command = commands.getoutput(params)
            slash_action.outputText(command, True)
        else:
            slash_action.outputText(_('Usage: /exec <system command>'))

    def slash_logout(self, slash_action):
        self.controller.logout()

    def slash_online(self, slash_action):
        self.controller.contacts.set_status("NLN")

    def slash_busy(self, slash_action):
        self.controller.contacts.set_status("BSY")

    def slash_away(self, slash_action):
        self.controller.contacts.set_status("AWY")

    def slash_idle(self, slash_action):
        self.controller.contacts.set_status("IDL")

    def slash_offline(self, slash_action):
        self.controller.contacts.set_status("HDN")

    def stop( self ):
        '''stop the plugin'''
        self.Slash.unregister('repl')
        self.Slash.unregister('me')
        self.Slash.unregister('nudge')
        self.Slash.unregister('invite')
        self.Slash.unregister('send')
        self.Slash.unregister('add')
        self.Slash.unregister('remove')
        self.Slash.unregister('block')
        self.Slash.unregister('unblock')
        self.Slash.unregister('clear')
        self.Slash.unregister('psm')
        self.Slash.unregister('amsg')
        self.Slash.unregister('exec')
        self.Slash.unregister('offline')
        self.Slash.unregister('online')
        self.Slash.unregister('busy')
        self.Slash.unregister('away')
        self.Slash.unregister('idle')
        self.Slash.unregister('logout')
        self.enabled = False

    def check( self ):
        return ( True, 'Ok' )
