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

# Right now we are not using gtk themes facilities
#
# We should consider using them at some point

import re
import os
import gtk.gdk
from shutil import copyfile

import paths
import emesenelib.common
from AvatarHistory import getLastCachedAvatar

ALTERNATIVE_SMILEYS = {\
    '<:o)':['<:O)'],
    '(a)' : ['(A)'],\
    ':@' : [':-@'],\
    '(b)' : ['(B)'] ,\
    '(z)' : ['(Z)'] ,\
    '(u)' : ['(U)'] ,\
    '(p)' : ['(P)'] ,\
    '(o)' : ['(O)'] ,\
    '(c)' : ['(C)'] ,\
    ':s' : [':S', ':-S', ':-s'] ,\
    ':|' : [':-|'] ,\
    '(d)' : ['(D)'] ,\
    '(e)' : ['(E)'] ,\
    ':$' : [':-$'] ,\
    '(g)' : ['(G)'] ,\
    '(x)' : ['(X)'] ,\
    '(h)' : ['(H)'] ,\
    '(i)' : ['(I)'] ,\
    '(m)' : ['(M)'] ,\
    ':D' : [':d', ':-d', ':-D', ':>', ':->'] ,\
    '(l)' : ['(L)'] ,\
    '(k)' : ['(K)'] ,\
    '(f)' : ['(F)'] ,\
    ':(' : [':-(', ':<', ':-<'] ,\
    ':)' : [':-)'] ,\
    ':p' : [':P', ':-P', ':-p'] ,\
    ':-O' : [':O', ':o', ':-o'] ,\
    '(t)' : ['(T)'] ,\
    '(n)' : ['(N)'] ,\
    '(y)' : ['(Y)'] ,\
    '(w)' : ['(W)'] ,\
    ';)' : [';-)'] ,\
    '(r)' : ['(R)'],\
    ':-[' : [':['],\
}


# TODO: map file
SMILEY_TO_NAME = [\
    (':)' , 'smile'),\
    (':D' , 'grin'),\
    (';)' , 'wink'),\
    (':-O' , 'oh'),\
    (':p' , 'tongue'),\
    ('(h)' , 'coolglasses'),\
    (':@' , 'angry'),\
    (':s' , 'confused'),\
    (':$' , 'blushing'),\
    (':(' , 'unhappy'),\
    (':\'(' , 'cry'),\
    ('(h5)' , 'Hi_five'),\
    ('(@)' , 'pussy'),\
    ('(&)' , 'Dog_face'),\
    ('''('.')''' , 'bunny'),\
    ('(tu)' , 'Turtle'),\
    (':|' , 'stare'),\
    ('(a)' , 'angel'),\
    ('(6)' , 'devil'),\
    ('8o|' , 'Baring_teeth_smiley'),\
    ('8-|' , 'face-glasses'),\
    ('+o(' , 'sick'),\
    ('<:o)' , 'party_smiley'),\
    ('|-)' , 'sleeping'),\
    ('*-)' , 'Thinking_smiley'),\
    (':-#' , 'Dont_tell_anyone'),\
    (':-*' , 'Secret_telling_smiley'),\
    ('(yn)' , 'Fingerscrossed'),\
    ('(bah)' , 'Black_sheep'),\
    ('(nah)' , 'goat'),\
    ('(sn)' , 'Snail'),\
    (':-[' , 'bat'),\
    ('^o)' , 'Sarcastic_smiley'),\
    ('8-)' , 'Eye_rolling_smiley'),\
    (':^)' , 'andy'),\
    ('(brb)' , 'brb'),\
    ('({)' , 'hugleft'),\
    ('(})' , 'hugright'),\
    ('(k)' , 'kiss'),\
    ('(f)' , 'flower'),\
    ('(w)' , 'brflower'),\
    ('(l)' , 'emblem-favorite'),\
    ('(u)' , 'brheart'),\
    ('(i)' , 'lamp'),\
    ('(8)' , 'audio-x-generic'),\
    ('(p)' , 'photo'),\
    ('(~)' , 'video-x-generic'),\
    ('(m)' , 'Messenger'),\
    ('(o)' , 'Clock'),\
    ('(e)' , 'mail'),\
    ('(t)' , 'Telephone_receiver'),\
    ('(mp)' , 'phone'),\
    ('(co)' , 'computer'),\
    ('(g)' , 'Gift_with_a_bow'),\
    ('(^)' , 'Birthday_cake'),\
    ('(z)' , 'Boy'),\
    ('(x)' , 'Girl'),\
    ('(y)' , 'thumbup'),\
    ('(n)' , 'thumbdown'),\
    ('(au)' , 'Auto'),\
    ('(ap)' , 'Airplane'),\
    ('(ip)' , 'Island_with_a_palm_tree'),\
    ('(mo)' , 'Money'),\
    ('(so)' , 'Soccer_ball'),\
    ('(c)' , 'coffee'),\
    ('(ci)' , 'Cigarette'),\
    ('(b)' , 'beer'),\
    ('(d)' , 'drink'),\
    ('(pl)' , 'Plate'),\
    ('(||)' , 'Bowl'),\
    ('(pi)' , 'Pizza'),\
    ('(S)' , 'weather-clear-night'),\
    ('(*)' , 'star'),\
    ('(#)' , 'weather-clear'),\
    ('(r)' , 'rainbow'),\
    ('(st)' , 'weather-showers-scattered'),\
    ('(li)' , 'weather-storm'),\
    ('(um)' , 'Umbrella'),\
    ('(%)' , 'cuffs'),\
    ('(xx)' , 'Xbox'),\
    ('*red+u' , 'im'),\
    ('*bgca' , 'im'),\
    ('*hsus' , 'im'),\
    ('*naf' , 'im'),\
    ('*mssoc' , 'im'),\
    ('*9mil' , 'im'),\
    ('*sierra' , 'im'),\
    ('*help' , 'im'),\
    ('*komen' , 'im'),\
    ('*unicef' , 'im'),\
]

