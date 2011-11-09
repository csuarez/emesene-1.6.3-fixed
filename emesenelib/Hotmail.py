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
import hashlib
import common
from time import time

import paths

class Hotmail:
    def __init__( self, msn, config ):
        self.user = msn.user
        self.password = common.escape(msn.password)
        self.MSPAuth = msn.MSPAuth
        self.dg = msn.demographics
        self.config = config
        
    def getLoginPage( self, MessageURL=None , PostURL=None, id='2' ):
        if PostURL == None:
            if self.user.split('@')[1] == 'msn.com':
                PostURL = 'https://msnia.login.live.com/ppsecure/md5auth.srf?lc=' + self.dg['lang_preference']
            else:
                PostURL = 'https://login.live.com/ppsecure/md5auth.srf?lc=' + self.dg['lang_preference']
               
        if MessageURL == None:
            MessageURL = "/cgi-bin/HoTMaiL"
           
        sl = str( int ( time() ) - int( self.dg['LoginTime'] ) )
        auth = self.MSPAuth
        sid = self.dg['sid']
        cred =  hashlib.md5( auth + sl + self.password ).hexdigest()

        templateData = {
        'id':id,
        'site':PostURL,
        'login': self.user.split('@')[0],
        'email':self.user,
        'sid':sid,
        'kv':'',
        'sl':sl,
        'url':MessageURL,
        'auth':auth,
        'creds':cred
        }
        
        return self.parseTemplate( templateData )
        
    def getProfilePage( self, user ):
        pass
        
    def parseTemplate( self, data ):
        f = open(paths.APP_PATH + os.sep + 'hotmlog.htm')
        hotLogHtm = f.read()
        f.close()
        for key in data:
            hotLogHtm = hotLogHtm.replace( '$'+key, data[ key ] )

        self.file = os.path.join(
            self.config.getUserConfigPath(), 'cache', 'login.htm')
        
        tmpHtml = open( self.file, 'w' )
        tmpHtml.write( hotLogHtm )
        tmpHtml.close()
        
        return 'file:///' + self.file
        
