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

import urllib
import base64
import hashlib
import os

class MsnObjectsManager(object):
    def __init__( self, user ):
        self.user = user
        self.objects = {}
        self.idToContext = {}
    
    def getByContext( self, context ):
        tmp = base64.b64decode( context )
        if not tmp.endswith( '\0' ):
            context = base64.b64encode( tmp+'\0' )
        if self.objects.has_key(context):
            return self.objects[context]
        else:
            return None
        
    def getIds( self ):
        return self.idToContext.keys()
        
    def getById( self, id ):
        return self.getByContext( self.idToContext[id] )
        
    def create( self, id, filename, type ):
        #msnobj = Msnobj.Msnobj( self.user, size, Msnobj.Msnobj.CUSTOM_EMOTICON, name, data = f.read() )
        f = file( filename, 'rb' )
        f.seek( 0,2 )
        size = f.tell()
        f.seek( 0,0 )
        name = filename.split( os.sep )[ -1: ][ 0 ]
        msnobj = Msnobj( self.user.lower(), size, type, "0", data = f.read(), filename=filename, friendly=id )
        f.close()
        context = base64.b64encode( str( msnobj )+ '\0' )
        self.objects.update( {context:msnobj} )
        if id !='': self.idToContext.update( {id:context} )
        return msnobj
        
    def remove( self, id=None, context=None ):
        try:
            if id != None:
                context = self.getById( id )
                self.idToContext.pop( id )
            self.objects.pop( context )
        except: pass
                
