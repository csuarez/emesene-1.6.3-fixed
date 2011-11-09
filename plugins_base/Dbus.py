# -*- coding: utf-8 -*-

#   This file is a plugin for emesene.
#
#    Dbus Emesene Plugin is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Dbus Emesene Plugin is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gtk
from AvatarHistory import getLastCachedAvatar
import Plugin

try:
    import dbus, dbus.service
    dbusError = ''
    if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
        import dbus.glib
    if getattr(dbus, 'version', (0,0,0)) >= (0,80,0):
        import _dbus_bindings as dbus_bindings
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)
        NEW_DBUS = True
    else:
        import dbus.mainloop.glib
        import dbus.dbus_bindings as dbus_bindings  
        NEW_DBUS = False
except Exception, e:
    dbusError = e

BUS_NAME = 'org.emesene.dbus'
OBJECT_PATH = '/org/emesene/dbus'

PLUGIN_DESCRIPTION = _('With this plugin you can interact via D-Bus with emesene')
PLUGIN_AUTHORS = {'Roger Duran' : 'RogerDuran at gmail dot com'}
PLUGIN_WEBSITE = 'http://www.rogerpc.com.ar'
PLUGIN_DISPLAY_NAME = 'D-Bus'
PLUGIN_NAME = 'D-Bus'

