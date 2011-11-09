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
import re
import gtk
import pango
import poplib
import gobject

import Plugin

class MainClass( Plugin.Plugin ):

    description = _('A gmail notifier')
    authors = { 'Jacopo Lamanna' : 'jazzenco@fastwebnet.it' }
    website = 'www.jazzenco.org'
    displayName = _('gmailNotify')
    name = 'gmailNotify'
    def __init__( self, controller, msn ):
        Plugin.Plugin.__init__( self, controller, msn )

        self.description = _('A gmail notifier')
        self.authors = { 'Jacopo Lamanna' : 'jazzenco@fastwebnet.it' }
        self.website = 'www.jazzenco.org'
        self.displayName = _('gmailNotify')
        self.name = 'gmailNotify'
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
            '''create the gui look'''
            self.Mbox = gtk.HBox(homogeneous=False, spacing=5)
            self.controller.mainWindow.vbox.pack_start(self.Mbox, False, False)
            self.Mbox.show_all()
            self.button = gtk.Button()
            self.button.set_relief(gtk.RELIEF_NONE)
            self.img = gtk.Image()
            self.mailIcon = self.controller.theme.getSmiley( "(e)" )
            self.img.set_from_animation(self.mailIcon)
            self.img.set_pixel_size(10)
            self.button.set_image(self.img)
            self.button.connect("clicked", self.Mcheck , None)
            self.button.set_tooltip_text(_('Click here to checked your mail'))
            self.Mbox.pack_start(self.button, False, False)
            self.button.show_all()
            
            self.Tbutton = gtk.Button()
            self.Tbutton.connect("clicked", self.Client , None)
            self.Tbutton.set_tooltip_text(_('Click here to access your mail'))
            self.Mtext = gtk.Label(_("Not checked yet."))
            self.Mtext.set_ellipsize( pango.ELLIPSIZE_END )
            self.Mtext.set_use_underline(True)
            self.Tbutton.add(self.Mtext)
            self.Tbutton.set_relief(gtk.RELIEF_NONE)
            self.Tbutton.show_all()
            self.Mbox.pack_start(self.Tbutton, True, True)
            self.Mtext.show_all()
            
            self.isbutt = 1
        
        self.Mcheck( None , None)
        
        self.interval = 60*1000*int(self.config.getPluginValue( self.name, 'time', '5' ))
        self.source_id = gobject.timeout_add(self.interval, self.Mcheck, self , None)

    def Client( self , widget , data=None):
        os.popen(self.config.getPluginValue( self.name, 'client', 'thunderbird' )+" &")
    
    def Mcheck( self , widget , data=None):
        if not self.checking:
            self.checking = True
            self.Mtext.set_label( _('Checking') )
            self.deffun( data )
            
        return True
        
    def function( self, data ):
        mail = ""
        numMes = '0'
        err2 = 0
        try:
            server = poplib.POP3_SSL('pop.gmail.com', 995)
            server.user(self.config.getPluginValue( self.name, 'user','user'))
            server.pass_(self.config.getPluginValue( self.name, 'pass','*****'))
        except:
            numMes = "error"
            #print "error"
        else:
            numMes = server.stat()[0]
            
            if int(numMes) <= 5:
                numList = range(int(numMes)) 
            else:
                numList = range(int(numMes - 5), int(numMes)) 
                
            for i in numList:
                mm = None
                try:
                    mm = str(server.top(i+1, 0))
                    mail = mail + re.search('(From).*?(?=\',)'  , mm).group(0) + "\n" + \
                                re.search('(Subj).*?(?=\',)'  , mm).group(0) + "\n\n"
                except Exception, exception:
                    print "error parsing mail: " + str( exception )
                    print mm, "for mail #" + str(i)
                    err2 = 1

            if int(numMes) > 5 and err2 == 0:
                mail = mail + "and more.."

        return (numMes,err2,mail)

    def callback( self, args ):
        self.checking = False
        numMes,err2,mail = args
        user = self.config.getPluginValue(self.name, 'user', 'user')
        if numMes == "error" :
            self.Mtext.set_label(_("Server error"))
        else:
            if int(numMes) >= 1:
                params = {'num': numMes, 'user': user}
                self.Mtext.set_label(_("%(num)s messages for %(user)s")%params)

                if err2 == 0:
                    self.Tbutton.set_tooltip_text(mail)
                else:
                    self.Tbutton.set_tooltip_text(_("Server error"))

            else:    
                self.Mtext.set_label( _("No messages for %s") % user)
                self.Tbutton.set_tooltip_text(_("No new messages"))
   
    def stop( self ):
        self.enabled = False
        gobject.source_remove(self.source_id)
        self.controller.mainWindow.vbox.remove( self.Mbox )
        self.isbutt = 0

    def check( self ):
        return ( True, 'Ok' )

    def configure( self ):
        dataM = []
        dataM.append(Plugin.Option('time', str, _('Check every [min]:'), '',\
            self.config.getPluginValue( self.name, 'time', '5' )) )
        dataM.append(Plugin.Option('client', str, _('Client to execute:'), '',\
            self.config.getPluginValue( self.name, 'client', 'thunderbird' )))
        dataM.append( Plugin.Option( 'user', str, _('Username:'), '', self.config.getPluginValue( self.name, 'user', _('user'))) )
        
        #dataM.append( Plugin.Option( 'pass', str, 'password:', '',
        #   self.config.getPluginValue( self.name, 'pass', '*****')) )        
        
        self.confW = Plugin.ConfigWindow(_('Mail checker config'), dataM)
        
        #Let's keep the pass entry secret
        label = gtk.Label( _('Password:') )
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_width_chars( 20 )
        entry = gtk.Entry()
        entry.set_text(self.config.getPluginValue(self.name, 'pass', ''))
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
            self.config.setPluginValue(self.name, 'user', r['user'].value)
            self.config.setPluginValue(self.name, 'pass', passwd )
            self.config.setPluginValue(self.name, 'client', r['client'].value)
        #self.start()
        return True
        
