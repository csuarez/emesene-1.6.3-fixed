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
from ctypes import *
from ctypes.wintypes import *
user = windll.user32

import CurrentSong
from emesenelib import *


_window = None

WNDENUMPROC=WINFUNCTYPE(BOOL, HWND, LPARAM)

@WNDENUMPROC
def EnumWindowsCallbackFunc(hwnd,lParam):
    global _window
    st = create_unicode_buffer(100)
    user.GetClassNameW(hwnd,st,100)
    user.GetWindowTextW(hwnd,st,100)
    if st.value.find("foobar2000") != -1:
        _window = hwnd
    return True #Allow windows to keep enumerating

class Foobar2000( CurrentSong.CurrentSong ):

    def __init__( self ):
        CurrentSong.CurrentSong.__init__( self )
        self.isRunning()
        self.foobarwindow = None
        self.currentSong = ''
        self.template = "Foobar2000\\0Music\\01\\0{0}\\0%s\\0\\0"
        
    def isPlaying( self ):
        st = create_unicode_buffer(100)
        user.GetWindowTextW(self.foobarwindow,st,100)
        return not st.value.startswith("foobar2000")

    def isRunning( self ):
        global _window
        user.EnumWindows(EnumWindowsCallbackFunc,0)
        if _window is not None:
            self.foobarwindow = _window
            return True
        else:
            return False

    def getCurrentSong( self ):
        return self.currentSong

    def check( self ):
        if not self.isRunning(): 
            self.currentSong = ""
            return True
        if self.isPlaying():
            st = create_unicode_buffer(100)
            user.GetWindowTextW(self.foobarwindow, st, 100)
            index = st.value.rfind("foobar2000")
            # stadard ui adds "  [foobar2000 v1.0.3]" at the end
            # columns ui adds " - foobar2000" at the end, that's the -3 for
            string = st.value[:index-3]
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