class Msnobj( object ):
    '''this class represent the msnobject, for example:
    <msnobj Creator="buddy@hotmail.com" Size="24539" Type="3" Location="TFR2C.tmp" Friendly="AAA=" SHA1D="snip" SHA1C="snip"/>
    wlm CE:
    spoo    <msnobj Creator="buddy@hotmail.com" Type="2" SHA1D="87YzhijLQyyp4iIlL2k9LlB2wr0=" Size="1169" Location="0" Friendly="cwBwAG8AbwAAAA=="/>
    *  2: Custom Emoticons
    * 3: Display Pictures
    * 5: Background Images
    * 7: Dynamic Display Pictures (Flash-animated DPs)
    * 8: Winks (short Flash animations)
    * 11: Voice Clips (Wave sounds)
    * 12: "SavedState" Property of Add-Ins
    * 14: MSNP15 Locations 
    '''
    
    CUSTOM_EMOTICON = 2
    DISPLAY_PICTURE = 3
    BACKGROUND_IMAGE = 4
    DYNAMIC_DISPLAY_PICTURE = 7
    WINK = 8
    VOICE_CLIP = 11
    SAVED_STATE_PROPERTY = 12
    LOCATION = 14
    
    def __init__( self, creator, size='', type='', location='', friendly='\x00', sha1c='', sha1d='', data='', filename='' ):
        '''#  Creator - This field indicates the person who made (and is sending) the object.
            # Size - The Size field contains the length of the file in bytes
            # Type - The Type field indicates what sort of image (or file) it is about. At the moment the following flags are known:

            * 2: Custom Emoticons
            * 3: Display Pictures
            * 5: Background Images
            * 7: Dynamic Display Pictures (Flash-animated DPs)
            * 8: Winks (short Flash animations)
            * 11: Voice Clips (Wave sounds)
            * 12: "SavedState" Property of Add-Ins
            * 14: MSNP15 Locations 

            # Location - The Location field contains the filename under which the picture (or file) will be (or has been) stored
            # Friendly - This field contains the name of the picture in Unicode (UTF-16) format. The string is then encoded with Base64. So far this field has only been seen used with Background Images and Winks. With other file types, its value is "AAA=" (the utf-16 null string, encoded with Base64).
            # SHA1D - The SHA1D field contains a SHA1 hash of the images data encoded in Base64. It will from now on be called the SHA1 Data field.
            # SHA1C - This field contains all previous fields hashed with SHA1, and then encoded in Base64'''
        #FIXME: that docstring sucks
        self.creator = creator
        self.size = size
        self.type = int(type)
        self.location = location
        self.friendly = friendly
        self.filename = filename

        self.data = data
        #for received msnobj
        
        if sha1d != '':
            self.sha1d = sha1d
            # always return the same sha1d, amsn requires this
            self.forceSha1d = True
        else:
            self.sha1d = self.makeSha1d() 
            self.forceSha1d = False
        
        if sha1c != '':
            self.sha1c = sha1c
        else:
            self.sha1c = self.makeSha1c()
        
    def __repr__( self ):
        friendly = base64.b64encode( unicode( self.friendly ).encode( 'utf-16' )[2:] )
        
        string = '<msnobj Creator="' + self.creator + '" '
        string += 'Size="' + str( self.size ) + '" Type="' + str( self.type ) + '" '
        string += 'Location="'+ self.location +'" '
        string += 'Friendly="' + friendly + '" '
        
        sha1d = ''
        if self.forceSha1d:
            sha1d = self.sha1d
        else:
            sha1d = self.makeSha1d()
        
        string += 'SHA1D="' + sha1d + '" SHA1C="' + self.makeSha1c() + '"/>'
        return string
    
    def makeSha1d( self ):
        h = hashlib.sha1(self.data)
        return base64.b64encode( h.digest() )
    
    def makeSha1c( self ):
        friendly = base64.b64encode( unicode( self.friendly ).encode( 'utf-16' )[2:] )
        
        string = 'Creator' + self.creator
        string += 'Size' + str( self.size ) + 'Type' + str( self.type )
        string += 'Location'+ unquote( self.location )
        string += 'Friendly' + friendly
        string += 'SHA1D' + self.sha1d

        h = hashlib.sha1(string)
        
        return base64.b64encode( h.digest() )
    
    def quote( self ):
        return urllib.quote( self.__repr__() )
    
    def getCreator( self ): #XXX: property
        return self.creator
    
    def setCreator( self, creator ):
        self.creator = creator
        
    def getType(self):
        return str( self.type )

    def __eq__(self, obj):
        status = True
        if not isinstance(obj, Msnobj):
            return False

        fields = ['creator', 'location', 'friendly', 'size', 'type',
                  'sha1c', 'sha1d']

        for field in fields:
            if getattr(self, field) != getattr(obj, field):
                #print "DEBUG msnobj %s differ: %s != %s" % (field,
                #    getattr(self, field),
                #    getattr(obj, field))
                status = False
        return status

    def __neq__(self, obj):
        return not (self == obj)
    
            
def unquote( msnobj ):    
    return urllib.unquote( msnobj )

def createFromString( string, quoted=True ):
    if string == '0': return None
    
    if quoted:
        msnobjStr = unquote( string )
    else:
        msnobjStr = string
    
    def getData( string, start, stop ):
        if start in string:
            return string.split( start )[1].split(stop)[0]
        else:
            # TODO: what to do when a field is not in the string?
            return ''
    
    try:
        creator = getData( msnobjStr, 'Creator="', '"' )
        size = getData( msnobjStr, 'Size="', '"' )
        _type = getData( msnobjStr, 'Type="', '"' )
        location = getData( msnobjStr, 'Location="', '"' )
        friendly = getData( msnobjStr, 'Friendly="', '"' )
        try:
            friendly = str( base64.b64decode( friendly ).decode( 'utf-16' ) )
        except:
            friendly = '\x00'
        sha1d = getData( msnobjStr, 'SHA1D="', '"' )
        sha1c = getData( msnobjStr, 'SHA1C="', '"' )
        
        return Msnobj(creator, size, _type, location, friendly, sha1c, sha1d)
    except Exception, e:
        print 'cant create msnobj from: ' + msnobjStr
        print str( e )
        return None

