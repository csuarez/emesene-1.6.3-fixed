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

#    LastFm subplugin for CurrentSong plugin
#    by Loïc GRENON

VERSION = '0.1'

import CurrentSong
import xml.dom.minidom
import urllib
import time

class LastFm( CurrentSong.CurrentSong ):

	customConfig = {
		'Login': 'Difool80',
		'updateInterval': '60'
	}
	def __init__( self ):
		CurrentSong.CurrentSong.__init__( self )
		self.track = self._get_data()
		self.lastUpdate = 0

	def _get_data( self ):
		url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&api_key=fbb6f8beb8beb065baf549d57c73ac66&user=" + self.customConfig['Login'] + "&limit=1"
		f = urllib.urlopen(url)
		doc = xml.dom.minidom.parse(f)
		track = doc.getElementsByTagName('track')[0]
		return track

	def check( self ):
		if self.lastUpdate < ( time.time() - int(self.customConfig.get('updateInterval','60') ) ):
			self.track = self._get_data()
			self.lastUpdate = time.time()
			if self.track.getAttribute('nowplaying') == "true":
				artist = self.track.getElementsByTagName('artist')[0].childNodes[0].nodeValue
				title = self.track.getElementsByTagName('name')[0].childNodes[0].nodeValue
				album = self.track.getElementsByTagName('album')[0].childNodes[0].nodeValue
				if self.artist != artist or self.title != title or self.album != album:
					self.artist = artist
					self.title = title
					self.album = album
					return True
				else:
					return False
			else:
				self.artist = ''
				self.title = ''
				self.album = ''
				return True
		return False

	def isPlaying( self ):
		if self.track.getAttribute('nowplaying') == "true":
			return True
		return False

	def isRunning( self ):
		return True

	def getStatus( self ):
		if self.customConfig['Login'] == '':
			return ( False, 'No last.fm user set' )
		return ( True, 'Ok' )
