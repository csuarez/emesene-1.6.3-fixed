# -*- coding: utf-8 -*-

#   This file is part of emesene
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

import sys

import Login
import TrayIcon
import MainMenu
import UserList
import UserPanel
import FilterEntry
import dialog
import emesenelib.common
import pango
import stock

try:
    import gtk
    import gobject
    import pango
except:
    print 'you need pyGTK to run emesene'
    sys.exit(-1)

class MainWindow(gtk.Window):
    '''
    This class represent the main window of emesene,
    it inherit from gtk.Window
    and basically it is a container for other classes.
    '''

    __gsignals__ = {
        'gui-build-done' :
            (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_STRING,)),
    }

    def __init__(self, controller):
        '''Constructor'''
        gtk.Window.__init__(self)

        self.controller = controller
        self.config = controller.config
        # accelerators
        accelGroup = gtk.AccelGroup()
        self.add_accel_group(accelGroup)
        self.accelGroup = accelGroup
        accelGroup.connect_group(ord('M'), gtk.gdk.CONTROL_MASK, \
            gtk.ACCEL_LOCKED, self.on_toggle_menu)

        self.set_title('emesene')
        self.set_role('main')

        self.geometry = self.config.glob['mainWindowGeometry']
        self.parse_geometry(self.geometry)
        self.on_size_alloc
        self.x, self.y = self.get_position()

        self.connect('size-allocate', self.on_size_alloc)

        theme = controller.theme
        gtk.window_set_default_icon_list(theme.getImage('icon16'),
                                          theme.getImage('icon32'),
                                          theme.getImage('icon48'),
                                          theme.getImage('icon96'))

        self.windowVBox = None
        self.vbox = None
        self.login = None
        self.userList = None
        #The next generates a variable with letters and numbers to manage the searches
        self.acceptedCharacters = map(chr, range(97, 123)) + map(chr, range(65, 91)) \
            + ['0','1','2','3','4','5','6','7','8','9']

        self.disconectionMessage = None

        self.currentInterface = 'login'
        self.buildInterface('login')

        self.itemSelectedId = 0

        self.signals = []
        sap = self.signals.append
        sap(self.config.connect('change::showUserPanel',
            self.updateConfig))
        sap(self.config.connect('change::showSearchEntry',
            self.updateConfig))
        sap(self.config.connect('change::showStatusCombo',
            self.updateConfig))
        sap(self.config.connect('change::showMenu',
            self.updateConfig))
        sap(self.config.connect('change::userListAvatarSize',
            self.updateSize))
        sap(self.config.connect('change::smallIcons', self.updateSize))
        # TODO: do we need disconnecting these signals?

    def on_size_alloc(self, widget, allocation):
        self.width = allocation.width
        self.height = allocation.height

    def on_toggle_menu(self, *args):
        self.config.user['showMenu'] = not self.config.user['showMenu']

    def saveToQuit(self):
        '''Saves configuration parametes and everything needed ir order
        to safely quit'''

        if self.userList:
            try:
                self.userList.saveGroupState()
            except:
                pass

        self.geometry = '%dx%d+%d+%d' % (self.width,self.height,self.x,self.y)
        self.controller.config.glob['mainWindowGeometry'] = self.geometry

    def quit(self, status = 0):
        '''close the window, and do all the things needed...'''
        self.controller.quit(status)

    def show(self):
        '''Shows itself'''
        if not (self.x < 0 or self.y < 0):
            self.move(self.x, self.y)
        gtk.Window.show(self)

    def hide(self):
        '''Hides itself and any other window'''

        # saves position
        if self.get_property('visible'):
            self.x, self.y = self.get_position()

        if self.userList:
            self.userList.tooltips.hideTooltip()

        # ------------ let the window hide itself the last ---------
        gtk.Window.hide(self)

    def hideOrClose(self, *args):
        '''hide or close depending if we have trayicon'''

        if TrayIcon.disabled:
            def remove_cb(response):
                if response == stock.YES:
                    self.quit(0)

            message = _('This action will close emesene, continue?')
            dialog.yes_no(message,remove_cb)
        else:
            self.hide()

        return True

    def buildInterface(self , guiType = 'login'):
        '''build the interface depending on the guiType parameter, by
        default build the login window.'''

        # save old login values, we may need them in new interface
        if self.login:
            user = self.login.getUser()
            passwd = self.login.getPass()
            status = self.login.getStatus()
        else:
            user = passwd = status = ''

        if self.get_child():
            self.remove(self.windowVBox)

        if self.userList:
            self.userList.tooltips.hideTooltip()
            self.userList.disconnect(self.itemSelectedId)

        # if i dont add this if we disconnect then the image isnt shown
        if guiType == 'userlist' and self.login:
            try:
                self.login.remove(self.login.loginImage)
            except:
                emesenelib.common.debug('Error when removing loginImage')

        self.currentInterface = guiType

        #widgets

        self.vbox = gtk.VBox(spacing=2)
        self.vbox.set_border_width(3)
        self.windowVBox = gtk.VBox()
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER , gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_IN)
        self.menu = MainMenu.MainMenu(self.controller, \
                                       guiType, self.accelGroup)

        if guiType == 'login':
            self.initEventBox()
            self.vbox.pack_start(self.eventBox, False, False, 0)
            self.login = Login.Login(self.controller, 'login')
            self.showNiceBar(self.disconectionMessage)
            self.vbox.pack_end(self.login)

        elif guiType == 'userlist':
            self.login = None
            self.userList = UserList.UserList(self.controller, \
                self.controller.theme, self.controller.config)
            self.itemSelectedId = self.userList.connect('item-selected',
                self.onItemSelected)

            self.userPanel = UserPanel.UserPanel(self.controller)
            self.vbox.pack_start(self.userPanel, False, False)
            self.statusCombo = StatusCombo(self.controller)
            self.statusVBoxTop = gtk.VBox()
            self.statusComboBottom = StatusCombo(self.controller)
            self.statusVBoxBottom = gtk.VBox()
            self.filterEntry = FilterEntry.FilterEntry(
                self.userList.setFilterText)
            self.scroll.add(self.userList)
            vbox2 = gtk.VBox()
            vbox2.pack_start(self.scroll)

            self.vbox.pack_start(self.statusVBoxTop, False, False)
            self.vbox.pack_start(self.filterEntry, False, False)
            self.vbox.pack_start(vbox2)
            self.vbox.pack_start(self.statusVBoxBottom, False, False)

            statusPos = self.config.user['statusComboPos']
            if statusPos == 0:
                self.userPanel.show_status_icon()
            elif statusPos == 2:
                self.userPanel.hide_status_icon()
                self.statusVBoxBottom.pack_start(self.statusCombo, False, False)
                self.statusVBoxBottom.show_all()
            else:
                self.userPanel.hide_status_icon()
                self.statusVBoxTop.pack_start(self.statusCombo, False, False)
                self.statusVBoxTop.show_all()

            self.filterEntry.connect('filter-entry-lost-focus', self.lost_focus)
            vbox2.show_all()
            self.controller.connect('preferences-changed',
                self.updateConfig)

        elif guiType == 'loading':
            self.menu.set_sensitive(False)
            self.login = Login.Login(self.controller, 'loading')
            self.login.setFieldValues(user, passwd, status)
            self.vbox.pack_start(self.login)

        elif guiType == 'reconnect':
            self.menu.set_sensitive(False)
            self.login = Login.Login(self.controller, 'reconnect')
            self.vbox.pack_start(self.login)

        self.windowVBox.pack_start(self.menu, False, False)
        self.windowVBox.pack_start(self.vbox, True, True)
        self.menu.show_all()
        self.add(self.windowVBox)
        self.vbox.show()
        self.windowVBox.show()
        self.update(self.controller)

        self.connect('delete-event' , self.hideOrClose)
        self.connect('destroy-event', self.hideOrClose)
        self.emit('gui-build-done', guiType)
        self.connect('key-press-event', self.on_key_press)


    def toggle_status_box(self, combo):
        if self.statusCombo.get_parent():
            self.statusCombo.get_parent().remove(self.statusCombo)
        pos = combo.get_active()
        if pos == 0:
            self.userPanel.show_status_icon()
        else:
            self.userPanel.hide_status_icon()
            if pos == 1:
                self.statusVBoxTop.pack_start(self.statusCombo, False, False)
                if self.config.user['showStatusCombo']:
                    self.statusVBoxTop.show_all()
                self.filterEntry.queue_draw()
            elif pos == 2:
                self.statusVBoxBottom.pack_start(self.statusCombo, False, False)
                if self.config.user['showStatusCombo']:
                    self.statusVBoxBottom.show_all()
                self.filterEntry.queue_draw()

    def lost_focus(self, widget):
        if self.filterEntry.entry.get_text() =='' and not self.config.user['showSearchEntry']:
            self.filterEntry.hide()

    def on_key_press(self, widget, event):
        if self.currentInterface != 'userlist': 
            if gtk.keysyms.Escape == event.keyval:
                self.hideOrClose()
        else:
            from gtk.gdk import CONTROL_MASK, MOD1_MASK
            if gtk.keysyms.Escape == event.keyval:
                if self.filterEntry.entry.get_text() == '' and not \
                   self.config.user['showSearchEntry'] and self.filterEntry.entry.is_focus():
                    self.filterEntry.hide()
                    return True
                elif self.filterEntry.entry.get_text() != '':
                    self.filterEntry.entry.set_text('')
                    return True
                elif self.filterEntry.entry.get_text() == '':
                    if self.userPanel.isEditing():
                        self.userPanel.stopEditing()
                        return True
                    self.hideOrClose()
                    return True
            elif not self.userPanel.tNick.is_focus() and not self.userPanel.tPersonalMessage.is_focus(): 
                if not self.filterEntry.entry.is_focus() : 
                    if gtk.gdk.keyval_name(event.keyval)  in self.acceptedCharacters: 
                        if event.state & CONTROL_MASK or event.state & MOD1_MASK:
                            return False
                        else:
                            if self.filterEntry.entry.get_text() == '' and not \
                               self.config.user['showSearchEntry']:
                                self.filterEntry.show()
                            self.filterEntry.entry.set_text(self.filterEntry.entry.get_text() + gtk.gdk.keyval_name(event.keyval))
                            self.filterEntry.entry.grab_focus()
                            self.filterEntry.entry.set_position(len(self.filterEntry.entry.get_text()))
                            return True

    def updateConfig(self, *args):
        self.update(self.controller, False)

    def updateSize(self, config, value, oldvalue):
        if value != oldvalue and self.userList:
            self.userList.fill()

    def update(self, controller, refresUserList=True):
        if not controller or self.currentInterface != 'userlist':
            return

        if not self.config.user['showUserPanel']:
            self.userPanel.hide()
        else:
            self.userPanel.show()

        if not self.config.user['showSearchEntry']:
            self.filterEntry.hide()
        else:
            self.filterEntry.show()

        if not self.config.user['showStatusCombo']:
            self.statusCombo.hide()
        else:
            if self.statusCombo.get_parent():
                self.statusCombo.get_parent().show_all()

        if not self.config.user['showMenu']:
            self.menu.hide();
        else:
            self.menu.show();

        # update UserPanel Nick and PM
        if self.config.user['showUserPanel']:
            self.userPanel.personalMessageRefresh()
            self.userPanel.nickRefresh()

        if refresUserList:
            self.refreshUserList()

    def rebuild(self):
        '''repaint the currentinteface'''

        self.buildInterface(self.currentInterface)

    def refreshUserList(self, force=False):
        '''refresh the userlist :D
        (if we are in userlist mode)'''

        if self.currentInterface == 'userlist':
            groups = self.controller.msn.contactManager.groups
            groups[_('no group')] = \
                self.controller.msn.contactManager.noGroup
            self.userList.fill(groups, force)

    def setAvatar(self, pixbuf):
        if self.currentInterface == 'userlist':
            self.userPanel.setAvatar(pixbuf)

    def onItemSelected(self, userlist, objType, obj, path):
        if objType == 'user':
            self.controller.newConversation(self.controller.msn,
                                            obj.email, None, True)
        elif objType == 'group':
            if self.userList.row_expanded(path):
                self.userList.collapse_row(path)
            else:
                self.userList.expand_row(path, False)

    def initEventBox(self):
        self.eventBox = gtk.EventBox()
        self.box = gtk.HBox()
        self.eventBox.add(self.box)
        self.label = gtk.Label()
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.box.pack_start(self.image, False, False, 3)
        self.box.pack_start(self.label, True, True, 3)
        self.eventBox.connect("button-press-event", self.onClickNiceBar)

    #Info bar by default
    def showNiceBar(self, message, color=None, image=gtk.STOCK_DIALOG_INFO):
        if message != None:
            if color == None:
                color = self.controller.tooltipColor
            self.eventBox.modify_bg(gtk.STATE_NORMAL, color)
            self.image.set_from_stock(image, gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.label.set_text(message)
            self.eventBox.show_all()
        else:
            self.eventBox.hide_all()

    #hide nicebar
    def onClickNiceBar(self, widget, event):
        self.eventBox.hide_all()

class StatusCombo(gtk.ComboBox):
    '''this class represent the combo where you set the status'''

    def __init__(self, controller):
        '''Constructor'''

        self.statusListStore = gtk.ListStore(gtk.gdk.Pixbuf, \
                      gobject.TYPE_STRING, gobject.TYPE_STRING)

        gtk.ComboBox.__init__(self, self.statusListStore)

        self.controller = controller

        self.statusPixbufCell = gtk.CellRendererPixbuf()
        self.statusTextCell = gtk.CellRendererText()
        self.pack_start(self.statusPixbufCell, False)
        self.pack_start(self.statusTextCell, False)
        self.statusPixbufCell.set_property('xalign', 0.0)
        self.statusPixbufCell.set_property('xpad', 5)
        self.statusTextCell.set_property('xalign', 0.0)
        self.statusTextCell.set_property('xpad', 5)
        self.statusTextCell.set_property('width', 158)
        self.add_attribute(self.statusPixbufCell, 'pixbuf', 0)
        self.add_attribute(self.statusTextCell, 'text', 2)
        self.set_resize_mode(0)
        self.set_wrap_width(1)

        counter = 0
        flag = False
        j = 0
        for i in controller.status_ordered[0]:
            if i not in self.controller.bad_statuses:
                self.statusListStore.append([ \
                    self.controller.theme.statusToPixbuf(i).scale_simple(20,20,gtk.gdk.INTERP_BILINEAR), i, \
                    _(self.controller.status_ordered[2][j])]) # re-gettext-it
            j += 1

        self.set_current_status()
        # flag needed to avoid the double-changing of status when
        # user changes it from another place
        self.changeStatusFlag = True

        self.connect('scroll-event', self.on_scroll_event)
        self.connect('changed', self.on_status_changed, self.changeStatusFlag)
        self.controller.msn.connect('self-status-changed',
            self.selfStatusChanged)
    
    def set_current_status(self, status=None):
        ''' sets current status in the widget '''
        if status is None:
            i = self.controller.contacts.get_status()
            status = self.controller.status_ordered[0][i]
        
        i = 0
        for item in self.statusListStore:
            if item[1] == status:
                break
            i += 1
            
        self.set_active(i)
        
    def selfStatusChanged(self, msnp, status):
        self.changeStatusFlag = False
        self.set_current_status(status)        
        self.changeStatusFlag = True

    def on_status_changed(self , *args):
        if self.changeStatusFlag:
            asd = self.statusListStore.get(self.get_active_iter(), 1)
            self.controller.contacts.set_status(asd[0])

    def on_scroll_event(self,button, event):
        self.popup()
        return True
