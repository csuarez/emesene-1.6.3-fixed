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
import gc
import hashlib
import gtk
import ImageAreaSelector

class Avatar( object ):
    '''this class represent an avatar'''

    def __init__( self, controller, path, avatarsPath, dontCache=False,
                  height=96, width=96, thumbHeight=48, thumbWidth=48, 
                  resizeDialog=False ):
        self.controller = controller
        if path == '':
            self.noAvatar()
        elif not self.loadExisting(path):
            self.loadNew(path, avatarsPath, height, width, thumbHeight, 
                thumbWidth, resizeDialog)

    def loadNew( self, path, avatarsPath, height, width, thumbHeight, 
                 thumbWidth, resizeDialog ):
        self.height = height
        self.width = width
        self.thumbHeight = thumbHeight
        self.thumbWidth = thumbWidth

        pixbuf = gtk.gdk.pixbuf_new_from_file( path )
        if resizeDialog:
            areaSelector = ImageAreaSelector.ImageAreaSelectorDialog(self.controller, pixbuf)
            response, pixbuf = areaSelector.run()
            if response == gtk.RESPONSE_CANCEL:
                self.noAvatar()
                return

        self.image = self.scale( pixbuf, width, height ) 
        self.thumb = self.scale( pixbuf, thumbWidth, thumbHeight )

        imagePath = avatarsPath + os.sep + 'temp.png'
        thumbPath = avatarsPath + os.sep + 'temp_thumb.png'
        self.image.save( imagePath, 'png' )
        self.thumb.save( thumbPath, 'png' )
        
        f = file(imagePath, 'rb')
        hash = hashlib.sha1(f.read())
        f.close()
        self.imagePath = avatarsPath + os.sep + hash.hexdigest() + '.png'
        self.thumbPath = avatarsPath + os.sep + hash.hexdigest() + '_thumb.png'
        
        if not os.path.exists( self.thumbPath ):
            os.rename( thumbPath, self.thumbPath )
        else:
            os.remove( thumbPath )
            
        if not os.path.exists( self.imagePath ):
            os.rename( imagePath, self.imagePath )
        else:
            os.remove( imagePath )
            
        # TODO: instead of removing the old we could just not create the new ones..        
        if os.path.dirname( os.path.abspath( path ) ) == os.path.abspath( avatarsPath ):
            os.remove( path )
            
            thumbName = path.split( '.png' )[ 0 ] + '_thumb.png'
            
            try:
                os.remove( thumbName )
            except:
                print 'could not remove ' + thumbName

    def noAvatar(self):
        self.imagePath = ''
        self.thumbPath = ''       

        self.image = None 
        self.thumb = None

        self.height = 0
        self.width = 0
        self.thumbHeight = 0
        self.thumbWidth = 0

    def loadExisting( self, path ):
        self.imagePath = path
        self.thumbPath = path[:-4] + '_thumb.png'       

        try:
            self.image = gtk.gdk.pixbuf_new_from_file( self.imagePath ) 
            self.thumb = gtk.gdk.pixbuf_new_from_file( self.thumbPath ) 
        except:
            return False

        self.height = self.image.get_height()
        self.width = self.image.get_width()
        self.thumbHeight = self.thumb.get_height()
        self.thumbWidth = self.thumb.get_width()
        return True
            
    def getImagePath( self ):
        return self.imagePath
    
    def getThumbPath( self ):
        return self.thumbPath
    
    def getImage( self ):
        return self.image
    
    def getThumb( self ):
        return self.thumb

    def scale( self, image, width, height ):
        h,w = image.get_height(), image.get_width()
        width_max, height_max = width, height
        width=float( image.get_width() )
        height=float( image.get_height() )
        if ( width/width_max ) > ( height/height_max ):
            height=int( ( height/width )*width_max )
            width=width_max
        else:
            width=int( ( width/height )*height_max )
            height=height_max

        image = image.scale_simple( width, height, gtk.gdk.INTERP_BILINEAR )
        gc.collect() # Tell Python to clean up the memory
        return image
