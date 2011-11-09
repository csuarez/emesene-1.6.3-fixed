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

# Audacious subplugin for CurrentSong plugin
# by rescbr, Patrick Dessalle

VERSION = '0.2'
IFACE_NAME = 'org.atheme.audacious'
IFACE_PATH = '/org/atheme/audacious'
# Documentation for the dbus: http://svn.atheme.org/audacious/trunk/src/audacious/objects.xml

import os
import commands

import CurrentSong
 
class Audacious( CurrentSong.DbusBase ):

    def __init__( self ):
        # init for this class
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )
        
        try:
            self.iface
        except:
            self.iface = None # We don't run a recent Audacious with dbus support
            self.playingNow = '' # We'll use that variable to hold the filename as returned by Audacious
        
    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )
        
    def isPlaying( self ):
        if self.iface:
            return self.iface.Status() == "playing" #Note: self.iface.Playing() returns True even if it's paused
        else:
            return commands.getoutput("audtool2 playback-status") == "playing"

    # In this plugin we have to override isRunning and getStatus.
    # Audacious in old versions didn't use D-Bus and used an external
    # program called audtool2 to comunicate. Now newer versions can use D-Bus.
    # We support both.
    
    def isRunning( self ):
        if self.iface:
            return True
        version = commands.getoutput("audtool2 version")
        if version == "sh: audtool2: not found":
			return False
        if len(version) > 0:
            return True
        return False
        
    def getStatus( self ):
        '''check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> ( True , 'some message' )
        else -> ( False , 'error message' )'''

        if os.name != 'posix':
            return ( False, _( 'This plugin only works in posix systems' ) )

        # We can't work if we don't have D-Bus and there is no audtool2
        if self.bus == None and not self.is_on_path( 'audtool2' ):
            return ( False, _( 'audtool2 is not on the path and you don\'t have dbus enabled.' ) )
        
        return ( True, 'Ok' )

    def getCurrentSong( self ):
        if not self.iface:
            if self.isPlaying():
                song = commands.getoutput( "audtool2 current-song" )
                fsong = '\\0Music\\01\\0' + song + '\\0\\0'
                return fsong
            else:
                return ''
        else: #Use the parseStyle from the super class
            return self.parseStyle()
        
    def check( self ):
        if self.iface:
            if self.isPlaying():
                songPosition = self.iface.Position()
                artist = self.iface.SongTuple(songPosition, "artist") 
                title = self.iface.SongTuple(songPosition, "title") 
                album = self.iface.SongTuple(songPosition, "album") 
                if self.artist != artist or self.title != title or self.album != album:
                    self.artist = artist
                    self.title = title
                    self.album = album
                    self.filename = self.iface.SongTitle(songPosition)
                    return True
            else: # Just stopped, paused, ... set the data as empty strings
                if self.artist != "" or self.title != "" or self.album != "":
                    self.artist = ""
                    self.title = ""
                    self.album = ""
                    self.filename = ""
                    return True
        elif self.isPlaying():
            currentSong = self.getCurrentSong()
            if self.playingNow != currentSong:
                self.playingNow = currentSong
                return True
        elif self.playingNow != "": # Just stopped, paused ... set to an empty string
            self.playingNow = ""
            return True
        
        # Not playing or no changes
        return False
