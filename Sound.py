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
import TrayIcon
import gtk

if os.name == 'nt':
    import winsound
    
import paths

try: 
    import gst
    GSTREAMER = True
except:
    GSTREAMER = False

try:
    from AppKit import NSSound
    MAC = True
except:
    MAC = False

class Sound:
    '''A plugin to play sounds using the available modules on the system'''

    def __init__(self, theme):
        '''class constructor'''
    
        self.theme = theme
        self.beep = False
        self.command = ''
        self.canPlay = False
        self.canGstreamer = False
        self.isMac = False
        
        if os.name == "posix":
            self.checkAvailability()
            if self.canGstreamer:
                self.player = gst.element_factory_make("playbin", "player")
                bus = self.player.get_bus()
                bus.enable_sync_message_emission()
                bus.add_signal_watch()
                bus.connect('message', self.gst_on_message)
        else:
            self.canPlay = True

    def gst_on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)

    def checkAvailability(self):
        if self.beep:
            self.canPlay = True
        elif GSTREAMER:
            self.canPlay = True
            self.canGstreamer = True
        elif MAC:
            self.canPlay = True
            self.isMac = True
        elif self.is_on_path('aplay'):
            self.canPlay = True
            self.command = 'aplay'
        elif self.is_on_path('play'):
            self.canPlay = True
            self.command = 'play'
        
    def play(self, sound_theme,  sound):
        if self.beep and not self.isMac:
            gtk.gdk.beep()
            return
        
        for theme in (sound_theme, 'default'):
            soundPath = os.path.join(paths.SOUNDS_PATH, sound_theme,
                sound + ".wav")
            if os.path.exists(soundPath):
                break
            else:
                soundPath = ''

        if not soundPath:
            return

        self.play_path(soundPath)

    def play_path(self, soundPath):
        if os.name == "nt":
            winsound.PlaySound(soundPath, 
                winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif os.name == "posix":
            if self.canGstreamer:
                loc = "file://" + soundPath
                self.player.set_property('uri', loc)
                self.player.set_state(gst.STATE_PLAYING)
            elif self.isMac:
                macsound = NSSound.alloc()
                macsound.initWithContentsOfFile_byReference_( \
                    soundPath, True)
                macsound.play()
                while macsound.isPlaying():
                    pass
            else:
                os.popen4(self.command + " " + soundPath)
            
    def getCommand(self):
        return self.command
        
    def setCommand(self, string):
        self.command = string
        
    def is_on_path(self, fname):
        for p in os.environ['PATH'].split(os.pathsep):
            if os.path.isfile(os.path.join(p, fname)):
                return True

class SoundHandler:
    def __init__(self, controller, msn, action=None):
        '''Contructor'''
        self.theme = controller.theme
        self.sound = Sound(self.theme)
        self.controller = controller
        self.config = self.controller.config
        self.msn = msn
        self.muteSound = self.config.user['soundsmuteSound']
        self.checkBox = gtk.CheckMenuItem(_('Mute Sounds'))
        self.checkBox.set_active(self.muteSound)
        if action == 'start':
            self.onlineId = None
            self.offlineId = None
            self.messageId = None
            self.nudgeId = None
            self.transferId = None
            self.sendMessageId = None
            self.connectpbId = None
            self.senderrorId = None
            self.exceptionId = None
            self.errorId = None
            self.check()
            self.checkBox.connect('activate', self.on_muteSounds_activate)
            self.updateTrayIconMenuList()
            self.update()
            self.start()
            
    def update(self):
        self.playOnline = self.config.user['soundsplayOnline']
        self.playOffline = self.config.user['soundsplayOffline']
        self.muteSound = self.config.user['soundsmuteSound']
        self.checkBox.set_active(self.muteSound)
        self.playMessage = self.config.user['soundsplayMessage']
        self.playNudge = self.config.user['soundsplayNudge']
        self.playTransfer = self.config.user['soundsplayTransfer']
        self.playInactive = self.config.user['soundsplayInactive']
        self.playSend = self.config.user['soundsplaySend']
        self.playError = self.config.user['soundsplayError']
        self.disableBusy = self.config.user['soundsdisableBusy']
        
        self.sound_theme = self.config.user['soundstheme']
        self.sound.beep = self.config.user['soundsbeep']
        
    def on_muteSounds_activate(self, *args):
        self.muteSound = self.checkBox.get_active()
        self.config.user['soundsmuteSound'] = (self.muteSound)

    def connect_onoff(self, *args):
        self.onlineId = self.msn.connect('user-online', self.online)
        self.offlineId = self.msn.connect('user-offline', self.offline)
        if self.notifyId is not None: self.msn.disconnect(self.notifyId)
        self.notifyId = None
    
    def start(self):
        self.notifyId = None
        self.onlineId = None
        self.offlineId = None
        if self.msn.canNotify:
            self.connect_onoff()
        else:
            self.notifyId = self.msn.connect('enable-notifications', self.connect_onoff)
        self.messageId = self.msn.connect('message-received', self.message)
        self.nudgeId = self.msn.connect('nudge-received', self.nudge)
        self.transferId = self.msn.connect('new-file-transfer', self.transfer)
        self.sendMessageId = self.controller.conversationManager.connect(
            'send-message', self.send)
        self.connectpbId = self.msn.connect('connection-problem', self.alert)    
        self.senderrorId = self.msn.connect('send-message-error', self.alert)
        self.exceptionId = self.msn.connect('exception', self.alert)
        self.errorId = self.msn.connect('error', self.alert)
        
    def stop(self):
        if self.onlineId is not None: self.msn.disconnect(self.onlineId)
        if self.offlineId is not None: self.msn.disconnect(self.offlineId)
        if self.notifyId is not None: self.msn.disconnect(self.notifyId)
        self.msn.disconnect(self.messageId)
        self.msn.disconnect(self.nudgeId)
        self.msn.disconnect(self.transferId)
        self.controller.conversationManager.disconnect(self.sendMessageId)
        self.msn.disconnect(self.connectpbId)
        self.msn.disconnect(self.senderrorId)
        self.msn.disconnect(self.exceptionId)
        self.msn.disconnect(self.errorId)
        if not TrayIcon.disabled:
            self.controller.trayIcon.menu.remove(self.checkBox);
            self.controller.trayIcon.menu.show_all()
            self.controller.trayIcon.update(self.controller.msn.status)
    
    def check(self):
        if not self.sound.canPlay:
            return (False, _('gstreamer, NSSound, play and aplay not found.'))
        return (True, 'Ok')

    def online(self, msnp, email, oldStatus):
        if oldStatus == 'FLN' and self.playOnline and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'online')

    def offline(self, msnp, email):
        if self.playOffline and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'offline')

    def message(self, msnp, email):
        if self.playMessage and self.soundsEnabled():
            result = self.controller.conversationManager\
                .getOpenConversation(email)
            if self.playInactive and result != None:
                window, conversation = result
                windowFocus = window.is_active()
                tabFocus = (window.conversation == conversation)
                if not (windowFocus and tabFocus):
                    self.sound.play(self.sound_theme, 'type')
            else:
                self.sound.play(self.sound_theme, 'type')

    def nudge(self, *args):
        if self.playNudge and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'nudge')

    def transfer(self, *args):
        if self.playTransfer and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'nudge')
    
    def send(self, *args):
        if self.playSend and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'send')
            
    def alert(self, *args):
        if self.playError and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'alert')
            
    def soundsEnabled(self):
        if (self.disableBusy and self.msn.status == 'BSY') or \
           self.muteSound or not self.config.user['enableSounds']:
            return False
        else:
            return True
    
    def updateTrayIconMenuList(self):
     	if not (TrayIcon.disabled):
     		#Generates the Systray list with the new feature
     		#when the TrayIcon is enabled
            self.controller.trayIcon.menu.prepend(self.checkBox)
            self.controller.trayIcon.menu.show_all()
            self.controller.trayIcon.update(self.controller.msn.status)
