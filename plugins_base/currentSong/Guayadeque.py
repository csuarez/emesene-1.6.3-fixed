VERSION = '0.1'
IFACE_NAME = 'org.mpris.guayadeque'
IFACE_PATH = '/Player'

import os
import CurrentSong

error = False

class Guayadeque ( CurrentSong.DbusBase ):
    '''guayadeque Interface'''

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try:
            self.iface
        except:
            self.iface = None
            self.playingNow = ''

    def setInterface( self ):
        self.iface = self.bus.get_object(IFACE_NAME, IFACE_PATH)

    def isPlaying( self ):
        isPlayingiface = self.bus.get_object(IFACE_NAME, '/Player')
        if isPlayingiface:
            status = isPlayingiface.get_dbus_method("GetStatus", dbus_interface='org.freedesktop.MediaPlayer')()
            if status[0] == 0:
                return True
            else:
                return False

    def getCurrentSong(self):
        if self.iface:
            if self.isPlaying():
                current_song = self.iface.get_dbus_method("GetMetadata", dbus_interface='org.freedesktop.MediaPlayer')()
                self.artist = current_song['artist']
                self.title = current_song['title']
                self.album = current_song['album']
            return self.parseStyle()

    def check(self):
        if self.isPlaying():
            current_song = self.iface.get_dbus_method("GetMetadata", dbus_interface='org.freedesktop.MediaPlayer')()
            if self.artist != current_song['artist'] or \
                    self.title != current_song['title']:
                        self.artist = current_song['artist']
                        self.title = current_song['title']
                        self.album = current_song['album']
                        return True
            else:
                return False

    def getCoverPath(self):
        if self.iface and self.isNameActive(IFACE_NAME):
            dict = self.iface.get_dbus_method("GetMetadata", dbus_interface='org.freedesktop.MediaPlayer')()
            if dict.has_key('arturl'):
                print dict['arturl']
                return dict['arturl'].replace('file://','')
            return None
        else:
            return None

