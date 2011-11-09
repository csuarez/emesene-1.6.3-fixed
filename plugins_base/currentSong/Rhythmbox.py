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

# signal code:
# self.bus.add_signal_receiver( self.on_playing_uri_changed, \
#     'playingUriChanged', PLAYER_NAME, None, PLAYER_PATH )
# self.bus.add_signal_receiver( self.on_playing_changed, \
#     'playingChanged', PLAYER_NAME, None, PLAYER_PATH)
# self.bus.remove_signal_receiver( ... )

# based on plugin by Alberto Talavera

VERSION = '0.2'

#HELL_NAME = 'OMGWTFBBQ'
OBJECT_NAME = 'org.gnome.Rhythmbox'
PLAYER_NAME = 'org.gnome.Rhythmbox.Player'
PLAYER_PATH = '/org/gnome/Rhythmbox/Player'
SHELL_NAME = 'org.gnome.Rhythmbox.Shell'
SHELL_PATH = '/org/gnome/Rhythmbox/Shell'

import CurrentSong

class Rhythmbox( CurrentSong.DbusBase ):
    '''Rhythmbox interface'''
    
    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, OBJECT_NAME, self.setInterface )
        try: self.iface
        except: self.iface = None
        
        try: self.rbshell
        except: self.rbshell = None
        
        self.uri = ''
    
    def setInterface( self ):
        rbobj = self.bus.get_object( OBJECT_NAME, PLAYER_PATH )
        self.iface = self.module.Interface( rbobj, PLAYER_NAME )
        rbshellobj = self.bus.get_object( OBJECT_NAME, SHELL_PATH )
        self.rbshell = self.module.Interface( rbshellobj, SHELL_NAME )
        
    def setCurrentSongData( self, uri ):
        if not self.rbshell: return
        
        data = self.rbshell.getSongProperties( uri )
        self.title = data['title']
        self.artist = data['artist']
        self.album = data['album']
        self.uri = uri
    
    def check( self ):
        if not self.iface or not self.isNameActive(OBJECT_NAME) or not self.iface.getPlaying():
            self.setCurrentSongData( uri )
            return
        
        uri = self.iface.getPlayingUri()
        if uri != self.uri:
            self.setCurrentSongData( uri )
            return True
        return False
    
    def isPlaying( self ):
        if not self.iface:
            return False
        else:
            return bool( self.iface.getPlaying() )
