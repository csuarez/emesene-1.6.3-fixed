# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gtk
import subprocess
from xml.dom import minidom
from Plugin import Plugin,Option,ConfigWindow
import desktop
import hashlib

class MainClass(Plugin):

    description = _('Show preview image and play the received winks.')
    authors = {'Jan de Mooij': 'jandemooij@gmail.com', \
               'Scantimplax':'scantimplax@hotmail.com', \
               'Nicolas Espina Tacchetti':'nicolasespina@gmail.com', \
               'arielj' : 'arieljuod@gmail.com'}
    website = ''
    displayName = _('Wink Receiving')
    name = 'WinkReceiving'
    def __init__(self, controller, msn):
        Plugin.__init__(self, controller, msn)

        self.msn = msn
        self.enabled = False

        self.winkCacheDir = os.path.join(self.msn.cacheDir,'winks')
        if not os.path.exists(self.winkCacheDir):
            os.mkdir(self.winkCacheDir)
        self.autoplay = False
        self.checkIfHasGnash()
        
        self.config = controller.config
        self.config.readPluginConfig(self.name)

    def start(self):
        self.wink_id = self.msn.connect('switchboard::wink', self.on_wink)
        self.wink_transferred_id = self.msn.connect('wink-transferred', \
                self.on_wink_transferred)
        self.autoplay = bool(int(self.config.getPluginValue(self.name, \
            'autoplay', False)))
        self.enabled = True

    def stop(self):
        self.msn.disconnect(self.wink_id)
        self.msn.disconnect(self.wink_transferred_id)
        
        self.enabled = False

    def check(self):
        # check if we have cabextract
        # nt uses extrac32.exe, which is there by default
        if os.name != "nt":
            try:
                subprocess.call(['cabextract'], #stderr=subprocess.PIPE, 
                    stdout=subprocess.PIPE)
            
            except OSError:
                return (False, _('cabextract not installed'))
        
        return (True, 'Ok')

    def checkIfHasGnash ( self ):
        if os.name != "nt":
            self.out=os.popen("which gnash").read()
            if self.out == "/usr/bin/gnash\n":
                #Have the command gnash
                self.hasGnash = True
            else:
                #Dont have the command gnash
                self.hasGnash = False
        else:
            self.hasGnash = False

    
    def get_conversation(self, switchboard):
        for conversation in self.getOpenConversations():
            if conversation.getSwitchboard() == switchboard:
                return conversation
        return None

    def playWink(self, path):
        if self.hasGnash == True:
            retval = subprocess.call(['gnash', '-1', path])
        elif os.name != "nt":
            retval = subprocess.call(['firefox',  path])
        else:
            desktop.open(path)
    
    def onplayWink(self,*args):
        self.playWink(args[1])

    def getThumbnail(self,xmlfile):
        xmldoc = minidom.parse(xmlfile)
        for item in xmldoc.getElementsByTagName('item'):
            if item.attributes["type"].value == "thumbnail":
                return item.attributes["file"].value

    def getSwf(self,xmlfile):
        xmldoc = minidom.parse(xmlfile)
        for item in xmldoc.getElementsByTagName('item'):
            if item.attributes["type"].value == "animation":
                return item.attributes["file"].value

    def winkEvent( self, img, event, attrs ):
        winkDir = os.path.join(self.winkCacheDir,attrs['class'])
        xmlfile = os.path.join(winkDir,'content.xml')
        if not os.path.exists(xmlfile):
            return
        if event.type == gtk.gdk.BUTTON_PRESS:
            menu = gtk.Menu()
            menu_items = gtk.ImageMenuItem( _( "_Play" ) )
            menu_items.set_image( gtk.image_new_from_stock( gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU ))
            menu.append(menu_items)
            swfFile = os.path.join(winkDir,self.getSwf(xmlfile))
            menu_items.connect( 'activate', self.onplayWink,swfFile)
            menu_items.show()
            menu.popup(None, None, None, event.button, event.time)

    def on_wink(self, msn, switchboard, signal, (mail, msnobj)):
        '''this method is called when a wink is received'''
        sha1d = hashlib.sha1(msnobj.sha1d).hexdigest()
        html = '<object type="application/x-emesene-wink" class="%s" ' \
            'data="%s"></object>' % (sha1d, sha1d)
        
        # TODO: is there a better way than this?
        conversation = self.get_conversation(switchboard)
        if conversation:
            conversation.ui.textview.customObjectsCallbacks['application/x-emesene-wink']\
=(conversation.ui.textview.wink,self.winkEvent)
            conversation.ui.textview.display_html(html.encode('ascii', \
                'xmlcharrefreplace'))

    def on_wink_transferred(self, msn, to, msnobj, path):
        '''call when a wink is transfered'''
        cabfile = os.path.join(path, 'wink.cab')
        if not os.path.exists(cabfile):
            return
        sha = path.split("wink_")[1]
        winkDir = os.path.join(self.winkCacheDir,sha)
        
        if not os.path.isdir(winkDir):
            # extract
            if os.name != "nt":
                retval = subprocess.call(['cabextract', '-d' + winkDir, cabfile])
            else:
                os.mkdir(winkDir)
                arg = ' /e /a /y /l "' + winkDir + '" "' + cabfile + '"'
                proc = subprocess.Popen('extrac32.exe' + arg)
                proc.wait()

        os.remove(cabfile)
        os.rmdir(path)

        xmlfile = os.path.join(winkDir, 'content.xml')
        # find filenames
        image=self.getThumbnail(xmlfile)
        image_path = os.path.join(winkDir, image)

        # update wink preview
        for conversation in self.getOpenConversations():
            conversation.ui.textview.setCustomObject(sha, \
                image_path, type='application/x-emesene-wink')

        if self.autoplay:
            swffile=self.getSwf(xmlfile)
            swf_path = os.path.join(winkDir, swffile) 
            self.playWink(swf_path)

    def configure(self):
        self.autoplay = bool(int(self.config.getPluginValue(self.name, \
            'autoplay', False)))

        opt = []
        opt.append(Option('autoplay', bool, _('Automatic playing'), \
            _('It plays automatically the received winks'), self.autoplay))

        result = ConfigWindow(_('Winks Receiving config'), opt ).run()
        if result:
           if result.has_key('autoplay'):
                self.autoplay = result['autoplay'].value
                self.config.setPluginValue(self.name, 'autoplay', \
                    str(int(self.autoplay)))


