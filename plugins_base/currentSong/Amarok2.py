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
#   
#    CurrentSong plugin extension for Amarok2
#    Adolfo J. Fitoria E. <adolfo.fitoria@gmail.com>


VERSION = '0.3'
IFACE_NAME = 'org.mpris.amarok'
IFACE_PATH = '/TrackList'

import os
import CurrentSong

error = False

class Amarok2( CurrentSong.DbusBase ):
    '''Amarok2 CurrentSong Plugin.'''

    def __init__(self):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try:
            self.iface
        except:
            self.iface = None
            self.playingNow = ''

    def setInterface( self ):
        self.iface = self.bus.get_object(IFACE_NAME, IFACE_PATH)

    def isPlaying( self ):
        if self.iface:
            isPlayingiface = self.bus.get_object(IFACE_NAME, '/Player')
            if isPlayingiface:
                status = isPlayingiface.GetStatus()
                if status[0] == 0:
                    return True
                else:
                    return False
        return False
            
    def check(self):
        if self.isPlaying():
            current_track = self.iface.GetCurrentTrack()
            current_song = self.iface.GetMetadata(current_track)
            if self.artist != current_song['artist'] or \
                    self.title != current_song['title']:
                        self.artist = current_song['artist']
                        self.title = current_song['title']
                        self.album = current_song['album']
                        return True
            else:
                return False

