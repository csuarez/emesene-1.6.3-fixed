VERSION = '0.1'
IFACE_NAME = 'org.mpris.vlc'
IFACE_PATH = '/Player'

import CurrentSong

class Vlc ( CurrentSong.DbusBase ):
    '''vlc Interface'''

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try: self.iface
        except: self.iface = None

    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )

    def check(self):
        if not self.iface or not self.isNameActive(IFACE_NAME):
            if self.artist != '' or self.title != '' or self.album != '':
                self.artist = ''
                self.title = ''
                self.album = ''
                return True

        dict = self.iface.GetMetadata()
        title = dict.get('nowplaying', dict.get('title', '')) or ''
        album = dict.get('album', dict.get('title', '')) or ''
        artist = dict.get('artist', '') or ''

        #if no metadata set title to filename
        if not title and not album:
            title = dict.get('location','').split('/')[-1]

        if title != self.title or album != self.album or artist != self.artist:
            self.title = title
            self.album = album
            self.artist = artist
            return True

    def isPlaying(self):
        if not self.isRunning(): return False
        if not self.iface: return False
        return bool(self.iface.GetStatus())

    def isRunning(self):
        return self.isNameActive(IFACE_NAME)

    def getCoverPath(self):
        if self.iface and self.isNameActive(IFACE_NAME):
            dict = self.iface.GetMetadata()
            if dict.has_key('arturl'):
                return dict['arturl'].replace('file://','')
            return None
        else:
            return None

