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
'''a module that define a class to contain all the information regarding a 
session
'''

class Session(Object.Object):
    '''a class that contain information and methods to handle a session'''

    def __init__(self, account, password, host, port):
        '''class constructor'''
        self.account = account
        self.password = password
        self.host = host
        self.port = port

        # set this on login
        self.contacts = None
        self.groups = None

        self.signal_add('login-successful', 0)
        # message
        self.signal_add('login-error', 1)
        # message
        self.signal_add('connection-error', 1)

    def login(self, account, password, stat):
        '''do login and set status'''
        raise NotImplementedError("This method isn't not implemented")

    def cancel_login(self):
        '''cancel the login process if posible on the protocol implementation
        '''
        raise NotImplementedError("This method isn't not implemented")

    def logout(self):
        '''do logout'''
        raise NotImplementedError("This method isn't not implemented")

