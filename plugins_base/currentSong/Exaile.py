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

VERSION = '0.3'
IFACE_NAME = 'org.exaile.Exaile'
IFACE_PATH = '/org/exaile/Exaile'
    
import CurrentSong, string

class Exaile( CurrentSong.DbusBase ):
    '''Exaile Interface'''
    
    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )
        
        try: self.iface
        except: self.iface = None
       
    def setInterface( self ):
        proxy_obj = self.bus.get_object( IFACE_NAME, IFACE_PATH )
        self.iface = self.module.Interface( proxy_obj, IFACE_NAME )

    def isPlaying(self):
        return self.iface.IsPlaying()

    def check( self ):
        if not self.isRunning():
            return False
        
        artist = ""
        title = ""
        album = ""
        
        if self.isPlaying():
            artist = self.iface.GetTrackAttr('artist')
            if artist == None:
                artist = ""
            
            title = self.iface.GetTrackAttr('title')
            if title == None:
                title = ""
            
            album = self.iface.GetTrackAttr('album')
            if album == None:
                album = ""
            
        if self.artist != artist or self.title != title or self.album != album:
            self.artist = artist
            self.title = title            
            self.album = album
            return True

        return False

