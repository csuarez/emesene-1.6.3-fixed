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

from os import name
if name == 'posix':
    from Amarok import Amarok
    from Amarok2 import Amarok2
    from Audacious import Audacious
    from Banshee import Banshee
    from Clementine import Clementine
    from Consonance import Consonance
    from Exaile import Exaile
    from Gmusicbrowser import Gmusicbrowser
    from Guayadeque import Guayadeque    
    from LastFm import LastFm
    from Listen import Listen
    from Mesk import Mesk
    from QuodLibet import QuodLibet
    from Rhythmbox import Rhythmbox
    from Vagalume import Vagalume
    from Vlc import Vlc
    from Xfmedia import Xfmedia
    from Songbird import Songbird
    from Spotify import Spotify
    from Xmms import Xmms
    from Xmms2 import Xmms2
else:
    from AIMP2 import AIMP2
    from aTunes import aTunes
    from Foobar2000 import Foobar2000
    from GOMPlayer import GOMPlayer
    from MediaMonkey import MediaMonkey
    from MediaPlayerClassic import MediaPlayerClassic
    from OneByOne import OneByOne
    from RealPlayer import RealPlayer
    from SMPlayer import SMPlayer
    from Winamp import Winamp
    from XMPlay import XMPlay

# can stay out, since it uses sockets
from Mpd import Mpd
    
from CurrentSong import CurrentSong

del name
