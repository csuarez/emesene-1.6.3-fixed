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
import gobject

disabled = False
type_ = 'gtk'

if not gtk.check_version( 2, 10, 0 ) == None:
    if os.name == 'posix':
        try:
            import egg.trayicon
            type_ = 'egg'
        except:
            print 'No tray icon library detected'
            disabled = True
    elif os.name == 'nt':
        try:
            from gtkwin32 import *
            WM_LBUTTONUP = 0x0202
            WM_RBUTTONUP = 0x0205
            type_ = 'win'
        except:
            print 'No tray icon library detected'
            disabled = True

# WARNING: disable for release until stable enough.
#try:
#    import appindicator
#    type_ = 'indicator'
#    disabled = False
#except:
#    pass

class TrayIcon:
    '''This class creates the tray icon notification - Pre-GTK 2.10'''

    def __init__(self, controller):
        '''Constructor'''
        global disabled
        
        self.controller = controller
        self.config = self.controller.config
        self.mainWindow = self.controller.mainWindow
        self.theme = self.controller.theme
        self.status = ''
        self.tray = None
        self.ind = None

        disabled = self.config.glob['disableTrayIcon']

        try:
            if disabled:
                pass
            elif type_ == 'gtk':
                self.tray = gtk.StatusIcon()
                self.tray.set_tooltip( 'emesene' )
                pixbuf = self.theme.getImage('trayicon')
                self.tray.set_from_pixbuf( pixbuf )
                self.buildMenu()
                self.tray.hide = lambda: self.tray.set_visible( False )
                self.tray.show = lambda: self.tray.set_visible( True )
                
                self.tray.connect( 'activate', self.on_activate )
                self.tray.connect( 'popup-menu', self.on_popup_menu )
            elif type_ == 'indicator':
                self.ind = appindicator.Indicator("emesene", \
                        "trayicon", appindicator.CATEGORY_APPLICATION_STATUS, \
                        self.theme.path)
                print self.ind.get_property("icon-theme-path")
                self.ind.set_status(appindicator.STATUS_ACTIVE)
                self.ind.set_attention_icon("lunch")
                self.buildMenu()
                self.ind.set_menu(self.menu)
            elif os.name == 'posix':
                self.tray = egg.trayicon.TrayIcon('emesene')
                self.buildTrayIconPosix()
                self.buildMenu()
            elif os.name == 'nt':
                # Note: gtk window must be realized before installing extensions.
                self.mainWindow.realize()
                self.win32ext = GTKWin32Ext(self.mainWindow)
                self.buildMenu()
                self.buildTrayIconWin32()
        except Exception, e:
            print 'exception creating trayicon: ' + str( e )
            disabled = True
            
    def remove(self):
        '''remove the trayicon'''

        if os.name == 'nt' and type_ != 'gtk': 
            self.win32ext.remove_notify_icon()
        elif type_ == 'indicator':
            self.ind.set_status(appindicator.STATUS_PASSIVE)
        else:
            self.tray.hide()
        
    def buildTrayIconPosix(self):
        '''Build the trayIcon for linux'''

        self.eventBox = gtk.EventBox()
        pixbuf = self.theme.getImage('trayicon')
        self.image = gtk.Image()
        self.image.set_from_pixbuf( pixbuf )

        self.eventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.eventBox.connect_object('button_press_event', self.iconClickPosix, self.eventBox)

        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self.eventBox, 'emesene')
        
        self.eventBox.add(self.image)
        self.tray.add(self.eventBox)
        self.eventBox.show_all()
        self.tray.show_all()

    def update(self, newUserStatus, pixbuf=None):
        
        self.status = newUserStatus

        if type_ == 'gtk':
            func = self.tray.set_from_pixbuf
        elif type_ == 'egg':
            func = self.image.set_from_pixbuf
        elif type_ == 'indicator':
            self.ind.set_icon(self.theme.statusToPixbuf(newUserStatus, False))
            self.ind.set_menu(self.menu)
            self.menu.show_all()
            return

        if pixbuf == None:
            func(self.theme.statusToPixbuf(newUserStatus))
        else:
            func(pixbuf)

        if self.controller.msn and self.controller.userEmail:
            text = 'emesene - ' + str(self.controller.userEmail)
            if type_ == 'egg':
                self.tooltips.set_tip(self.eventBox, text)
            elif type_ == 'gtk':
                self.tray.set_tooltip(text)
        
    def buildTrayIconWin32(self):
        '''Build the trayIcon for windows'''

        ## http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/winui/windowsuserinterface/resources/icons/iconreference/iconfunctions/loadicon.asp
        hicon = win32gui.ExtractIcon(0, 'themes\\' + \
            self.config.user['theme'] + '\\' + 'trayicon.ico', 0)
        self.win32ext.add_notify_icon(hicon, 'Emesene') # TODO: account
        self.win32ext.notify_icon.menu = self.menu

        # Set up the callback messages
        self.win32ext.message_map({WM_TRAYMESSAGE: self.iconClickWin32})

    def iconClickWin32(self, hwnd, message, wparam, lparam):
        '''the event handler for windows'''

        if lparam == WM_RBUTTONUP:
            self.win32ext.notify_icon.menu.popup(None, None, None, 0, 0)
        elif lparam == WM_LBUTTONUP:
            self.win32ext.notify_icon.menu.popdown()
            self.showHide()

    def iconClickPosix(self, widget, event):
        '''the event handler for linux'''

        if event.type == gtk.gdk.BUTTON_PRESS: # Single click
            if event.button == 1: # Left Click
                self.showHide(self.eventBox)
            elif event.button == 3: # Right Click - Show popup
                self.menu.popup(None, None, None, event.button, event.time)
                
    def on_popup_menu( self, status_icon, button, activate_time ):
        position = gtk.status_icon_position_menu
        if os.name == 'nt':
            position = None       
        self.menu.popup( None, None, position, button, activate_time, status_icon )

    def on_activate( self, status_icon ):
        if self.tray.get_blinking():
            conv = self.controller.conversationManager.newest_message_conv
            conv_window = conv.parentConversationWindow

            if conv_window.get_urgency_hint():
                if conv_window.tabs.get_show_tabs():
                    conv_window.showTab(conv_window.tabs.page_num(conv.ui))
            conv_window.present()
        else:
            self.showHide()

    def buildMenu(self):
        '''Build the menu widget'''

        self.menu = gtk.Menu()
        
        menuItemQuit = gtk.ImageMenuItem( gtk.STOCK_QUIT )
        menuItemQuit.connect('activate', self.on_quit)

        menuItemShowHide = gtk.MenuItem(_("Hide/Show emesene"))
        menuItemShowHide.connect('activate', self.showHide)

        self.menu.append(menuItemShowHide)
        self.menu.append(menuItemQuit)
        if os.name == "nt":
            self.timerID = None
            self.menu.connect("leave-notify-event", self.start_timer_nt)
        self.menu.show_all()

    #I had to add all this "timerID != None" checks because the "source_remove"
    #method doesn't stop the timeout_add function, am I doing something grown? -arielj
    def start_timer_nt(self, menu, event):
        if self.timerID == None:
            self.timerID = gobject.timeout_add( 2000, self.popdownmenu )
        self.deleteTimerID = self.menu.connect("motion-notify-event", self.remove_timer)

    def remove_timer(self, menu, event):
        if self.timerID != None:
            gobject.source_remove(self.timerID)
            self.timerID = None

    def popdownmenu(self):
        if self.timerID != None:
            self.menu.popdown()
        return False
        
    def on_quit( self, menuitem):
        self.controller.quit( 0 )
    
    def showHide(self, widget = None):
        '''Show or hide the main window'''

        if self.mainWindow.flags() & gtk.VISIBLE:
            self.mainWindow.hide()
        else:
            self.mainWindow.deiconify()
            self.mainWindow.show()
            
    def getNotifyObject( self ):
        if not disabled and not type_ == 'gtk' and not type_ == 'indicator':
            return self.tray
        return None

