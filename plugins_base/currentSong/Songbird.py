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

#    CurrentSong plugin extension for Songbird
#    Kevin J. <marcspitz(at)l2mystic.be>
#    Based on Adolfo J. Fitoria E. <adolfo.fitoria@gmail.com>'s Amarok2 plugin


VERSION = '0.1'
IFACE_NAME = 'org.mpris.songbird'
IFACE_PATH = '/Player'

import CurrentSong

class Songbird( CurrentSong.DbusBase ):

    def __init__(self):
        CurrentSong.DbusBase.__init__(self, IFACE_NAME, self.setInterface)

        try:
            self.iface
        except:
            self.iface = None
            self.playingNow = ''

    def setInterface(self):
        try:
            self.iface = self.bus.get_object(IFACE_NAME, IFACE_PATH)
        except:
            self.iface = None
            
    def isPlaying(self):
        if not self.iface or not self.isNameActive(IFACE_NAME):
            return False
        isPlayingiface = self.bus.get_object(IFACE_NAME, '/Player')
        if isPlayingiface:
            status = isPlayingiface.GetStatus()
            if status[0] == 0:
                return True
            else:
                return False
            
    def setCurrentSongData(self):
        if self.iface:
            if self.isPlaying():
                current_song = self.iface.GetMetadata()
                self.artist = current_song['artist']
                self.title = current_song['title']
                self.album = current_song['album']
            return self.parseStyle()

    def check(self):
        if not self.iface or not self.isNameActive(IFACE_NAME) or not self.isPlaying():
            self.title = ''
            self.artist = ''
            self.album = ''
            return True            

        if self.iface.GetMetadata()["title"] != self.title:
            self.setCurrentSongData()
            return True
        return False
