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

import re
import os
import gtk
import pango
import gobject

from imaplib import *

import Plugin

class MainClass( Plugin.Plugin ):

    description = _('An IMAP mail checker')
    authors = { 'Jacopo Lamanna' : 'jazzenco@fastwebnet.it', 
        'Astu': 'astu88 at gmail dot com' }
    website = 'www.jazzenco.org'
    displayName = _('mailChecker')
    name = 'mailChecker'
    def __init__( self, controller, msn ):
        Plugin.Plugin.__init__( self, controller, msn )

        self.description = _('An IMAP mail checker')
        self.authors = { 'Jacopo Lamanna' : 'jazzenco@fastwebnet.it',
            'Astu': 'astu88 at gmail dot com' }
        self.website = 'www.jazzenco.org'
        self.displayName = _('mailChecker')
        self.name = 'mailChecker'
        self.config = controller.config
        self.config.readPluginConfig(self.name)
        self.enabled = False
        self.controller = controller
        self.isbutt = 0
        self.checking = False
        
        self.deffun = Plugin.Function( self.function, self.callback )
        
    def start( self ):
            
        self.enabled = True
        if self.isbutt == 0 :
            #create the gui look
            self.Mbox = gtk.HBox(homogeneous=False, spacing=5)
            self.controller.mainWindow.vbox.pack_start(self.Mbox, False, False)
            self.Mbox.show_all()
            self.button = gtk.Button()
            self.button.set_relief(gtk.RELIEF_NONE)
            self.img = gtk.Image()
            self.mailIcon = self.controller.theme.getSmiley( '(e)' )
            self.img.set_from_animation(self.mailIcon)
            self.img.set_pixel_size(10)
            self.button.set_image(self.img)
            self.button.connect('clicked', self.Mcheck , None)
            self.button.set_tooltip_text(_('Click here to checked your mail'))
            self.Mbox.pack_start(self.button, False, False)
            self.button.show_all()
            
            self.Tbutton = gtk.Button()
            self.Tbutton.connect('clicked', self.Client , None)
            self.Tbutton.set_tooltip_text(_('Click here to access your mail'))
            self.Mtext = gtk.Label(_('Not checked yet.'))
            self.Mtext.set_ellipsize( pango.ELLIPSIZE_END )
            self.Mtext.set_use_underline(True)
            self.Tbutton.add(self.Mtext)
            self.Tbutton.set_relief(gtk.RELIEF_NONE)
            self.Tbutton.show_all()
            self.Mbox.pack_start(self.Tbutton, True, True)
            self.Mtext.show_all()
            
            self.isbutt = 1

        self.Mcheck( None , None )
        
        self.interval = 60*1000*int(self.config.getPluginValue(
            self.name, 'time', '5' ))
        self.source_id = gobject.timeout_add(self.interval, 
                self.Mcheck, self , None)
        # Are notifications enabled?
        self.notifications = bool(int(self.config.getPluginValue(self.name, \
            'notifications', '0' )))
             

    def Client( self , widget , data=None):
        os.popen(self.config.getPluginValue( self.name, 
            'client', 'thunderbird' )+' &')
    
    def Mcheck( self , widget , data=None):
        if not self.checking:
            self.checking = True
            self.Mtext.set_label( _('Checking') )
            self.deffun( data )
            
        return True
    
    def IMAP4_connect(self, server_name, use_ssl):
        '''chooses the righ connection depending on the parameter use_ssl'''
        if use_ssl == True: return IMAP4_SSL(server_name)
        else: return IMAP4(server_name)
    
    def function( self, data ):
        '''this function will run on a thread and the result will be passed
        to the callback function'''
        mail = ''
        numMes = '0'
        
        server_name = self.config.getPluginValue(self.name, 'server', '')
        user_name = self.config.getPluginValue(self.name, 'user', '' )
        password = self.config.getPluginValue(self.name, 'pass', '' )
        use_ssl = bool(int(self.config.getPluginValue(self.name, \
            'use_ssl', '1' )))

        try:
            try:
                server = self.IMAP4_connect(server_name, use_ssl)
                server.login(user_name, password) 
            except:
                if '@' in user_name:
                    old_server_name = server_name
                    user_name, server_name = user_name.split('@')
                    try:
                        server = self.IMAP4_connect(server_name, use_ssl)
                        server.login(user_name, password) 
                    except:
                        server = self.IMAP4_connect(old_server_name, use_ssl)
                        server.login(user_name, password) 
                else:
                    raise
        except:
            numMes = 'error'
        else:
            r = server.select()
            if r[0] == 'OK' :
                answer, data = server.search(None, "(UNSEEN)") # Get unread msgs
                # numList contains the identifiers of unread messages
                try: numList = [int(k) for k in data[0].split(' ')]
                except: numList = []
 
                numMes = len(numList) #number of unread messages
                
                numList = numList[-5:] # Consider only 5 newest
                numList.reverse() # newer messages first
                for i in numList:
                    m = re.search('.*(?=\r\n\r\n)', 
                            server.fetch(i, 
                                '(BODY[HEADER.FIELDS (FROM)])')[1][0][1])
                    mail = mail + m.group(0) + '\n'

                    m = re.search('.*(?=\r\n\r\n)', 
                            server.fetch(i, 
                                '(BODY[HEADER.FIELDS (SUBJECT)])')[1][0][1])
                    mail = mail + m.group(0) + '\n\n'
            else:
                numMes = 'error'
        
            if numMes != 'error' and numMes > 5:
                mail += _("and more..")
                
            #self.config.setPluginValue( self.name, 'numMes', numMes ) #why ???
            server.logout()
        return (numMes, mail)
        
    def callback( self, args ):
        numMes,mail = args
        self.checking = False
        if numMes == 'error' :
            self.Mtext.set_label(_('Server error'))
        else:
            if numMes >= 1 :
                params = {'num': numMes, 'user': self.config.getPluginValue(\
                    self.name, 'user','user')}
                self.Mtext.set_label(\
                    _('%(num)s new messages for %(user)s') % params)
                self.Tbutton.set_tooltip_text(mail)
                
                if self.notificationsAvailable() and self.notifications:
                    self.notification_plugin.notify('', _('New email messages'), \
                        _('There are %(num)s new messages for %(user)s') % params)
            else:
                self.Mtext.set_label( _('No new messages for %s') %  \
                    self.config.getPluginValue( self.name, 'user', 'user'))
                self.Tbutton.set_tooltip_text(_('No new messages'))
   
    def notificationsAvailable(self):
        '''Returns true if NotifyOsdImproved is available and enabled'''
        self.notification_plugin = \
            self.controller.pluginManager.getPlugin("NotifyOsdImproved")
        if self.notification_plugin and self.notification_plugin.enabled:
            return True
        else: return False
    
    def stop( self ):
        self.enabled = False
        gobject.source_remove(self.source_id)
        self.controller.mainWindow.vbox.remove( self.Mbox )
        self.isbutt = 0

    def check( self ):
        return ( True, 'Ok' )

    def configure( self ):
        dataM = []
        dataM.append( Plugin.Option( 'use_ssl', bool, _('Use SSL'), '', \
            bool(int(self.config.getPluginValue(self.name, 'use_ssl', '1' )))) )
        dataM.append( Plugin.Option( 'notifications', bool, \
            _('Email notification - requires: ') + _('NotifyOsdImproved'), '', \
            bool(int(self.config.getPluginValue(self.name, \
            'notifications', '0' )))) )
        dataM.append( Plugin.Option( 'time', str, _('Check every [min]:'), '',\
            self.config.getPluginValue( self.name, 'time', '5' )) )
        dataM.append( Plugin.Option( 'server', str, _('IMAP server:'), '', \
            self.config.getPluginValue( self.name, 'server', 'pop.test.com' )))
        dataM.append( Plugin.Option('client', str, _('Client to execute:'),'',\
            self.config.getPluginValue( self.name, 'client', 'thunderbird' )) )
        dataM.append( Plugin.Option( 'user', str, _('Username:'), '', \
            self.config.getPluginValue( self.name, 'user', _('user'))) )
        
        #dataM.append( Plugin.Option( 'pass', str, 'password:', '', self.config.getPluginValue( self.name, 'pass', '*****')) )        
        
        self.confW = Plugin.ConfigWindow( _('Mail checker config'), dataM)
        
        #Let's keep the pass entry secret
        label = gtk.Label( _('Password:') )
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_width_chars( 20 )
        entry = gtk.Entry()
        entry.set_text('')
        entry.set_visibility(False) #with this op.
        hbox = gtk.HBox()
        hbox.pack_start( label )
        hbox.pack_start( entry )
        self.confW.vbox.pack_start( hbox )
        self.confW.vbox.show_all()
        
        r = self.confW.run()
        passwd = str(entry.get_text())
        
        if r is not None:
            self.config.setPluginValue(self.name, 'time', r['time'].value)
            self.config.setPluginValue(self.name, 'server', r['server'].value)
            self.config.setPluginValue(self.name, 'user', r['user'].value)
            self.config.setPluginValue(self.name, 'pass', passwd )
            self.config.setPluginValue(self.name, 'client', r['client'].value)
            self.config.setPluginValue(self.name, 'use_ssl', str(int(r['use_ssl'].value)))
            self.notifications = r['notifications'].value
            self.config.setPluginValue(self.name, 'notifications', \
                str(int(self.notifications)))
                 
            
        #self.start()
        return True

