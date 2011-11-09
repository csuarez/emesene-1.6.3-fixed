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

VERSION = '1.0'
IFACE_NAME = 'org.bansheeproject.Banshee'
IFACE_PATH = '/org/bansheeproject/Banshee/PlayerEngine'

import CurrentSong

class Banshee( CurrentSong.DbusBase ):

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try: self.iface
        except: self.iface = None

    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )

    def setCurrentSongData( self ):
        if self.iface:
            info = self.iface.GetCurrentTrack()
            self.title = info["name"]
            self.artist = info["artist"]
            self.album = info["album"]

    def isPlaying( self ):
        if not self.iface or not self.isNameActive(IFACE_NAME):
            return False

        if self.iface.GetCurrentState() == "playing":
            return True
        else:
            return False

    def check( self ):          
        if not self.iface or not self.isNameActive(IFACE_NAME) or self.iface.GetCurrentState() == "paused":
            # I think this is a mistake, gives the error global name 'info'
            # is not defined, so I'll leave it commented.
            #self.title = info["name"]
            #self.artist = info["artist"]
            #self.album = info["album"]
            self.title = ""
            self.artist = ""
            self.album = ""
            return False

        if self.iface.GetCurrentTrack()["name"] != self.title:
            self.setCurrentSongData()
            return True
