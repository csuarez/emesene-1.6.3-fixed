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
#    Using code from the xmms2 python tutorials

VERSION = '0.1'
ERROR = ''

# include xmmsclient module
try:
    import xmmsclient
except:
    ERROR = _('You need to install XMMS2 Python bindings (python-xmmsclient) to use this plugin')

import os

import CurrentSong

class Xmms2(CurrentSong.CurrentSong):

    def __init__( self ):
        CurrentSong.CurrentSong.__init__( self )
        self.connected = False
        self.status = 'not connected'
        self.xmms = xmmsclient.XMMS("emesene")
        self.id_song = 0

    def _connect( self ):        
        if not self.connected:
            self.log('info', _('trying to connect'))

            try:
                #self.xmms.connect(os.getenv("XMMS_PATH"))
                self.xmms.connect(None)
                self.log('info', _('connected'))
                self.status = 'connected'
                self.connected = True
                            
            except IOError, detail:
                self.connected = False
                self.log('error', detail)
                self.status = 'not connected'
        
    def start( self ):
        self._connect()
        
    def isPlaying( self ):
        self._connect()
        if not self.connected:
            return False
        result = self.xmms.playback_current_id()
        result.wait()
        if result.iserror():
            return False    
        if result.value() == 0:
            return False
        return True
        
    def isRunning( self ):
        self._connect()
        if not self.connected:
            return False
        result = self.xmms.playback_current_id()
        result.wait()
        if result.iserror():
            return False
        return True

    def getStatus( self ):
        if ERROR:
            return ( False, ERROR )
        
        return ( True, 'Ok' )
        
    def check( self ):        
        if not self.connected:
            self._connect()
        if not self.connected:
            return False
        result = self.xmms.playback_current_id()
        result.wait()
        if result.iserror():
            self.log('error',_('Can\'t get current song id'))
            return False
        old_id_song = self.id_song
        self.id_song = result.value()
        if self.id_song == 0:
            self.log('info',_('Nothing is playing'))
            if (old_id_song != self.id_song):
                self.artist = ''
                self.title = ''
                self.album = ''
                return True
            return False
        result = self.xmms.medialib_get_info(self.id_song)
        result.wait()
        if result.iserror():
            self.log('error',_('Can\'t find the song in media lib'))
            return False

        minfo = result.value()
    
        if (old_id_song != self.id_song):
            try:
                self.artist = minfo["artist"]
            except KeyError:
                self.artist = ''         
            try:
                self.title = minfo["title"]
            except KeyError:
                self.title = ''
            try:
                self.album = minfo["album"]
            except KeyError:
                self.album = ''
            return True
        return False
