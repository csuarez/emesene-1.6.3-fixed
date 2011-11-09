# -*- coding: utf-8 -*-
#  devloop.lyua.org - 03/2009
#  CurrentSong Emesene module for the Mesk audio player

VERSION = '1.0'
IFACE_NAME = 'net.nicfit.mesk.MeskApp.profile_default'
IFACE_PATH = '/net/nicfit/mesk/MeskApp/profile_default'

import CurrentSong

class Mesk( CurrentSong.DbusBase ):
    '''Mesk Interface'''

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )

        try: self.iface
        except: self.iface = None

    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )

    def setCurrentSongData( self ):
        if self.iface:
            self.title  = self.iface.get_current_title()
            self.artist = self.iface.get_current_artist()
            self.album  = self.iface.get_current_album()

    def isPlaying( self ):
        if not self.isNameActive(IFACE_NAME):
            return False
        if not self.iface:
            return False

        if self.iface.get_state() == "playing":
            return True
        else:
            return False

    def check( self ):
        if not self.isNameActive(IFACE_NAME):
            return False
        if not self.iface:
            return False

        if self.iface.get_state() == "playing":
          if self.iface.get_current_artist() != None and \
             self.iface.get_current_title() != None and \
             self.iface.get_current_album() != None:
                self.setCurrentSongData()
                return True

        return False
