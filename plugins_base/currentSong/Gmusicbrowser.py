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
#    Original version by Quentin Sculo
#    http://squentin.free.fr/gmusicbrowser/dokuwiki/doku.php?id=third_party_apps:emesene

VERSION = '0.2'
IFACE_NAME = 'org.gmusicbrowser'
IFACE_PATH = '/org/gmusicbrowser'

import CurrentSong

class Gmusicbrowser ( CurrentSong.DbusBase ):
    '''Gmusicbrowser Interface'''

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try: self.iface
        except: self.iface = None

    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )

    def isPlaying(self):
        if self.isRunning():
            return bool( self.iface.Playing() )
        return False

    def check(self):
        if not self.isRunning():
            return False

        info = { 'title':'', 'album':'', 'artist':'' }

        if self.isPlaying():
            info = dict(self.iface.CurrentSong())
        
        if info['title'] != self.title or info['album'] != self.album or info['artist'] != self.artist:
            self.title = info['title']
            self.album = info['album']
            self.artist = info['artist']
            return True        
        return False

    def getCoverPath( self ):
        if self.isRunning() and len(self.album) > 0:
            return self.iface.GetAlbumCover(self.album)
        return None

