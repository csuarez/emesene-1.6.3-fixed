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

# based on Listen.py plugin

VERSION = '0.0'
IFACE_NAME = 'org.spuriousinterrupt.Xfmedia0'
IFACE_PATH = '/org/spuriousinterrupt/Xfmedia/0'

import CurrentSong
import re


class Xfmedia( CurrentSong.DbusBase ):
    '''Communicate with GNOME's Listen player'''
    
    def __init__(self):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try: self.iface
        except: self.iface = None

    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )
        
    def check(self):
        if not self.iface or not self.isNameActive(IFACE_NAME):
            return
        
        message = self.iface.NowPlaying()
        
        # process the received string. it's built this way:
        #  <m_track> - (<m_album> - <m_artist>)
        
        if message != "":
            title = message[1]
            
            if title != self.title:
                self.title = title
                return True
            else:
                return False
            
    def isPlaying(self):
        if not self.isRunning(): return False
        if not self.iface: return False
        try:
            self.iface.NowPlaying()
        except:
            return False
        return True
        
    def isRunning(self):
        return self.isNameActive(IFACE_NAME)
