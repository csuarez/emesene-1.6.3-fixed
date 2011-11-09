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

# Consonance subplugin for CurrentSong plugin
# by sgesweb (sgesweb@gmail.com)

VERSION = '1.0'

import os
import commands

import CurrentSong

class Consonance( CurrentSong.CurrentSong ):
    customConfig = {
        'unknownArtistString': '[N/A]',
        'unknownTitleString': '[N/A]',
        'unknownAlbumString': '[N/A]'
    }
    
    def __init__( self ):
        CurrentSong.CurrentSong.__init__( self )

    def check(self):
        if self.isPlaying():
            self.title = commands.getoutput("consonance -c 2>/dev/null | grep '^title' | sed s/'^title: *'//")
            self.artist = commands.getoutput("consonance -c 2>/dev/null | grep '^artist' | sed s/'^artist: *'//")
            self.album = commands.getoutput("consonance -c 2>/dev/null | grep '^album' | sed s/'^album: *'//")
            if self.artist == '':
                self.artist = self.customConfig['unknownArtistString']
            if self.album == '':
                self.album = self.customConfig['unknownAlbumString']
            if self.title == '':
                self.title = self.customConfig['unknownTitleString']
            return True
        return False

    def isPlaying(self):
        if not self.isRunning():
            return False
        state = commands.getoutput("consonance -c 2>/dev/null | grep '^state' | sed s/'^.* '//")
        if state == "Paused" or state == "Stopped":
            return False
        return True

    def isRunning(self):
        if len(commands.getoutput("ps -C consonance --no-heading")) > 0:
            return True
        return False

    def getStatus( self ):
        if os.name != 'posix':
            return ( False, _( 'This plugin only works in posix systems' ) )
        return ( True, "OK" )
        
    def getCoverPath(self):
        return None