ACCEPTED_FORMATS = ['png', 'gif', 'svg', 'xpm']

def resizePixbuf(pixbuf, height, width):
    pWidth, pHeight = pixbuf.get_width(), pixbuf.get_height()
    
    if pWidth == width and pHeight == height:
        return pixbuf
            
    destX = destY = 0
    destWidth, destHeight = width, height
    if pWidth > pHeight:
        scale = float(width) / pWidth
        destHeight = int(scale * pHeight)
        destY = int((height - scale * pHeight) / 2)
    elif pHeight > pWidth:
        scale = float(height) / pHeight
        destWidth = int(scale * pWidth)
        destX = int((width - scale * pWidth) / 2)
    else:
        return pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
    
    if scale == 1:
        return pixbuf
    
    scaled = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height)
    pixbuf.scale(scaled, 0, 0, width, height, \
                    destX, destY, scale, scale, \
                    gtk.gdk.INTERP_BILINEAR)
    return scaled

def sortedKeysByLen(adict, reverse=True):
    keys = adict.keys()
    keys.sort(lambda left, right: cmp(len(left),len(right)), reverse=reverse)
    return keys

class BaseTheme:
    '''Common functions to both theme classes'''

    def setTheme(self, name, small=False):
        '''Sets the current theme to the name given.
        In case of error, it will directly fallback to the default theme
        Returns True if the specified theme was correctly set, otherwise
        False'''
        
        if name == 'default' and not small:
            self.pixbufs = self.defaults
            self.path = self.defaultPath
            return True
        else:
            self.pixbufs = {}
        
        path = None
        smallFound = False
        SMALL_PATH = self.HOME_PATH + os.sep + '.' + name + 'Small'
        if small and os.path.isdir(SMALL_PATH):
            path = SMALL_PATH
            smallFound = True
        elif os.path.isdir(self.HOME_PATH + os.sep + name):
            path = self.HOME_PATH + os.sep + name
        elif os.path.isdir(self.SYSTEM_WIDE_PATH + os.sep + name):
            path = self.SYSTEM_WIDE_PATH + os.sep + name
        else:
            emesenelib.common.debug('Theme '+ name + 
                      ' couldn\'t be found where it was supposed to be')
            emesenelib.common.debug('Falling back to the default theme')
            self.path = self.defaultPath
            return False
        
        if small and not smallFound:
            if not os.path.isdir(SMALL_PATH):
                path = self.makeSmall(path, SMALL_PATH)
            else:
                path = path + 'Small'
        self.small = small
        self.path = path + os.sep
        return True
        
    def makeSmall(self, path, spath):
        return path

    def searchPixbuf(self, path, name, isLocation=False, pixbufCreator=None):
        '''Finds name in path with ACCEPTED_FORMATS extensions
        Returns location if found and if isLocation
        Else, return pixbufCreator(location)'''
        
        for extension in ACCEPTED_FORMATS:
            location = path + name + '.' + extension
            if isLocation:
                if os.path.exists(location):
                    return location
            else:
                try:
                    pixbuf = pixbufCreator(location)
                    return pixbuf
                except:
                    pass
        return None
        
    def getImage(self, name, animated=False):
        '''Returns a pixbuf of the requested image from the current theme
        If the requested image name is not found in the current theme, the
        default theme's corresponding image will be returned.
        If the default theme doesn't have such a image, None is returned'''
        
        # checks if already loaded
        if name in self.pixbufs: return self.pixbufs[name]
        
        # determines which pixbuf function is used to create it
        if animated:
            creator = gtk.gdk.PixbufAnimation
        else:
            creator = gtk.gdk.pixbuf_new_from_file
                
        pixbuf = self.searchPixbuf(self.path, name, pixbufCreator=creator)

        if pixbuf:
            # returns icon from theme
            self.pixbufs[name] = pixbuf
            return pixbuf

        #else, return icon from default theme
        if name in self.defaults:
            return self.defaults[name]

        self.defaults[name] = self.searchPixbuf(self.defaultPath, name, pixbufCreator=creator)
        return self.defaults[name]
                
    def getImageIcon(self, name, animated=False):
        '''Returns the location of the requested image from the current theme
        If the requested image name is not found in the current theme, the
        default theme's corresponding image will be returned.
        If the default theme doesn't have such a image, None is returned'''

        location = self.searchPixbuf(self.path, name, isLocation=True)
        if location:
            # returns icon from theme
            return location
        else:
            # will return icon from default theme
            return self.searchPixbuf(self.defaultPath, name, isLocation=True)

