# Vagalume NowSong Plugin
# by Gemu - gemunet@gmail.com
# 
# ---------------------------------------------------------------------------------
# Part of code was extracted from
# Copyright (c) Thomas Perl <thpinfo.com>.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# ---------------------------------------------------------------------------------

VERSION = '1.0'
IFACE_NAME = 'com.igalia.vagalume'
IFACE_PATH = '/com/igalia/vagalume'

import CurrentSong

class CurrentTrack(object):
    def __init__(self):
        self.status = None
        self.artist = None
        self.title = None
        self.album = None
        self.changed = False

    def notify(self):
        self.changed = True
    
    def reset(self):
        self.changed = False

class Vagalume ( CurrentSong.DbusBase ):
    '''VAGALUME'''
    
    def __init__(self):
        self.current_track = CurrentTrack()
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )
        try: self.iface
        except: self.iface = None

    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )
        
    def check(self):
        if not self.isPlaying() or not self.isRunning():
            self.artist = ""
            self.title = ""
            self.album = ""
            return True

        if self.current_track.changed:
            self.artist = self.current_track.artist
            self.title = self.current_track.title
            self.album = self.current_track.album
            self.current_track.reset()
            return True

    def isPlaying(self):
        if not self.isRunning(): return False
        if not self.iface: return False

        if self.current_track.status == 'playing':
            return True
        else:
            return False
        
    def isRunning(self):
        return self.isNameActive(IFACE_NAME)

    def vagalume_status_changed(self, status, artist=None, title=None, album=None):
        if self.current_track is not None:
            self.current_track.status = status
            self.current_track.artist = artist
            self.current_track.title = title
            self.current_track.album = album
            self.current_track.notify()



