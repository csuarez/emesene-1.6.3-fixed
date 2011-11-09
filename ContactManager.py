# -*- coding: utf-8 -*-
'''a module to handle contacts'''

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
import urllib

import abstract.ContactManager
import abstract.stock as stock
import status
import dialog

class ContactManager(abstract.ContactManager.ContactManager):
    '''Implementation of abstract.ContactManager using emesenelib'''

    def __init__(self, dialog, protocol, account):
        '''initialize the object, dialog is a implementation
        of abstract.dialog, it's used to interact with the user'''
        abstract.ContactManager.ContactManager.__init__(self,
            dialog, protocol, account)

        # for dummy implementations
        if protocol:
            self._connect_signals()
        else:
            debug('Protocol is None')

    def _connect_signals(self):
        '''connect all the signals of the protocol'''
        # connect the signals to the private methods (see the double
        # underscore, this methods receive the parameters and call
        # the methods of abstract.ContactManager.ContactManager
        self.protocol.connect('contact-added', self.__on_contact_added)
        self.protocol.connect('contact-removed', self.__on_contact_removed)

        self.protocol.connect('contact-attr-changed',
            self.__on_contact_attr_changed)
        self.protocol.connect('nick-changed',
            self.__on_contact_nick_changed)
        self.protocol.connect('contact-status-change',
            self.__on_contact_status_changed)
        self.protocol.connect('initial-status-change',
            self.__on_initial_status_changed)
        self.protocol.connect('personal-message-changed',
            self.__on_contact_message_changed)

        self.protocol.connect('contact-added-to-group',
            self.__on_contact_added_to_group)
        self.protocol.connect('contact-removed-from-group',
            self.__on_contact_removed_from_group)

    def __on_contact_added(self, protocol, account, identifier=None,
        nick=None, message=None, _status=status.OFFLINE, alias=None,
        blocked=False):
        '''callback called when a new contact is added'''

        if _status in status.MSN_TO_STATUS:
            _status = status.MSN_TO_STATUS[_status]
        elif not status.is_valid(_status):
            debug("Invalid status '%s', setting offline" % (_status,))
            _status = status.OFFLINE

        self._on_contact_added(account, identifier, nick, message, _status,
            alias, blocked)

    def __on_contact_removed(self, protocol, account):
        '''callback called when a contact is removed'''
        self._on_contact_removed(account)

    def __on_contact_attr_changed(self, protocol, account, attr, val):
        '''callback called when an attribute is changed on a contact,
        this attribute can be block or alias (since these are the
        attributes that the user can change, the others are changed
        by the user itself)'''
        self._on_contact_attr_changed(account, attr, val)

    def __on_contact_nick_changed(self, protocol, account, nick):
        '''callback called when an user change his nick'''
        self._on_contact_nick_changed(account, nick)

    def __on_contact_message_changed(self, protocol, account, message):
        '''callback called when an user change his message'''
        self._on_contact_message_changed(account, message)

    def __on_contact_status_changed(self, protocol, account, new_status):
        '''callback called when an user change his status'''
        if new_status in status.MSN_TO_STATUS:
            self._on_contact_status_changed(account,
                status.MSN_TO_STATUS[new_status])
        else:
            debug("invalid status '%s'" % (new_status,))

    def __on_initial_status_changed(self, protocol, command, tid, params):
        '''callback called when an user change his status'''
        (_status, account, networkid, nick, rest) = params.split(' ', 4)
        nick = urllib.unquote(nick)

        if self.exists(account):
            contact = self.contacts[account]
            old_nick = contact.nick
            old_status = contact.status
            contact._on_nick_changed(nick)
            contact._on_status_changed(status.MSN_TO_STATUS[_status])
            self.signal_emit('contact-changed', contact, 'nick', old_nick)
            self.signal_emit('contact-changed', contact, 'status', old_status)
            self.signal_emit('contact-nick-changed', contact, old_nick)
            self.signal_emit('contact-status-changed', contact, old_status)
        else:
            debug("account '%s' not in self.contacts" % (account,))

    def __on_contact_added_to_group(self, protocol, account, group_name):
        '''callback called when an account is added to a group'''
        self._on_contact_added_to_group(account, group_name)

    def __on_contact_removed_from_group(self, protocol, account, group_name):
        '''callback called when an account is removed from a group'''
        self._on_contact_removed_from_group(account, group_name)

    # actions on our contact
    def set_nick(self, nick):
        '''set the nick of our account to nick'''
        if self.protocol:
            self.me.nick = nick
            self.protocol.changeNick(nick)
        
    def set_message(self, message):
        '''set the personal message of our account to message'''
        if self.protocol:
            self.me.message = message
            self.protocol.changePersonalMessage(message)

    def set_media(self, media):
        '''set the current media of out account to current_media'''
        if self.protocol:
            self.me.attrs['media'] = media
            self.protocol.changeCurrentMedia(media)

    def set_status(self, new_status):
        '''set the status to status, the status should be one of the
        constants on status.py, consider calling status.is_valid.
        Also you should convert it to the values on the library'''
        if not self.protocol:
            return

        if status.is_valid(new_status):                        # direct
            self.me.status = status.STATUS_TO_MSN[new_status]
            self.protocol.changeStatus(status.STATUS_TO_MSN[new_status])
        elif new_status in status.STATUS_TO_MSN.values():             # HDN
            self.me.status = new_status
            self.protocol.changeStatus(new_status)
        else:
            debug('not a valid status"' + new_status + '"')

    def get_status(self, account=None):
        '''return the status of an account if exist, status.OFFLINE if dont
        if account == None, return the status of our user'''
        if account:
            if self.exists(account):
                return status.STATUS_TO_MSN[self.contacts[account].status]
            else:
                debug("account '%s' not in self.contacts" % (account,))
        else:
            return self.me.status

    def set_picture(self, path):
        '''set the display picture to path'''
        if self.protocol:
            self.protocol.changeAvatar(path)
            self.me.picture = path

    # actions on other contacts
    def set_alias(self, account, alias):
        '''set the contact alias, give an empty alias to reset'''
        if self.protocol:
            self.protocol.changeAlias(account, alias)
            self._on_contact_attr_changed(account, 'alias', alias)

    def block(self, account):
        '''unblock an user'''
        if self.protocol:
            self.protocol.blockUser(account)
            self._on_contact_attr_changed(account, 'block', True)

    def unblock(self, account):
        '''unblock an user'''
        if self.protocol:
            self.protocol.unblockUser(account)
            self._on_contact_attr_changed(account, 'block', False)

    def remove(self, account):
        '''remove an user'''
        message = _('Are you sure you want to delete %s from your contacts?') %account
        window = dialog.yes_no(message, self.delete_confirmation, account)
        
    def delete_confirmation(self, *args):
        if args[0] == stock.YES:
            if self.protocol:
                account = args[1]
                self.protocol.removeUser(account)
                
    def remove_from_pending_list(self, mail):
        '''rejects add request'''
        if self.protocol:
            self.protocol.removeUserFromPending(mail)

    def add(self, account, group, *callback_and_args_triple):
        '''add an user'''
        if self.protocol:
            self.protocol.addUser(account, group, *callback_and_args_triple)

    def move_to_group(self, account, src_group, dest_group):
        '''move a user from src_group to dest_group'''
        if self.protocol:
            self.protocol.moveUserToGroup(account, src_group, dest_group)

    def add_to_group(self, account, group):
        '''add an user to a group, return True on success'''
        if self.protocol:
            self.protocol.addUserToGroup(account, group)

    def remove_from_group(self, account, group):
        '''remove an user from a group'''
        if self.protocol:
            self.protocol.removeUserFromGroup(account, group)

def debug(msg):
    '''debug method, the module send the debug here, it can be changed
    to use another debugging method'''
    return
    print('ContactManager.py: ', msg)