class Theme(BaseTheme):
    '''This class contains all the data related to a theme:
    images, icons, animations, path to sounds etc'''
    
    def __init__(self, config, name=None, sname='default'):
        '''Constructor'''
        
        self.config = config
        self.defaults = {}
        self.pixbufs = {}
        self.HOME_PATH = paths.THEME_HOME_PATH 
        self.SYSTEM_WIDE_PATH = paths.THEME_SYSTEM_WIDE_PATH
        self.defaultPath = paths.DEFAULT_THEME_PATH
        if name:
            self.setTheme(name)
        else:
            self.path = self.defaultPath
        
        self.smilies = SmilieTheme(self, sname)
        self.getSmileysList = self.smilies.getSmileysList
        self.getSmiley = self.smilies.getSmiley
        self.getSmileyPath = self.smilies.getSmileyPath
        self.smileyParser = self.smilies.smileyParser
        self.getSmileysList = self.smilies.getSmileysList
        self.getSingleSmileysList = self.smilies.getSingleSmileysList
    
    def statusToPixbuf(self, status, returnPix=True):
        '''Translates a status code in a pixbuf returning the according
        theme image'''
        
        name = None
        if status == 'NLN' or status == 'online':
            name = 'online'
        elif status == 'AWY' or status == 'away':
            name = 'away'
        elif status == 'BSY' or status == 'busy':
            name = 'busy'
        elif status == 'BRB' or status == 'brb':
            name = 'away'
        elif status == 'PHN' or status == 'phone':
            name = 'busy'
        elif status == 'LUN' or status == 'lunch':
            name = 'away'
        elif status == 'HDN' or status == 'invisible':
            name = 'invisible'
        elif status == 'IDL' or status == 'idle':
            name = 'idle'
        elif status == 'FLN' or status == 'offline':
            name = 'offline'
        # the following status are dummys
        elif status == 'DCD' or status == 'disconnected':
            name = 'trayicon'
        elif status == 'LOG' or status == 'login':
            name = 'trayicon2'

        if returnPix:
            return self.returnPixbuf(name)

        return name

    def returnPixbuf(self, name):
        if name:
            return self.getImage(name)
        else:
            return None
       
    def hasUserDisplayPicture(self, contact):
        '''return True if the user has a cached Display picture'''
        imagePath = os.path.join(self.config.getCachePath(), \
            contact.displayPicturePath)
        
        if (os.path.exists(imagePath) and os.path.isfile(imagePath)):
            return True
        else:
            return False
            
    # PLEASE KILL THIS METHOD
    def getUserDisplayPicture(self, contact, width=96, height=96, forceResize=False):
        '''return a pixbuf with the display picture of the user
        or the default image if not found'''
        
        imagePath = os.path.join(self.config.getCachePath(), \
            contact.displayPicturePath)
        
        try:
            if os.path.exists(imagePath) and os.path.isfile(imagePath):
                pixbuf = gtk.gdk.pixbuf_new_from_file(imagePath)
            else:
                lastCached=getLastCachedAvatar(contact.email, self.config.getCachePath())
                if os.path.isfile(lastCached):
                    pixbuf = gtk.gdk.pixbuf_new_from_file(lastCached)
                else:
                    pixbuf = self.getImage('login')
        except:
            pixbuf = self.getImage('login')

        if width == 96 and height == 96 and not forceResize:
            return pixbuf
        else:
            return resizePixbuf(pixbuf, width, height)

    def makeSmall(self, path, spath):
        os.mkdir(spath)
        try:
            for root, dirs, files in os.walk(path):
                del dirs
                if root != path: continue
                for file in files:
                    name = file.split('.')[0]
                    fullname = os.path.join(root, file)
                    destname = os.path.join(spath, file)
                    if name in ('away','brb','busy','icon','idle','lunch', \
                                'invisible','mobile','offline','online', \
                                'phone'):
                        pixbuf = resizePixbuf(gtk.gdk.pixbuf_new_from_file(fullname), 16, 16)
                        pixbuf.save(destname, 'png')
                    elif file.split('.')[1] in ACCEPTED_FORMATS:
                        copyfile(fullname,destname)
            return spath
        except Exception, e:
            print "Error creating small theme", e
            return path
    
