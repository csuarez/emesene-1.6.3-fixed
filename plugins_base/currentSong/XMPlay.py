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
import ctypes
user = ctypes.windll.user32

import CurrentSong
from emesenelib import *

class XMPlay( CurrentSong.CurrentSong ):

    def __init__( self ):
        CurrentSong.CurrentSong.__init__( self )
        self.xmplay = None
        self.isRunning()
        self.currentSong = ''
        self.template = "XMPlay\\0Music\\01\\0{0}\\0%s\\0\\0"
        
    def isPlaying( self ):
        if self.xmplay:
            st = ctypes.create_unicode_buffer(100)
            user.GetWindowTextW(self.xmplay, st, 100)
            return st.value != 'XMPlay'
        else:
            return False
        
    def isRunning( self ):
        try:
            xmplayClassName = ctypes.c_wchar_p('XMPLAY-MAIN')
            self.xmplay = user.FindWindowW(xmplayClassName, None)
            return self.xmplay != 0
        except: 
            return False

    def getCurrentSong( self ):
        return self.currentSong

    def check( self ):
        if not self.isRunning(): 
            self.currentSong = ""
            return True
        if self.isPlaying():
            st = ctypes.create_unicode_buffer(100)
            user.GetWindowTextW(self.xmplay, st, 100)
            string = st.value
            newCurrentSong = self.template % string
        else:
            newCurrentSong = ''

        if self.currentSong != newCurrentSong:
            self.currentSong = newCurrentSong
            return True
            
        return False
    
    def getStatus( self ):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> ( True , 'some message' )
        else -> ( False , 'error message' )
        '''
        
        if os.name != 'nt':
            return ( False, 'This plugin only works on windows systems' )
        
        return ( True, 'Ok' )
