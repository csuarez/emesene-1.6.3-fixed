# -*- coding: utf-8 -*-
#
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

IFACE_NAME = 'net.sacredchao.QuodLibet'
IFACE_PATH = '/net/sacredchao/QuodLibet'

# interesting methods:
#  Next() - Previous() - Pause() - Play() - PlayPause()

import os
import CurrentSong

class QuodLibet( CurrentSong.DbusBase ):

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )
        try: self.iface
        except: self.iface = None
        
    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )
        
    def isPlaying( self ):
        return self.isNameActive( IFACE_NAME )
        
    def check( self ):
        if not self.iface:
            return False
    
        artist = ''
        title = ''
        album = ''
        filename = ''
        if self.isPlaying():
            data = dict(self.iface.CurrentSong())
            if 'title' in data: title = data['title']
            if 'album' in data: album = data['album']
            if 'artist' in data: artist = data['artist']
            if '~filename' in data:
                filename = data['~filename']
                filename = filename[filename.rfind('/') +1:-1]
        
        if self.artist != artist or \
           self.title != title or \
           self.filename != filename:
            self.artist = artist
            self.title = title
            self.album = album
            self.filename = filename
            return True

        return False