class SmilieTheme(BaseTheme):

    def __init__(self, parent, name):
        '''Constructor'''
        
        self.theme = parent
        self.defaults = {}
        self.pixbufs = {}
        self.defaultPath = paths.DEFAULT_SMILIES_PATH
        self.HOME_PATH = paths.SMILIES_HOME_PATH
        self.SYSTEM_WIDE_PATH = paths.SMILIES_SYSTEM_WIDE_PATH
        if name:
            self.setTheme(name)
        else:
            self.path = self.defaultPath

        # sets up a dict with the different smiley shortcodes
        # that translates to smileys names
        self.smileyToName = {}
        smileyDict = dict(SMILEY_TO_NAME)
        for (key,value) in smileyDict.iteritems():
            self.smileyToName[key] = value
            
            if key in ALTERNATIVE_SMILEYS:
                for i in ALTERNATIVE_SMILEYS[key]:
                    self.smileyToName[i] = value
        smileyPattern = ''
        
        for smiley in sortedKeysByLen(self.smileyToName):
            smileyPattern += re.escape(emesenelib.common.escape(smiley)) + '|'
        self.reSmiley = re.compile('('+smileyPattern[:-1]+')')
    
    def smileyParser(self, text, callback=None):
        '''return text with smileys parsed in html
        you can set a callback to handle smileys parsing'''
        
        if callback == None:
            if os.name == 'posix':
                return self.reSmiley.sub(lambda data: '<img src="file://%s"/>'%self.getSmileyPath(emesenelib.common.unescape(data.groups()[0])), text)
            else:
                return self.reSmiley.sub(lambda data: '<img src="file://localhost/%s"/>'%self.getSmileyPath(emesenelib.common.unescape(data.groups()[0])), text)

        else:
            return self.reSmiley.sub(lambda data: callback(self.getSmileyPath(emesenelib.common.unescape(data.groups()[0]))), text)
    

    def getSmiley(self, shortcode, animated=True):
        '''Returns a pixbuf representing the corresponding smiley if we have one,
        otherwise None'''
            
        if shortcode in self.smileyToName:
            pixbuf = self.getImage(self.smileyToName[shortcode], animated)
            if not animated and type(pixbuf) == gtk.gdk.PixbufAnimation:
                pixbuf = pixbuf.get_static_image()
            return pixbuf
         
    def getSmileyPath(self, shortcode):
        '''Returns the path of the smiley if we have one,
        otherwise None'''
        
        if shortcode in self.smileyToName:
            return self.getImageIcon(self.smileyToName[shortcode], True)
        
    def getSmileysList(self):
        '''Returns a list of all the currently accepted smileys shortcodes'''
        
        return sortedKeysByLen(self.smileyToName)
    
    def getSingleSmileysList(self):
        '''Returns a list of the currently accepted smileys shortcodes,
        without repetitions, and sorted in the same order they appear'''
        
        smileyList = []
        for smiley, name in SMILEY_TO_NAME:
            smileyList.append(smiley)

        return (smileyList)
