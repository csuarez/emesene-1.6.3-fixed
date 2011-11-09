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

import gtk
import pango
import os
import gobject
import paths
import abstract.stock
import dialog
# TODO: write p2p for ink, then you can reenable this.
#import InkDraw
import ConversationUI

class ConversationWindow(gtk.Window):
    '''This class is the conversation window, it is just the frame
    where all the conversations are hold, it can be tabbed or one
    conversation per window, that depend on the config.'''

    def __init__(self, controller, conversation):
        '''Constructor'''
        gtk.Window.__init__(self)

        self.set_border_width(0)

        self.controller = controller
        self.config = controller.config
        self.closed = False
        self.notOpen = True
        self.minimized = False

        if not self.config.user['windows']:
            self.geometry = self.config.user['convWindowGeometry']
            self.parse_geometry(self.geometry)
        else:
            self.width = int(self.config.user['convWindowWidth'])
            self.height = int(self.config.user['convWindowHeight'])
            self.set_default_size(self.width, self.height)

        if self.config.user['convMaximized']:
            self.maximize()

        self.connect('size-allocate', self.on_size_alloc)

        # accelerators
        accelGroup = gtk.AccelGroup()
        self.add_accel_group(accelGroup)
        self.accelGroup = accelGroup
        accelGroup.connect_group(gtk.keysyms.W, \
                                  gtk.gdk.CONTROL_MASK, gtk.ACCEL_LOCKED, \
                                  self.on_key_close_tab)

        for i in range(1, 10):
            accelGroup.connect_group(gtk.keysyms._0 + i, \
                                  gtk.gdk.MOD1_MASK, gtk.ACCEL_LOCKED, \
                                  self.on_key_change_tab)

        self.conversation = conversation
        self.conversation.setIsCurrent(True)

        self.update_title()
        self.set_role('chat')

        self.textTagCount = 0

        self.user = self.conversation.getUser()
        self.conversations = []

        self.menu = ConversationWindowMenu(self, controller)

        self.vbox = gtk.VBox()
        self.tabs = gtk.Notebook()
        self.tabs.set_show_border(False)
        self.tabs.set_property('tab-vborder', 0)

        self.tabs.set_show_tabs(False) #ok, ok, never show tabs on window init
        self.tabs.set_scrollable(True)
        self.tabs.show_all()
        self.openTab(conversation)

        self.vbox.pack_start(self.menu, False, False)
        self.vbox.pack_start(self.tabs, True, True)

        if self.config.user['showMenubar']:
            self.menu.show_all()
        else:
            accelGroup.connect_group(ord('L'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.clearOutputText)
            accelGroup.connect_group(ord('Q'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.menu.onCloseActivate)
            accelGroup.connect_group(ord('I'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.menu.onInviteActivate)
            accelGroup.connect_group(ord('S'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.menu.onSendFileActivate)

        self.vbox.show()

        self.connect('delete-event', self.close)
        self.connect('focus-in-event', self.on_focus_in_event)
        self.connect('window-state-event', self.on_window_state_event)
        self.switchId = self.tabs.connect('switch-page', self.on_switch_page)
        self.showMenubarId = self.config.connect('change::showMenubar', \
            self.on_menubar_change)

        self.config.connect('change::avatarsInTaskbar', self.on_avatars_change)
        # the 'display-picture-changed' signal is emitted when the new dp is not cached
        self.controller.msn.connect('display-picture-changed', self.onDisplayPictureChanged)
        # using the 'user-attr-changed' signal to catch change to cached dps
        self.controller.msn.connect('user-attr-changed', self.onUserAttrChanged)

        self.connect('key-press-event', self.on_key_press)

        self.add(self.vbox)

        self.conversation.ui.hideUserList()
                
    def on_key_press(self, widget, event):
        if (event.state & gtk.gdk.CONTROL_MASK) and event.keyval in [ gtk.keysyms.Tab, gtk.keysyms.ISO_Left_Tab, gtk.keysyms.Page_Down, gtk.keysyms.Page_Up]:
	    if event.state & gtk.gdk.SHIFT_MASK or event.keyval == gtk.keysyms.Page_Up:
                self.cycleTabs(-1)
            else:
                self.cycleTabs(1)
            return True

    def on_focus_in_event(self, widget, event):
        self.unsetUrgency()
        self.conversation.ui.input.grabFocus()

    def on_window_state_event(self, widget, event):
        self.config.user['convMaximized'] = (event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED)
        self.minimized = (event.new_window_state == gtk.gdk.WINDOW_STATE_ICONIFIED)

    def on_size_alloc(self, widget, allocation):
        self.width = allocation.width
        self.height = allocation.height

    def on_key_close_tab(self, accelGroup, window, keyval, modifier):
        '''Catches events like Ctrl+W and closes current tab'''
        self.closeTab(self.conversation)

    def on_key_change_tab(self, accelGroup, window, keyval, modifier):
        '''Catches alt+number and shows tab number-1  '''
        pages = self.tabs.get_n_pages()
        new = keyval - gtk.keysyms._0 - 1   # WTF?
        if new < pages:
            self.showTab(new)

    def on_menubar_change(self, _config, value, oldValue):
        '''handler for showMenubar config change'''
        if value == '1':
            self.menu.show_all()
        else:
            accelGroup = self.accelGroup
            accelGroup.disconnect_key(ord('L'), gtk.gdk.CONTROL_MASK)
            accelGroup.disconnect_key(ord('Q'), gtk.gdk.CONTROL_MASK)
            accelGroup.disconnect_key(ord('I'), gtk.gdk.CONTROL_MASK)
            accelGroup.disconnect_key(ord('S'), gtk.gdk.CONTROL_MASK)
            accelGroup.connect_group(ord('L'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.clearOutputText)
            accelGroup.connect_group(ord('Q'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.menu.onCloseActivate)
            accelGroup.connect_group(ord('I'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.menu.onInviteActivate)
            accelGroup.connect_group(ord('S'), gtk.gdk.CONTROL_MASK, \
                gtk.ACCEL_LOCKED, self.menu.onSendFileActivate)
            self.menu.hide()

    def on_avatars_change(self, _config, value, oldValue):
        '''handler for avatarsInTaskbar config change'''
        self.set_icon(self.conversation.getWindowIcon())

    def onDisplayPictureChanged(self, _msnp, _switchboard, _msnobj, email):
        if self.conversation.switchboard.firstUser == email:
            self.set_icon(self.conversation.getWindowIcon())

    def onUserAttrChanged(self, _msnp, contact):
        if self.conversation.switchboard.firstUser == contact.email:
            self.set_icon(self.conversation.getWindowIcon())

    def show_invite_dialog(self, conversation=None):
        '''show the invite dialog for conversation, if conversation is
        None, then the current conversation is used'''
        if not self.controller or not self.controller.contacts \
            or not self.controller.msn:
            return

        conversation = conversation or self.conversation

        online_contacts = self.controller.contacts.get_online_list()
        dictionary = {}

        for i in online_contacts:
            dictionary[i.account] = i

        members = {}

        for mail in conversation.getMembers() + [conversation.getUser()]:
            contact = self.controller.getContact(mail)
            if contact:
                members[mail] = contact

        ConversationUI.InviteWindow(self.controller, None, dictionary,
            members, self.controller.theme, conversation.inviteUser).run()
            
    def show_inkdraw_dialog(self, conversation=None):
        '''shows inkdraw'''
        conversation = conversation or self.conversation
        if not self.controller or not self.controller.contacts \
            or not self.controller.msn:
            return
            
        InkDraw.InkDraw(self.controller)

    def cycleTabs(self, cycle):
        '''Move <cycle> pages to the right, if it's negative it moves
        to the left. Usually it's 1 or -1'''
        pages = self.tabs.get_n_pages()
        active = self.tabs.get_current_page()
        self.showTab((active + cycle) % pages)
        self.menu.update()

    def showTab(self, num):
        '''put the num tab as the selected one
        use this only if you want to explicitly set a tab NUMBER'''
        self.on_switch_page(None, None, num)
        self.tabs.set_current_page(num)

    def on_switch_page(self, _notebook, _page, page_num):
        '''callback for the switch-page signal'''

        self.conversation.setIsCurrent(False)
        self.conversation = self.tabs.get_nth_page(page_num).parentConversation

        self.set_icon(self.conversation.getWindowIcon())

        self.update_title()
        self.conversation.setIsCurrent(True)
        self.conversation.ui.update()

    def update_title(self):
        '''change window title to parsed title of current conversation'''
        self.set_title(\
            self.controller.unifiedParser.getParser(\
            self.conversation.getTitle()).get(escaped=False))

    def openTab(self, conversation):
        '''open a new tab, that represent a new conversation'''
        ui = conversation.ui
        tabWidget = ui.tabWidget

        eventbox = gtk.EventBox()
        eventbox.set_visible_window(False)
        eventbox.add(tabWidget)
        eventbox.connect('event', self.tabs_event, ui)

        tabNum = self.tabs.append_page(child=ui, tab_label=eventbox)

        try:
            self.tabs.set_tab_reorderable(ui, True)
        except AttributeError:
            #print 'Your "stable" system sucks because it's filled with'
            #print 'outdated libs. Please upgrade to a decent distro. '
            # :P
            pass

        self.conversations.append(conversation)

        #add the new tab label to notebook menu popup
        self.addOrUpdateMenuPopupItem(tabNum, conversation)

        # expand and fill
        self.tabs.set_tab_label_packing(ui, True, True, gtk.PACK_START)

        self.tabs.set_show_tabs(len(self.conversations) > 1)

        if not self.is_active() or len(self.conversations) == 0:
            self.tabs.set_current_page(tabNum)

    def addOrUpdateMenuPopupItem(self, tabNum, conversation):
        '''add the new tab label to notebook popup menu'''

        page = self.tabs.get_nth_page(tabNum)
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        image = gtk.Image()
        image.set_from_pixbuf(self.controller.theme.getImage('online'))
        hbox.pack_start(image, False, False)
        hbox.pack_start(gtk.Label(conversation.getTitle()))
        hbox.show_all()
        self.tabs.set_menu_label(page, hbox)

    def close_tab_confirmation(self, *args):
        if args[0] == abstract.stock.YES:
            for ft in args[1].transfers:
                ft.cancel() 
            self.close_tab_for_real(args[1])
            
    def closeTab(self, conversation):
        '''Close a conversation, but if there's some transfer,
        ask first and warns about unread messages'''
        closeBool = False

        #if prevention is activated and there are unread messages in this tab
        #tab grabs focus and label appears, else, check transfers
        if conversation.ui.tabWidget.hasMessageWaiting and self.config.user['preventClosingTime']:
            self.showTab(self.tabs.page_num(conversation.ui))
            message = _("There are unread messages in this tab")
            conversation.ui.set_label_closingPrevention(message)
            closeBool = False
        else:
            message = _("Transfers are happening, are you sure you want to cancel them?")
            if [x for x in conversation.transfers
                        if x.state not in (x.RECEIVED, x.FAILED)]:
                dialog.yes_no(message, self.close_tab_confirmation, conversation)
                closeBool = False
            else:
                closeBool = True

        if closeBool:
            self.close_tab_for_real(conversation)
        return closeBool

    def close_tab_for_real(self, conversation):                        
        num = self.tabs.page_num(conversation.ui)
        self.tabs.remove_page(num)

        #erase the conversation
        conversation.setStatus('closed')
        conversation.setClosed(True)
        conversation.ui.close()
        
        if conversation in self.conversations:
            self.conversations.remove(conversation)

        self.controller.conversationManager.emit('close-conversation-ui', \
            conversation, self)
        
        conversation.ui.destroy()
        
        # what do we have now?
        if len(self.conversations) == 0:
            # nothing
            self.destroy()
        else:
            # another tab, set is as current
            self.on_switch_page(None, None, self.tabs.get_current_page())
            self.tabs.set_show_tabs(len(self.conversations) > 1)

    def tabs_event(self, _widget, event, ui):
        '''closes a tab on middleclick press+release'''
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 2:
            self.closeTab(ui.parentConversation)
        
    def clearOutputText(self, *args):
        self.conversation.textBuffer.set_text('')

    def show(self):
        gtk.Window.show(self)
        self.notOpen = False

    def close_win_confirmation(self, *args):
        if args[0] == abstract.stock.YES:
            for ft in args[1]:
                ft.cancel() 
            self.close_win_for_real()
    
    def close(self, *args):
        '''close the window and set the attribute self.closed to true
           C10uD: i hate this function and its duplicated code, but 
           reusing the close tab code is real pain :D'''
        closeBool = True
        tabsWhitUnreadMessages = False

        #if the window have tabs, check if there are unread messages
        if self.config.user['preventClosingTime'] and not self.minimized:
            for conv in self.conversations:
                if conv.hasMessageWaiting or conv.ui.tabWidget.hasMessageWaiting:
                    tabsWhitUnreadMessages = True

        #if the window doesn't have tabs but it's not minimized with unread messages
        if tabsWhitUnreadMessages or (self.get_urgency_hint() and not self.minimized):
            message = _("There are unread messages in this window")
            self.conversation.ui.set_label_closingPrevention(message)
            #unset the "messageWaiting" so user can close the window if clicked again
            preventTime = 0
            if self.config.user['preventClosingTime']:
                preventTime = 1000
            gobject.timeout_add(preventTime, self.conversation.setNoMessageWaiting)
            gobject.timeout_add(preventTime, self.unsetUrgency)
            for conv in self.conversations:
                gobject.timeout_add(preventTime, conv.setNoMessageWaiting)
                gobject.timeout_add(preventTime, conv.ui.tabWidget.setNoMessageWaiting)
            closeBool = False
        else:
            activeTransfers = []
            for conv in self.conversations:
                for tr in conv.transfers:
                    if tr.state not in (tr.RECEIVED, tr.FAILED):
                        activeTransfers.append(tr)        
            if len(activeTransfers) > 0:
                message = _("Transfers are happening, are you sure you want to cancel them?")
                dialog.yes_no(message, self.close_win_confirmation, activeTransfers)
                closeBool = False
            else:
                closeBool = True

        if closeBool:
            self.unsetUrgency()
            self.close_win_for_real()
        return True
            
    def close_win_for_real(self):
        ''' this method kills all the tabs (if present) and this very window'''
        self.x, self.y = self.get_position()
        for conversation in self.conversations:
            conversation.setStatus('closed')
            conversation.setClosed(True)
            conversation.ui.close()
            # self.conversations.remove(conversation)

            self.controller.conversationManager.emit('close-conversation-ui', \
                conversation, self)
            conversation.ui.destroy()
        
        self.conversations = []
        self.closed = True

        self.geometry = '%dx%d+%d+%d' % (self.width,self.height,self.x,self.y)
        self.controller.config.user['convWindowGeometry'] = self.geometry
        self.controller.config.user['convWindowWidth'] = self.width
        self.controller.config.user['convWindowHeight'] = self.height

        self.config.disconnect(self.showMenubarId)
        self.tabs.disconnect(self.switchId)
        
        self.hide()
        self.destroy()
        
    def isClosed(self):
        '''return True if the window has been hided'''
        return self.closed

    def addChildAtAnchor(self, child, anchor, tab_num = None):
        '''add a child to an anchor in the current output if tab_num is None, otherwise add it in the tab'''
        # TODO: this method should be in conversation(ui)
        if tab_num is None:
            textview = self.conversation.ui.textview
        else:
            textview = self.tabs.get_nth_page(tab_num).textview
        textview.add_child_at_anchor(child, anchor)

    def setUrgency(self):
        '''try to set the urgency hint to the window or blink the tray icon'''

        # not perturb, respect the BSY status
        if self.controller.msn.status == 'BSY' and \
           self.config.user['dontDisturbOnBusy']:
            return

        if not self.has_toplevel_focus():
            try:
                if self.controller.config.user['blinkTrayIcon']:
                    self.controller.trayIcon.tray.set_blinking(True)
            except:
                pass
            try:
                if self.controller.config.user['statusbarHighLight']:
                    self.set_urgency_hint(True)
            except:
                pass

    def unsetUrgency(self):
        '''try to unset the urgency hint to the window and
        turn off tray icon blink'''
        try:
            self.set_urgency_hint(False)
            self.controller.trayIcon.tray.set_blinking(False)
            self.conversation.ui.update()
            self.controller.emit('message-read')
        except:
            # errors related to getting disconnected don't really matter
            pass

    def changeFont(self):
        '''opens the font selection dialog'''
        fontDesc = pango.FontDescription(self.config.user['fontFace'])
        if self.config.user['fontItalic']:
            uStyle = pango.STYLE_ITALIC
        else:
            uStyle = pango.STYLE_NORMAL

        if self.config.user['fontBold']:
            uWeight = pango.WEIGHT_BOLD
        else:
            uWeight = pango.WEIGHT_NORMAL

        fontDesc.set_style(uStyle)
        fontDesc.set_weight(uWeight)
        fontDesc.set_size(self.config.user['fontSize'] * pango.SCALE)

        fontDialog = gtk.FontSelectionDialog(_('Choose a font'))
        fontDialog.set_font_name(fontDesc.to_string())
        response = fontDialog.run()

        if response == gtk.RESPONSE_OK:
            pangoDesc = pango.FontDescription(fontDialog.get_font_name())
            font = pangoDesc.get_family()
            style = pangoDesc.get_style()
            weight = pangoDesc.get_weight()

            italic = bold = False

            if style == pango.STYLE_ITALIC:
                italic = True
            if weight == pango.WEIGHT_BOLD:
                bold = True

            self.controller.emit('font-changed', font, bold, italic, pangoDesc.get_size() / pango.SCALE)

        fontDialog.destroy()

    def changeColor(self):
        '''opens the color selection dialog'''
        colorDialog = gtk.ColorSelectionDialog(_('Choose a color'))
        colorDialog.set_resizable(False)
        colorDialog.colorsel.set_has_palette(True)
        colorDialog.colorsel.set_current_color(\
            gtk.gdk.color_parse(self.config.user['fontColor']))
        response = colorDialog.run()

        if response == gtk.RESPONSE_OK:
            color = colorDialog.colorsel.get_current_color()

            red = color.red >> 8
            green = color.green >> 8
            blue = color.blue >> 8

            self.controller.emit('color-changed', \
                '#%02X%02X%02X' % (red, green, blue))

        colorDialog.destroy()

    def send_file_dialog(self):
        '''Displays a dialog to choose a file to send'''
        if not self.controller or not self.controller.contacts \
            or not self.controller.msn:
            return

        dialog = gtk.FileChooserDialog(_('Send file'),
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_current_folder(paths.HOME_DIR)

        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            self.conversation.sendFile(dialog.get_filename())
        dialog.destroy()


class ConversationWindowMenu(gtk.MenuBar):
    '''This class represent the menu in the conversation window, i define
    it here because no other module here cares about this one.'''

    def __init__(self, parentConversationWindow, controller):
        '''Contructor'''

        gtk.MenuBar.__init__(self)

        self.parentConversationWindow = parentConversationWindow
        self.controller = controller
        accelGroup = parentConversationWindow.accelGroup

        # --- 'Conversation' menu

        conversationMenu = gtk.Menu()
        conversationMenuItem = gtk.MenuItem(_("_Conversation"))
        conversationMenuItem.set_submenu(conversationMenu)

        self.inviteMenuItem = gtk.ImageMenuItem(_('_Invite'))
        self.inviteMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,
                                    gtk.ICON_SIZE_MENU))
        self.inviteMenuItem.connect('activate', self.onInviteActivate)
        self.inviteMenuItem.add_accelerator('activate', accelGroup, ord('I'),
            gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        self.sendFileMenuItem = gtk.ImageMenuItem(_("_Send file"))
        self.sendFileMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_TOP,
                                    gtk.ICON_SIZE_MENU))
        self.sendFileMenuItem.connect('activate', self.onSendFileActivate)
        self.sendFileMenuItem.add_accelerator('activate', accelGroup, ord('S'),
            gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        clearMenuItem = gtk.ImageMenuItem(_('C_lear Conversation'))
        clearMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR,
                                    gtk.ICON_SIZE_MENU))
        clearMenuItem.connect('activate',
                                parentConversationWindow.clearOutputText)
        clearMenuItem.add_accelerator('activate', accelGroup, ord('L'),
            gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        closeMenuItem = gtk.ImageMenuItem(_('Close all'))
        closeMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE,
                                gtk.ICON_SIZE_MENU))
        closeMenuItem.connect('activate', self.onCloseActivate)
        closeMenuItem.add_accelerator('activate', accelGroup, ord('Q'),
            gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        conversationMenu.add(self.inviteMenuItem)
        conversationMenu.add(self.sendFileMenuItem)
        conversationMenu.add(clearMenuItem)
        conversationMenu.add(gtk.SeparatorMenuItem())
        conversationMenu.add(closeMenuItem)
        self.add(conversationMenuItem)

        # --- Format menu
        formatMenu = gtk.Menu()
        formatMenuItem = gtk.MenuItem(_("For_mat"))
        formatMenuItem.set_submenu(formatMenu)

        fontMenuItem = gtk.ImageMenuItem(gtk.STOCK_SELECT_FONT)
        colorMenuItem = gtk.ImageMenuItem(gtk.STOCK_SELECT_COLOR)

        fontMenuItem.connect('activate', self.onFontActivate)
        colorMenuItem.connect('activate', self.onColorActivate)

        formatMenu.add(fontMenuItem)
        formatMenu.add(colorMenuItem)
        self.add(formatMenuItem)

    def onCloseActivate(self, *args):
        '''This method is called when Close is activated on the menu'''
        self.parentConversationWindow.close()

    def onInviteActivate(self, *args):
        '''This method is called when Invite is activated on the menu'''
        self.parentConversationWindow.show_invite_dialog()

    def onSendFileActivate(self, *args):
        '''This method is called when Invite is activated on the menu'''
        self.parentConversationWindow.send_file_dialog()

    def onLogActivate(self, check):
        '''This method is called when Log is activated on the menu'''
        self.parentConversationWindow.conversation.setDoLog(
            check.get_active())

    def onFontActivate(self, *args):
        '''This method is called when font is activated on the menu'''
        self.parentConversationWindow.changeFont()

    def onColorActivate(self, *args):
        '''This method is called when color is activated on the menu'''
        self.parentConversationWindow.changeColor()

    def update(self, *args):
        '''This method is called when a switchboard error is detected'''
        self.inviteMenuItem.set_sensitive(False)
        self.sendFileMenuItem.set_sensitive(False)
