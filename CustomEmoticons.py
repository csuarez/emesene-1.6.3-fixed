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

import os
import gtk
import hashlib
import shutil
import urllib

import paths
import Theme

class CustomEmoticons( object ):
    def __init__( self, config, controller ):
        self.config = config
        self.msnOM = controller.msn.getMsnObjectsManager()
        self.list = {}
        self.CEPath = self.config.getCustomEmoticonsPath()
        self.loadMap()
        self.theme = controller.theme

    def _checkShortcut(self, shortcut):
        ''' return ( retVal , msg ) false = Error '''
        if shortcut == '':
            return( False, _( "Shortcut is empty" ) ) # sorry translators

        if shortcut in self.theme.getSingleSmileysList() or  \
           shortcut in self.list:
            return( False, _( "Shortcut already in use" ) )

        return ( True, '' )
    
    def create(self, shortcut, filename, size=0):
        shortcut = shortcut.replace(' ','')
        
        ret, msg = self._checkShortcut(shortcut)
        
        if not ret:
            return ( ret ,msg )
        if gtk.gdk.pixbuf_get_file_info(filename) == None:
            return ( False , _('No Image selected') )
        
        size_tab = (19,50)

        if size > 1:
            size = 1
        
        type = 'png'
        if gtk.gdk.pixbuf_get_file_info(filename)[0]['name'] == 'gif':
            pixbufAni = gtk.gdk.PixbufAnimation( filename )
            if pixbufAni.is_static_image():
                pixbuf = pixbufAni.get_static_image()
            else:
                type = 'gif'
                # TODO: resize gif
                #if pixbufAni.get_height() > size_tab[2] or\
                #    pixbufAni.get_width() > size_tab[2]:
                #    return ( False, _( "Gif animation too Large" ) )
        
        if type != 'gif':
            pixbuf = gtk.gdk.pixbuf_new_from_file( filename )
            if pixbuf.get_width() > size_tab[size] and \
               pixbuf.get_height() > size_tab[size]:
                pixbuf = Theme.resizePixbuf( pixbuf, size_tab[size], size_tab[size] )

        f = open(filename, 'rb')
        hash = hashlib.sha1(f.read()).hexdigest()
        f.close()
        
        dest = self.CEPath + paths.DIR_SEP + pathquote(shortcut) + '.' + \
            hash + '.' + type
        if type == 'gif':
            shutil.copyfile( filename, dest )
        else:
            pixbuf.save( dest, type )
        self.msnOM.create( id=shortcut, filename=dest, type=2 )
        self.list.update( {shortcut:dest} )
        self.saveMap()
        return ( True, '' )
            
    def delete( self, shortcut ):
        os.remove( str( self.list[shortcut] ) )
        self.list.pop( shortcut )
        self.msnOM.remove( shortcut )
        self.saveMap()
            
    def chageShortcut( self, shortcut, newShortcut ):

        if shortcut == newShortcut:
            return ( True, '')
        
        ret,msg = self._checkShortcut(newShortcut)
        
        if not ret:
            return ( ret , msg )

        emoPath = self.list[shortcut]
        
        self.list.pop( shortcut )
        self.list[newShortcut] = emoPath
        
        self.msnOM.remove( shortcut )
        self.msnOM.create( id=newShortcut, filename=emoPath, type=2 )
        
        self.saveMap()
        return ( True, '')
        
    def saveMap( self ):
        try:
            map = open(self.CEPath + paths.DIR_SEP + "map", "w")
        
            for k, v in self.list.iteritems():
                map.write(k + '\n' + v + '\r\n')

            map.close()
        except Exception, e:
            print 'exception writing config:\n'
            print e
            
    def loadMap( self ):
        smileysmap = self.CEPath + paths.DIR_SEP + "map"
        self.list = {}
        try:
            if os.path.exists(smileysmap):
                map = open(smileysmap, "r")
                string = map.read()
                map.close()
                for i in string.split( '\r\n' ):
                    if i != '':
                        try:
                            k,v = i.split( '\n' )
                            self.msnOM.create( id=k, filename=v, type=2 )
                            self.list.update( {k:v} )
                        except:
                            print 'Error reading smiley in map file', {k:v}
            else:
                print "File %s does not exist, skipping" %smileysmap
        except:
            print 'Error reading all smiley in map file', smileysmap
        return self.list

def pathquote(filename):
    '''Returns a safe url-quoted filename'''

    # if you don't trust me, use
    # [chr(x) for x in range(256) if not
    #  urllib.quote(chr(x)).startswith("%")]

    return urllib.quote(filename).replace("/", "%2f")