class MainClass(Plugin.Plugin):
    '''Main plugin class'''
    description = PLUGIN_DESCRIPTION
    authors = PLUGIN_AUTHORS
    website = PLUGIN_WEBSITE
    displayName = PLUGIN_DISPLAY_NAME
    name = PLUGIN_NAME

    def __init__(self, controller, msn):
        '''Contructor'''

        Plugin.Plugin.__init__(self, controller, msn)
        self.theme = controller.theme

        self.description = PLUGIN_DESCRIPTION
        self.authors = PLUGIN_AUTHORS
        self.website = PLUGIN_WEBSITE
        self.displayName = PLUGIN_DISPLAY_NAME
        self.name = PLUGIN_NAME

        #callback ids
        self.user_connect_id = None
        self.user_offline_id = None
        self.self_nick_changed_id = None
        self.psm_changed_id = None
        self.status_changed_id = None
        self.new_message_id = None
        self.message_read_id = None
        
        self.unread_message_count = None

        self.dbus_object = None

    def start( self ):
        '''start the plugin'''
        self.start_dbus()

        self.user_connect_id = self.connect('user-online', self.user_connect)
        self.user_offline_id = self.connect('user-offline', self.user_offline)
        self.self_nick_changed_id = self.connect('self-nick-changed',
                                                  self.self_nick_changed)
        self.psm_changed_id = self.connect('personal-message-changed',
                                            self.psm_changed)
        self.status_changed_id = self.connect('self-status-changed',
                                            self.status_changed)
        self.new_message_id = self.connect('switchboard::message', self.new_message)
        self.message_read_id = self.controller.connect('message-read', self.message_read)
        
        self.unread_message_count = 0

        self.enabled = True

    def stop( self ):
        '''stop the plugin'''
        self.disconnect( self.user_connect_id )
        self.disconnect( self.user_offline_id )
        self.disconnect( self.self_nick_changed_id )
        self.disconnect( self.psm_changed_id )
        self.disconnect( self.status_changed_id )
        self.disconnect( self.new_message_id )
        self.disconnect( self.message_read_id )

        self.destroy_dbus_session()

        self.enabled = False

    def action( self ):
        pass

    def check( self ):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> ( True , 'some message' )
        else -> ( False , 'error message' )
        '''
        if dbusError != '':
            self.destroy_dbus_session()
            return (False, 'Can\'t Load dbus', dbusError)

        return (True, 'Ok')

    def start_dbus(self):
        '''Start dbus session'''
        self.destroy_dbus_session()
        self.session_bus = dbus.SessionBus()
        self.bus_name = dbus.service.BusName(BUS_NAME, bus=self.session_bus)
        self.dbus_object = EmeseneObject(self.bus_name, OBJECT_PATH, self)

    def destroy_dbus_session(self):
        '''Destroy current dbus session'''
        
        if self.dbus_object:
            try:
                dbus.service.Object.remove_from_connection(self.dbus_object)
            except AttributeError:
                pass
            self.dbus_object = None

    ''' The tests on each function are there in case the internet connection dropped,
        and dbus is restarted.  When this happens, dbus_object can fail to
        instantiate, which can cause headaches.
    '''

    def user_connect(self, msnp, user, oldStatus):
        if self.dbus_object == None:
            self.start_dbus()
            
        if oldStatus == 'FLN':
            self.dbus_object.user_connect(user)

    def status_changed(self, msnp, status):
        if self.dbus_object == None:
            self.start_dbus()
            
        newstatus = self.msn.status
        self.dbus_object.status_changed('', newstatus)

    def user_offline(self, msnp, user):
        if self.dbus_object == None:
            self.start_dbus()
            
        self.dbus_object.user_offline(user)

    def self_nick_changed(self, msnp, old, nick):
        if self.dbus_object == None:
            self.start_dbus()
            
        self.dbus_object.self_changed_nick(nick)

    def psm_changed(self, msnp, email, pm):
        if self.dbus_object == None:
            self.start_dbus()
            
        self.dbus_object.psm_changed(email, pm)
        
    def new_message(self, msn, switchboard, signal, args, stamp=None):
        if self.dbus_object == None:
            self.start_dbus()
            
        count = self.unread_message_count
        count = count + 1
        self.unread_message_count = count
        self.dbus_object.set_message_count(count)
        self.dbus_object.unread_messages(count)
        
    def message_read(self, arg1):
        if self.dbus_object == None:
            self.start_dbus()
            
        self.unread_message_count = 0
        self.dbus_object.set_message_count(0)
        self.dbus_object.unread_messages(0)

try:
    class EmeseneObject(dbus.service.Object):
        def __init__(self, bus_name, object_path, main):
            ''' Try to create a new service object.  This will only fail if emesene already has a signal
                service running in dbus, where the plugin was brought down due to a loss of connection.
                If it does fail, it doesn't matter, it will just reconnect with the service again.
            '''
            try:
                dbus.service.Object.__init__(self, bus_name, object_path)
            except Exception, ex:
                print 'dbus.py: ERROR: %s' % str(ex)
                
            self.main = main
            self.msn = main.msn
            self.controller = main.controller
            self.contact_manager = self.controller.contacts
            self.msg_count = 0

        #Methods
        @dbus.service.method(BUS_NAME)
        def get_status(self):
            return self.msn.status

        @dbus.service.method(BUS_NAME)
        def show(self):
            # Show main window
            mainWindow = self.controller.mainWindow           
            if mainWindow != None:
                flags = mainWindow.flags()
                if not (flags & gtk.MAPPED):
                    mainWindow.deiconify()
                mainWindow.show()
            
            # Also show all open converstations           
            manager = self.controller.conversationManager
            if manager != None:
                for win, conv in manager.conversations:
                    win.present()

            # call map again so dialogs will refresh their contents
            if mainWindow != None:
                mainWindow.emit('map')

        @dbus.service.method(BUS_NAME)
        def set_psm(self, text):
            self.contact_manager.set_message(text)
            return 'Psm Changed'

        @dbus.service.method(BUS_NAME)
        def set_media(self, text):
            self.contact_manager.set_media(text)
            return 'Current Media Changed'

        @dbus.service.method(BUS_NAME)
        def set_status(self, status):
            self.contact_manager.set_status(status)
            return 'Status Changed'

        @dbus.service.method(BUS_NAME)
        def set_nick(self, nick):
            self.contact_manager.set_nick(nick)
            return 'Nick changed'

        @dbus.service.method(BUS_NAME)
        def set_avatar(self, path):
            ''' set avatar '''
            if path != None and os.path.exists(path):
                self.controller.changeAvatar(path)
                return True
            return False

        @dbus.service.method(BUS_NAME)
        def open_conversation(self, email='', weStarted=False):
            try:
                self.controller.newConversation(None, email, None, weStarted)
                return 'opened ' + str(email)
            except Exception, e:
                return 'error trying to start a conversation: ' + str(e)

        @dbus.service.method(BUS_NAME)
        def get_user_account(self):
            return self.controller.userEmail

        @dbus.service.method(BUS_NAME)
        def get_conversation_history(self, email):
            logger = self.controller.pluginManager.getPlugin('Logger')
            if not logger:
                debug('Logger plugin is not enabled, please enable it')
            else:
                logger.on_menuitem_activate(None, email)

        @dbus.service.method(BUS_NAME)
        def get_last_display_picture(self, email='', cache=True):
            imagePath='noImage'
            lista = []
            if cache:
                try:
                    cachePath = self.controller.config.getCachePath()
                    contact = self.controller.getContact(email)
                except Exception, e:
                    debug("Exception when getting contact %s" % str(e))
                    return imagePath
                imagePath = os.path.join(cachePath, contact.displayPicturePath)
                if os.path.exists( imagePath ) and os.path.isfile( imagePath ):
                    debug("Dbus.get_last_display_picture: ImagePath for contact %s = %s" % (email, imagePath))
                    return imagePath
                else:
                    imagePath = getLastCachedAvatar(contact.email, cachePath)
                    if os.path.isfile(imagePath):
                        debug("Dbus.get_last_display_picture: ImagePath for contact %s = %s" % (email, imagePath))
                        return imagePath
                    imagePath = 'noImage'
            else:
                logger = self.controller.pluginManager.getPlugin('Logger')
                if not logger:
                    debug('Logger plugin is not enabled, please enable it')
                else:
                    lista = list(logger.get_last_display_picture(email))
                if len(lista) > 0:
                    display = lista[0]
                    imagePath = display[1]
                    debug("Dbus.get_last_display_picture: ImagePath for contact %s = %s" % (email, imagePath))
                else:
                    imagePath = 'noImage'
            return imagePath

        @dbus.service.method(BUS_NAME)
        def get_avatar_history(self, email):
            return self.controller.seeAvatarHistory(email);

        dbus.service.method(BUS_NAME)
        def get_email_page(self):
            return self.controller.hotmail.getLoginPage()

        @dbus.service.method(BUS_NAME, out_signature='aa{ss}')
        def get_online_users(self):
            users = self.contact_manager.get_online_list()
            contacts = []
            for user in users:
                user_status = self.contact_manager.get_status(user.account)
                contact = {'email': user.account, 'name': user.nick, 'status': user_status}
                contacts.append(contact)
            return contacts

        @dbus.service.method(BUS_NAME)
        def get_contact_nick(self, email):
            return self.contact_manager.get_nick(email)

        @dbus.service.method(BUS_NAME)
        def get_psm(self, email):
            return self.contact_manager.get_message(email)
            
        @dbus.service.method(BUS_NAME)
        def get_message_count(self):
            return self.msg_count
        
        @dbus.service.method(BUS_NAME)
        def set_message_count(self, count):
            self.msg_count = count
            return 'Message count changed'


        #Signals
        @dbus.service.signal(BUS_NAME)
        def user_connect(self, user):
            pass

        @dbus.service.signal(BUS_NAME)
        def user_offline(self, email):
            pass

        @dbus.service.signal(BUS_NAME)
        def self_changed_nick(self, nick):
            pass

        @dbus.service.signal(BUS_NAME)
        def psm_changed(self, email, pm):
            pass

        @dbus.service.signal(BUS_NAME)
        def status_changed(self, email, status):
            pass
            
        @dbus.service.signal(BUS_NAME)
        def unread_messages(self, count):
            pass

except Exception, e:
    dbusError = e

def debug(string):
    print string
