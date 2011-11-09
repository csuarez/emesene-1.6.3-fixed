# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk

from Plugin import Plugin

class MainClass(Plugin):
    
    description = _('Shakes the window when a nudge is received.')
    authors = {unicode('Yguaratã C. Cavalcanti','latin-1').encode('latin-1') : 'yguarata at gmail dot com' }
    website = 'http://www.yguarata.org'
    displayName = _('Window Trembling Nudge')
    name = 'WindowTremblingNudge'

    def __init__(self, controller, msn):
        '''
        Contructor
        '''
        
        Plugin.__init__(self, controller, msn, 100)
        self.description = _('Shakes the window when a nudge is received.')
        self.authors = {unicode('Yguaratã C. Cavalcanti','latin-1').
            encode('latin-1') : 'yguarata at gmail dot com' }
        self.website = 'http://www.yguarata.org'
        self.displayName = _('Window Trembling Nudge')
        self.name = 'WindowTremblingNudge'
        self.shakeWindowId = None
        self.controller = controller
        self.base_movement = 10
        self.iterations = 30
    
    def start(self):
        self.enabled = True
        self.shakeWindowId = self.connect('nudge-received', 
            self.shakeWindow)
        
    def stop(self):
        '''stop the plugin'''
        if self.shakeWindowId is not None: self.disconnect(self.shakeWindowId)
        self.enabled = False
        
    def check(self):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> (True , 'some message')
        else -> (False , 'error message')
        '''
        
        return (True, 'Ok')
        
    def shakeWindow(self, msnp, mail):
        ''' search the window conversation and shake it '''
        win = None
        for switchboard in msnp.switchboards:
            if mail in switchboard.members:
                response = self.controller.conversationManager.getOpenConversation(mail, switchboard)
                if response is not None:
                    w, c = response
                    if w is not None:
                        win = w
                        break

        if win is None:
            return
                    
        x, y = win.get_position()
        #"Butterfly Nudge"
        for i in range(self.iterations):
            win.move(x+self.base_movement, y-self.base_movement) #-down+right
            #gtk.main_iteration() #why are these for? it's crashing emesene
            
            win.move(x+self.base_movement, y+self.base_movement) #+up+right
            #gtk.main_iteration()
            
            win.move(x-self.base_movement, y-self.base_movement) #-down-left
            #gtk.main_iteration()
            
            win.move(x-self.base_movement, y+self.base_movement) #+up-left
            #gtk.main_iteration()
            
            win.move(x, y) #start position
            #gtk.main_iteration()
