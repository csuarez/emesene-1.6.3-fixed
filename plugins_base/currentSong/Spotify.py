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

# based on pilt-spotify
# created by X1sc0

VERSION = '0.1'

import CurrentSong
import os

class Spotify( CurrentSong.CurrentSong ):
    '''Spotify interface'''
    
    def __init__( self ):
               
        CurrentSong.CurrentSong.__init__( self )

        self.artist = ''
        self.title = ''
        
        
    def getStatus( self ):
        
        if os.name != 'posix':
            return ( False, _( 'This plugin only works in posix systems' ) ) #no posix here
        
        return ( True, 'Ok' ) #ok, run baby
    
    def isRunning( self ):
        strout = os.popen("xwininfo -root -tree", "r")
        
        for line in strout.readlines():
            if "(\"spotify.exe\" \"Wine\")" in line:
                return True
        return False

    def check( self ):

        strout = os.popen("xwininfo -root -tree", "r")
        
        for line in strout.readlines():
            if "(\"spotify.exe\" \"Wine\")" in line:
                if "has no name" not in line:
                    if "\"Spotify\": (\"spotify.exe\" \"Wine\")" in line:
                        self.artist = ''
                        self.title = ''
                        return True
                    else:
                        aux = line
        try:
            text = aux.split(": (\"spotify.exe\"")
            text = text[0].split("\"Spotify -")
            text = text[1].split("\xe2\x80\x93")
            
            text[0] = text[0].strip()
            text[1] = text[1].strip()
            text[1] = text[1].rstrip('\"')
        
            if self.artist != text[0] or self.title != text[1].replace('\n',''):
                self.title = text[1].replace('\n','')
                self.artist = text[0]
                return True
        except:
            self.artist = ''
            self.title = ''
            return True
