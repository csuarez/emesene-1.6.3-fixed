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
import gtk
import gobject
import tempfile

import Plugin

class MainClass(Plugin.Plugin):
    '''Main plugin class'''
    description = _('Take screenshots and send them with /screenshot [save] [<seconds>]')
    authors = { 'Dx' : 'dx@dxzone.com.ar',
                'arielj' : 'arieljuod@gmail.com'}
    website = 'http://www.dxzone.com.ar'
    displayName = _('Screenshots')
    name = 'Screenshots'

    def __init__( self, controller, msn ):
        '''Constructor'''

        Plugin.Plugin.__init__( self, controller, msn )
        
        self.config = controller.config
        self.config.readPluginConfig(self.name)

        self.controller = controller
        self.slash = controller.Slash
        self.msn = msn
        
        self.root = gtk.gdk.get_default_root_window()

    def start( self ):
        '''start the plugin'''
        self.slash.register('screenshot', self.screenshot, \
            _('Takes screenshots') )

        self.enabled = True

    def screenshot( self, slashAction ):
        params = slashAction.getParams().split()
        
        save = False
        delay = 0
        
        # parse parameters
        for param in params:
            if param == 'save':
                save = True
            elif param.isdigit():
                delay = int(param)
        
        if not save:
            if self.config.getPluginValue(self.name, 'tip', '0') == '0':
                slashAction.outputText( \
                    _('Tip: Use "/screenshot save <seconds>" to skip the upload '))
                self.config.setPluginValue(self.name, 'tip', '1')
    
        if delay > 0:
            slashAction.outputText(_('Taking screenshot in %s seconds') % delay)
            gobject.timeout_add(delay * 1000, lambda: self.do(slashAction, save))
        else:
            self.do(slashAction, save)

    def do(self, slashAction, save):
        temp = tempfile.mkstemp(prefix='screenshot', suffix='.png')
        os.close(temp[0])

        # überfast screenshots! 1.9secs in my pentium II 350mhz
        # er.. yes, that's fast.. try running import
        size = self.root.get_size()
        colormap = self.root.get_colormap()
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, *size)
        pixbuf.get_from_drawable(self.root, colormap, 0, 0, 0, 0, *size)
        pixbuf.save(temp[1], 'png')
            
        if not save:
            slashAction.conversation.sendFile(temp[1])
        else:
            slashAction.outputText( _('Temporary file:') + ' ' + \
                temp[1] )

    def stop( self ):    
        '''stop the plugin'''
        self.slash.unregister('screenshot')
        self.enabled = False

    def check( self ):
        return ( True, 'Ok' )
