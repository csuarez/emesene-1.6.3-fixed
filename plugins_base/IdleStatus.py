# -*- coding: utf-8 -*-

import Plugin
import gtk
import gobject
import time
import os

name_ = os.name
if name_ == "nt": #windows, use ctypes
    from ctypes import Structure, windll, c_uint, sizeof, byref

    class LASTINPUTINFO(Structure):
        _fields_ = [
            ('cbSize', c_uint),
            ('dwTime', c_uint),
        ]
    def get_idle_duration():
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = sizeof(lastInputInfo)
        windll.user32.GetLastInputInfo(byref(lastInputInfo))
        millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    XLibOK = True
else: #if name_ == "posix": #*nix, use python-xlib
    try:
        import Xlib.display
        import Xlib.X
        import Xlib.XK
        import Xlib.error
        XLibOK = True
    except Exception, e:
        XLibOK = False
#elif name_ == "mac": does mac uses xlib?    

class MainClass( Plugin.Plugin ):

    description = _( 'Change status to idle after X minutes. Be careful with the custom command option, put only the command (without the slash).' )
    authors = { 'arielj' : 'arieljuod gmail com' }
    website = ''
    displayName = _( 'Idle Status' )
    name = 'IdleStatus'
    def __init__( self, controller, msn ):
        Plugin.Plugin.__init__( self, controller, msn )

        self.config = controller.config
        self.config.readPluginConfig( self.name )
        self.controller = controller
        self.msn = msn
        self.window = self.controller.mainWindow

    def start( self ):
        '''start the plugin'''
        #read plugin config
        #read minutes value, default=5
        value = self.config.getPluginValue( self.name, 'idleafter', 5 )
        try:
            minutes = int(value)
        except ValueError:
            minutes = 5
        self.idleAfter = minutes*60
        if self.msn.status == "IDL":
            self.isIdle = True
            self.reconnectedIdle = True
        else:
            self.isIdle = False
            self.reconnectedIdle = False

        #read detectDesktop value, default=True
        if name_=="posix" and not XLibOK:
            self.detectDesktop = False
        else:
            self.detectDesktop = (self.config.getPluginValue( self.name,\
                                       'detectDesktop', None ) != "False")

        #read the custom status command value, default=""
        self.command = self.config.getPluginValue( self.name,\
                                     'customStatusCommand', "" )

        if name_=="posix" and XLibOK:
            self.display = Xlib.display.Display()
            self.screen = self.display.screen()
            self.last_x = -1
            self.last_y = -1

        #connects the plugin to mouse and keyboard events
        self.connectWindow(None,None,self.window)
        self.controller.conversationManager.connect("new-conversation-ui", self.connectWindow)
        for conversation in self.getOpenConversations():
            self.connectWindow(None,None,conversation.parentConversationWindow)
        self.lastActivity = time.time()

        #start
        self.enabled = True
        self.tag = gobject.timeout_add( 2500, self.idle_state )
    
    def stop( self ):
        gobject.source_remove(self.tag)
        self.enabled = False
        
    def check( self ):
        if name_ == "posix" and not XLibOK:
            return (True, _('This plugin requires python-xlib to enable the "Detect whole desktop inactivity" option'))
        else:
            return (True, 'Ok')

    def configure( self ):
        minutes, command = self.getText()
        if minutes == None:
            minutes = 5
        else:
            try:
                minutes = int(minutes)
            except ValueError:
                minutes = 5

        if command == None or command == '':
            self.command = ""
        else:
            if command[0] == '/':
                command = command[1:] #remove the slash
            self.command = command

        self.config.setPluginValue( self.name, 'idleafter', minutes )
        self.config.setPluginValue( self.name, 'detectDesktop', self.detectDesktop )
        self.config.setPluginValue( self.name, 'customStatusCommand', self.command )
        self.idleAfter=minutes*60
        return True

    #reset the last activity time
    def resetLastActivity( self , widget, event ):
        self.lastActivity=time.time()
        self.reconnectedIdle = False

    #connect the events of a window
    def connectWindow(self,something,conversation,window):
        window.add_events(gtk.gdk.KEY_PRESS_MASK |
                               gtk.gdk.POINTER_MOTION_MASK |
                               gtk.gdk.BUTTON_PRESS_MASK |
                               gtk.gdk.SCROLL_MASK)

        window.connect("motion-notify-event", self.resetLastActivity)
        window.connect("key-press-event", self.resetLastActivity)
        window.connect("button-press-event", self.resetLastActivity)

    def toggleDetection(self, button):
        self.detectDesktop = not self.detectDesktop

    #check if user was idle enough time to change status
    def idle_state(self):
        #compare actual with latest conditions to get the idle time
        if self.detectDesktop:
            if name_ == "nt":
                idleTime=get_idle_duration()
            elif XLibOK:
                #check mouse movement
                x = self.screen.root.query_pointer()._data["root_x"]
                y = self.screen.root.query_pointer()._data["root_y"]
                if self.last_x == x and self.last_y == y:
                    #if mouse didn't move, check pressed keys (not the best, but should work...)
                    #it's really ugly, but I tryied with keypress/release events
                    #and I can't/don't know how to make them work...
                    keymap = self.display.query_keymap()
                    for key in keymap:
                        if not key == 0:
                            self.resetLastActivity(None,None)
                else:
                    self.last_x = x
                    self.last_y = y
                    self.resetLastActivity(None,None)
                idleTime = time.time() - self.lastActivity
        else:
            idleTime = time.time() - self.lastActivity

        #comparte idle time with user's preferences
        if idleTime >= self.idleAfter:
            if self.msn.status == "NLN":
                slashCommand = self.command.partition(' ')[0] #if the command accept arguments
                if slashCommand in self.controller.Slash.commands:
                    message="/%s" % self.command
                    self.controller.Slash.sendMessage(self.controller.conversationManager, \
                                                                         None, message)
                    self.isIdle=True
                else:
                    self.command = ""
                    self.msn.changeStatus("IDL")
                    self.isIdle=True
            elif self.reconnectedIdle:
                self.reconnectedIdle = False
        elif idleTime < self.idleAfter and self.isIdle and not self.reconnectedIdle:
            self.msn.changeStatus("NLN")
            self.isIdle=False
        return True


    #methods for the config dialog
    def responseToDialog(self, entry, dialog, response):
        dialog.response(response)

    def getText(self, ):
        dialog = gtk.MessageDialog( None ,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          gtk.MESSAGE_INFO, gtk.BUTTONS_OK_CANCEL,
                          _('Go idle after X minutes (default 5)'))
        dialog.set_property("title",_("IdleStatus Plugin"))

		#add a warining if python-xlib is missing
        if name_ == "posix" and not XLibOK:
            dialog.format_secondary_markup("You need python-xlib to enable the 'Detect whole desktop inactivity' option")

        #entry box for the minutes to wait
        entry = gtk.Entry(3)
        minutos = self.idleAfter/60
        entry.set_text("%d" % minutos)
        entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_("Minutes:")), False, 5, 5)
        hbox.pack_end(entry)

        #checkbox for idle detection method
        checkbox = gtk.CheckButton(_("Detect whole desktop inactivity"))
        checkbox.set_active(self.detectDesktop)
        checkbox.set_sensitive(XLibOK)
        checkbox.connect("toggled",self.toggleDetection)

        #entry box for the custom command
        commandEntry = gtk.Entry()
        commandEntry.set_text(self.command)
        hboxC = gtk.HBox()
        hboxC.pack_start(gtk.Label(_("Custom status command:")), False, 5, 5)
        hboxC.pack_end(commandEntry)

        dialog.vbox.pack_start(hbox)
        dialog.vbox.pack_end(hboxC)
        dialog.vbox.pack_end(checkbox)
        dialog.show_all()

        resp = dialog.run()
        if resp == gtk.RESPONSE_OK:
            text = entry.get_text()
            command = commandEntry.get_text()
        else:
            text = minutos
            command = self.command
        dialog.destroy()
        return [text , command]
