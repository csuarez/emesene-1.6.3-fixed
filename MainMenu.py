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
import desktop
import StatusMenu
import PreferenceWindow
import SmilieWindow

import stock
import dialog

import os
from xml.dom.minidom import parseString

class MainMenu(gtk.MenuBar):
    '''this class represent the main menu in the main window'''

    def __init__(self, controller, window_type, accelGroup):
        '''constructor'''
        gtk.MenuBar.__init__(self)

        self.controller = controller
        self.config = self.controller.config
        self.theme = self.controller.theme

        fileMenu = gtk.Menu()
        fileMenuItem = self.newImageMenuItem(_('_Account'))
        fileMenuItem.set_submenu(fileMenu)

        # If we're in login window we don't need the View
        # or the Actions Menu
        if window_type == 'userlist':
            actionsMenu = gtk.Menu()
            actionsMenuItem = self.newImageMenuItem(_('_Contacts'))
            actionsMenuItem.connect('activate', self.on_actions_activate)
            actionsMenuItem.set_submenu(actionsMenu)

        optionsMenu = gtk.Menu()
        optionsMenuItem = self.newImageMenuItem(_('_Options'))
        optionsMenuItem.set_submenu(optionsMenu)

        helpMenu = gtk.Menu()
        helpMenuItem = self.newImageMenuItem(_('_Help'))
        helpMenuItem.set_submenu(helpMenu)

        # ---------------------- ACCOUNT MENU --------------------------------

        # In login window only quit option is usefull
        if window_type == 'userlist':
            statusMenuItem = self.newImageMenuItem(_('_Status'))
            statusMenu = StatusMenu.StatusMenu(self.controller)

            statusMenuItem.set_submenu(statusMenu)
            fileMenu.add(statusMenuItem)

            self.disconnectItem = self.newStockImageMenuItem(gtk.STOCK_DISCONNECT)
            fileMenu.add(gtk.SeparatorMenuItem())
            fileMenu.add(self.disconnectItem)
        else:
            getliveMenuItem = self.newImageMenuItem(_('_New account'), \
                                                    gtk.STOCK_NEW)
            fileMenu.add(getliveMenuItem)
            fileMenu.add(gtk.SeparatorMenuItem())

        # Quit option is always visible
        quitMenuItem = self.newStockImageMenuItem(gtk.STOCK_QUIT)
        quitMenuItem.add_accelerator('activate', accelGroup, ord('Q'), \
                                 gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        fileMenu.add(quitMenuItem)

        accelGroup.connect_group(ord('Q'), gtk.gdk.CONTROL_MASK, \
            gtk.ACCEL_LOCKED, self.on_quit_activate)

        # ------------------- CONTACTS MENU --------------------------------

        # Contacts Menu is useless in login window
        if window_type == 'userlist':
            # Add user, remove
            addUserMenuItem = self.newImageMenuItem(_('_Add contact'), \
                                                     gtk.STOCK_ADD)
            actionsMenu.add(addUserMenuItem)

            contactsActionGroup = gtk.ActionGroup('contacts')
            self.contactsActionGroup = contactsActionGroup

            setAliasAction = gtk.Action('setAlias',
                _('_Set contact alias...'), None, gtk.STOCK_EDIT)
            moveAction = gtk.Action('move', _('M_ove to group'), \
                                     None, gtk.STOCK_REDO)
            blockAction = gtk.Action('block', _('_Block'), \
                                        None, gtk.STOCK_STOP)
            unblockAction = gtk.Action('unblock', _('_Unblock'), \
                                        None, gtk.STOCK_APPLY)
            deleteAction = gtk.Action('delete', _('_Remove contact'), \
                                        None, gtk.STOCK_DELETE)

            self.blockAction = blockAction
            self.unblockAction = unblockAction

            contactsActionGroup.add_action(setAliasAction)
            actionsMenu.add(setAliasAction.create_menu_item())
            contactsActionGroup.add_action(blockAction)
            actionsMenu.add(blockAction.create_menu_item())
            contactsActionGroup.add_action(unblockAction)
            actionsMenu.add(unblockAction.create_menu_item())
            contactsActionGroup.add_action(moveAction)
            self.moveMenuItem = moveAction.create_menu_item()
            self.moveToGroupMenuSelected(self.moveMenuItem)
            self.moveMenuItem.connect('activate', self.moveToGroupMenuSelected)
            actionsMenu.add(self.moveMenuItem)
            contactsActionGroup.add_action(deleteAction)
            actionsMenu.add(deleteAction.create_menu_item())

            actionsMenu.add(gtk.SeparatorMenuItem())

            # Groups action group: Add, remove, rename
            addGroupMenuItem = self.newImageMenuItem(_('Add _group'),
                gtk.STOCK_ADD)
            actionsMenu.add(addGroupMenuItem)

            groupsActionGroup = gtk.ActionGroup('groups')
            self.groupsActionGroup = groupsActionGroup

            renameAction = gtk.Action('rename', _('Re_name group'), \
                                        None, gtk.STOCK_EDIT)
            deleteGAction = gtk.Action('remove', _('Re_move group'), \
                                        None, gtk.STOCK_DELETE)

            groupsActionGroup.add_action(renameAction)
            actionsMenu.add(renameAction.create_menu_item())
            groupsActionGroup.add_action(deleteGAction)
            actionsMenu.add(deleteGAction.create_menu_item())

            actionsMenu.add(gtk.SeparatorMenuItem())

            # Show Contacts
            FilterContactsMenuItem = self.newImageMenuItem(_("Show..."))
            FilterContactsMenu = gtk.Menu()
            FilterContactsMenuItem.set_submenu(FilterContactsMenu)
            FilterContactsMenuItem.show_all()
            actionsMenu.add(FilterContactsMenuItem)

            self.showByNick = self.newCheckMenuItem(_('Contacts by _nick'), \
                    self.config.user['showByNick'])
            self.showOffline = self.newCheckMenuItem(_('Contacts _offline'), \
                    self.config.user['showOffline'])
            self.showEmptyGroups = self.newCheckMenuItem(
             _('_Empty groups'), self.config.user['showEmptyGroups'])
            self.showCountContact = self.newCheckMenuItem(
                _('_Contact count'),
                self.config.user['showCountContact'])

            FilterContactsMenu.add(self.showByNick)
            FilterContactsMenu.add(self.showOffline)
            FilterContactsMenu.add(self.showEmptyGroups)
            FilterContactsMenu.add(self.showCountContact)

            # Order Contacts
            OrderContactsMenuItem = self.newImageMenuItem(_("Order contacts by..."))
            OrderContactsMenu = gtk.Menu()
            OrderContactsMenuItem.set_submenu(OrderContactsMenu)
            OrderContactsMenuItem.show_all()
            actionsMenu.add(OrderContactsMenuItem)

            self.orderByGroup = gtk.RadioMenuItem(None, \
                                                      _('_Group-ordered'))
            self.orderByStatus = gtk.RadioMenuItem(self.orderByGroup, \
                                                      _('_Status-ordered'))
            if not self.config.user['orderByStatus']:
                self.orderByGroup.set_active(True)
            else:
                self.orderByStatus.set_active(True)

            OrderContactsMenu.add(self.orderByGroup)
            OrderContactsMenu.add(self.orderByStatus)

            # Menu items to switch the contacts within each group
            SortContactsMenuItem = self.newImageMenuItem(_("Sort contacts by..."))
            SortContactsMenu = gtk.Menu()
            SortContactsMenuItem.set_submenu(SortContactsMenu)
            SortContactsMenuItem.show_all()
            actionsMenu.add(SortContactsMenuItem)

            self.orderGroupByEmail = gtk.RadioMenuItem(None, \
                                                      _('E_mail'))
            self.orderGroupByNick = gtk.RadioMenuItem(self.orderGroupByEmail, \
                                                      _('N_ick'))

            if self.config.user['sortNickGroupByContact']:
                self.orderGroupByEmail.set_active(True)
            else:
                self.orderGroupByNick.set_active(True)

            SortContactsMenu.add(self.orderGroupByEmail)
            SortContactsMenu.add(self.orderGroupByNick)

            actionsMenu.add(gtk.SeparatorMenuItem())

            # Export contact list
            exportMenu = gtk.Menu()
            exportAsPlain = self.newImageMenuItem(_('As plain text'), \
                                                    gtk.STOCK_FILE)
            exportAsCtt = self.newImageMenuItem(_('As .Ctt'), \
                                                    gtk.STOCK_DIALOG_AUTHENTICATION)
            exportMenu.add(exportAsPlain)
            exportMenu.add(exportAsCtt)
            export = self.newImageMenuItem(_('Save contact list...'), \
                                                    gtk.STOCK_FLOPPY)
            export.set_submenu(exportMenu)
    
            exportAsPlain.connect('activate', self.on_export_activate,'plain')
            exportAsCtt.connect('activate', self.on_export_activate,'ctt')
            actionsMenu.add(export)


        # ------------------------ OPTIONS MENU ---------------------------

        if window_type == 'userlist':
            #profileMenuItem to replace nick and avatar menu items
            changeProfileMenuItem = self.newImageMenuItem(\
                _('Change profile...'), gtk.STOCK_EDIT)
            optionsMenu.add(changeProfileMenuItem)

            optionsMenu.add(gtk.SeparatorMenuItem())

            autoReplyMenuItem = self.newImageMenuItem(\
                _('A_utoreply'), gtk.STOCK_EDIT)

            optionsMenu.add(autoReplyMenuItem)

            optionsMenu.add(gtk.SeparatorMenuItem())

            # Add Emoticon's
            addEmoticonMenuItem = self.newImageMenuItem(_('_Add an emoticon...'), \
                                                     gtk.STOCK_ADD)
            optionsMenu.add(addEmoticonMenuItem)

            optionsMenu.add(gtk.SeparatorMenuItem())

            pluginMenuItem = self.newImageMenuItem(_('P_lugins'), \
                gtk.STOCK_EXECUTE)
            optionsMenu.add(pluginMenuItem)

        preferencesMenuItem = self.newStockImageMenuItem(
            gtk.STOCK_PREFERENCES)
        preferencesMenuItem.add_accelerator('activate', accelGroup, \
            ord('P'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        optionsMenu.add(preferencesMenuItem)

        accelGroup.connect_group(ord('P'), gtk.gdk.CONTROL_MASK, \
            gtk.ACCEL_LOCKED, self.on_preferences_activate)

        # ---------------------- HELP MENU --------------------------------

        aboutMenuItem = self.newStockImageMenuItem(gtk.STOCK_ABOUT)
        comunityMenuItem = self.newImageMenuItem( \
                _('Community '), gtk.STOCK_INFO)
        homeMenuItem = self.newImageMenuItem( \
                _('_Homepage'), gtk.STOCK_HOME)

        helpMenu.add(homeMenuItem)
        helpMenu.add(comunityMenuItem)
        helpMenu.add(gtk.SeparatorMenuItem())
        helpMenu.add(aboutMenuItem)

        self.add(fileMenuItem)

        # No Actions Menu in login window
        if window_type == 'userlist':
            self.add(actionsMenuItem)

        self.add(optionsMenuItem)
        self.add(helpMenuItem)

        # -------------------- CALLBACKS ----------------------------------

        quitMenuItem.connect('activate', self.on_quit_activate)
        aboutMenuItem.connect('activate', self.on_about_activate)
        homeMenuItem.connect('activate', self.on_click_url, \
            'http://www.emesene.org/', None)
        comunityMenuItem.connect('activate', self.on_click_url, \
            'http://forum.emesene.org', None)
        # We don't need this callbacks in login window,
        # because we didn't create this menu items
        if window_type == 'userlist':
            self.disconnectItem.connect('activate', self.on_logout_activate)
            self.orderByGroup.connect('activate', self.on_order_changed)
            self.orderByStatus.connect('activate', self.on_order_changed)

            self.orderGroupByEmail.connect('activate',
                self.on_group_order_changed)
            self.orderGroupByNick.connect('activate',
                self.on_group_order_changed)

            self.showByNick.connect('activate',
                self.on_show_by_nick_activate)
            self.showOffline.connect('activate',
                self.on_show_offline_activate)
            self.showEmptyGroups.connect('activate',
                self.on_show_empty_groups_activate)
            self.showCountContact.connect('activate',
                self.on_show_count_contact_activate)
            addUserMenuItem.connect('activate', self.on_add_user_activate)
            addEmoticonMenuItem.connect('activate', self.on_emoticon_activate)
            setAliasAction.connect('activate', self.on_rename_user_activate)
            deleteAction.connect('activate', self.on_delete_user_activate)
            addGroupMenuItem.connect('activate', self.on_add_group_activate)
            deleteGAction.connect('activate', self.on_delete_group_activate)
            blockAction.connect('activate', self.on_block_user_activate)
            unblockAction.connect('activate', self.on_unblock_user_activate)
            renameAction.connect('activate', self.on_rename_group_activate)
            autoReplyMenuItem.connect('activate',
                self.on_set_auto_reply_activate)
            changeProfileMenuItem.connect('activate',
                self.on_change_profile_activate)
            pluginMenuItem.connect('activate', self.on_plugin_activate)
        else:
            getliveMenuItem.connect('activate', self.on_get_live_activate)

        preferencesMenuItem.connect('activate',
            self.on_preferences_activate)

    def moveToGroupMenuSelected(self, menu):
        '''build the submenu, please'''
        moveMenu = gtk.Menu()

        groups = self.controller.msn.getGroupNames()
        if groups == []:
            addGroupMenuItem = self.newImageMenuItem(_('Add _group'),
                gtk.STOCK_ADD)
            moveMenu.add(addGroupMenuItem)
            addGroupMenuItem.connect('activate', self.on_add_group_activate)
        else:
            for i in groups:
                i = i.replace('_', '__') # don't use _ as mnemonic
                menuItem = gtk.MenuItem (i)
                moveMenu.add(menuItem)
                menuItem.connect('activate', self.on_move_to_activate, i)
           
        self.moveMenuItem.set_submenu(moveMenu)
        moveMenu.show_all()
            
    def newStockImageMenuItem (self, stock):
        '''create a new image menu item from gtk's stock and retrun it'''

        mi = gtk.ImageMenuItem(stock)
        return mi

    def newImageMenuItem(self, label, stock = None, img = None):
        '''create a new Imege menu item and return it, it could have a
            stock image or a custom image'''

        mi = gtk.ImageMenuItem(_(label))

        if stock:
            mi.set_image(gtk.image_new_from_stock(stock,
                gtk.ICON_SIZE_MENU))
        elif img:
            image = gtk.Image()
            image.set_from_pixbuf(img)
            mi.set_image(image)

        return mi

    def newCheckMenuItem(self, label, checked):
        '''create a new checkbox and return it, if checked is true,
            the check box will be checked (d'uh!)'''

        mi = gtk.CheckMenuItem(_(label))
        mi.set_active(checked)
        return mi

    # -------------------------- CALLBACKS -------------------------------

    def on_export_activate(self, dialog,format):
        chooser = gtk.FileChooserDialog(title=_('Save contact list as...'),action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        if format=='ctt':
            filter.set_name('Contacts files')
            filter.add_pattern('*.ctt')
            chooser.set_current_name('myContacts.ctt')
        else:
            filter.set_name('All files')
            filter.add_pattern('*')
            chooser.set_current_name(_('myContacts'))
        chooser.add_filter(filter)
        if os.name != "nt":
            folder = os.environ['HOME']
        else:
            folder = os.environ['HOMEPATH']
        chooser.set_current_folder(folder)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            all_contacts = self.controller.contacts.get_all_contacts()
            f = open (chooser.get_filename(), 'w')
            if format=='ctt':
                doc = parseString('<messenger/>'.encode('UTF-8'))
                art = doc.documentElement
                serviceElement = doc.createElementNS(None,'service')
                serviceElement.setAttribute('name', '.NET Messenger Service')
                art.appendChild(serviceElement)
                contactlistElement = doc.createElementNS(None,'contactlist')
                serviceElement.appendChild(contactlistElement)
                for contact in all_contacts:
                    contactElement = doc.createElementNS(None,'contact')
                    contactElement.setAttribute('type', '1')
                    contactElement.appendChild(doc.createTextNode(str(contact.account)))
                    contactlistElement.appendChild(contactElement)
                out = str(doc.toxml())
            else:
                contactAccounts = []
                for contact in all_contacts:
                    contactAccounts.append(str(contact.account))
                out = '\n'.join(contactAccounts)
            f.write(out)
            f.close()
        chooser.destroy()

    def on_move_to_activate(self, menuItem, group):
        self.controller.contacts.move_to_group(self.userName,
            self.userGroup, group)

    def on_rename_user_activate(self, *args):
        self.controller.contacts.set_alias_dialog(self.userName)

    def on_actions_activate(self, *args):
        data = self.controller.getMenuData()
        typeSelected = data[0]

        self.contactsActionGroup.set_visible(typeSelected == 'user')
        self.groupsActionGroup.set_visible\
                    (typeSelected == 'group' and data[2] != 'nogroup')

        # set selected data class-available
        # set some action's senstibility
        if typeSelected == 'user':
            self.userName = data[1]
            self.userGroup = data[2]
            # block/unblock
            blocked = data[4]
            self.blockAction.set_visible(not blocked)
            self.unblockAction.set_visible(blocked)
        if typeSelected == 'group':
            self.groupName = data[1]

    def on_quit_activate(self, *args):
        self.controller.quit(0)

    def on_preferences_activate(self, *args):
        if not self.controller.preference_open:
            PreferenceWindow.PreferenceWindow(self.controller,
                self.config, self.controller.mainWindow).show()
            self.controller.preference_open = True


    def on_about_activate(self, *args):
        try:
            f = file('COPYING', 'r')
        except:
            f = None

        def closeAbout(widget, response_id):
            if response_id == gtk.RESPONSE_CANCEL:
                widget.destroy()

        gtk.about_dialog_set_url_hook(lambda *args:None)
        about = gtk.AboutDialog()
        about.set_name(self.controller.NAME)
        about.set_version(self.controller.VERSION)
        about.set_copyright(self.controller.COPYRIGHT)
        about.set_comments(self.controller.COMMENT)
        about.connect('response', closeAbout)

        if f == None:
            about.set_license(self.controller.LICENSE_FALLBACK)
        else:
            about.set_license(f.read())

        about.set_website(self.controller.WEBSITE)
        about.set_authors(self.controller.AUTHORS)
        about.set_translator_credits(_('translator-credits'))
        icon = self.controller.theme.getImage('login')
        about.set_icon(icon)
        about.set_logo(icon)
        about.run()

    def on_click_url(self, dialog, link, user_data):
        desktop.open(link)

    def on_logout_activate(self, *args):
        self.controller.logout()

    def on_order_changed(self, menuitem):
        if menuitem == self.orderByGroup:
            self.controller.config.user['orderByStatus'] = False
        elif menuitem == self.orderByStatus:
            self.controller.config.user['orderByStatus'] = True

        self.controller.refreshUserList()

    def on_group_order_changed(self, menuitem):
        if menuitem == self.orderGroupByNick:
            self.controller.config.user['sortNickGroupByContact'] = False
        elif menuitem == self.orderGroupByEmail:
            self.controller.config.user['sortNickGroupByContact'] = True

        self.controller.refreshUserList()

    def on_show_by_nick_activate(self, *args):
        self.controller.config.user['showByNick'] = \
            self.showByNick.get_active()
        self.controller.refreshUserList()

    def on_show_offline_activate(self, *args):
        self.controller.config.user['showOffline'] = \
            self.showOffline.get_active()
        self.controller.mainWindow.userList.refilter()

    def on_show_empty_groups_activate(self, *args):
        self.controller.config.user['showEmptyGroups'] = \
            self.showEmptyGroups.get_active()
        self.controller.mainWindow.userList.refilter()

    def on_show_count_contact_activate(self, *args):
        self.controller.config.user['showCountContact'] = \
            self.showCountContact.get_active()
        self.controller.refreshUserList()

    def on_emoticon_activate(self, *args):
        smilieWindow = SmilieWindow.SmilieWindow(self.controller, \
                                                None, None)
        smilieWindow.addClicked(None, self.controller)

    def on_add_user_activate(self, *args):
        self.controller.addUserDialog()

    def on_delete_user_activate(self, *args):
        self.controller.contacts.remove(self.userName)

    def on_add_group_activate(self, *args):
        self.controller.groups.add_dialog()

    def on_block_user_activate(self, *args):
        self.controller.contacts.block(self.userName)

    def on_unblock_user_activate(self, *args):
        self.controller.contacts.unblock(self.userName)

    def on_delete_group_activate(self, *args):
        self.controller.removeGroup(self.groupName)

    def on_rename_group_activate(self, *args):
        self.controller.groups.rename_dialog(self.groupName)

    def on_change_avatar_activate(self, *args):
        self.controller.set_picture_dialog()

    def on_change_nick_activate(self, *args):
        self.controller.contacts.set_nick_dialog()

    def on_change_profile_activate(self, *args):
        self.controller.change_profile_dialog()

    def on_set_auto_reply_activate(self, *args):
        def response_cb(response, message=''):
            '''callback for the set autoreply dialog'''
            if response == gtk.RESPONSE_ACCEPT:
                if self.checkbox.get_active() and message == '':
                    dialog.error(_("Empty autoreply"))
                else:
                    self.config.user['autoReply'] = self.checkbox.get_active()
                    self.config.user['autoReplyMessage'] = message

        replyDialog = gtk.Dialog( _("Autoreply") , None,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                           gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        replyDialog.set_border_width(2)

        self.checkbox = gtk.CheckButton(_('Activate au_toreply'))
        self.checkbox.set_active(self.config.user['autoReply'])

        self.entry = gtk.Entry()
        self.entry.set_text(self.config.user['autoReplyMessage'])
        self.entry.set_sensitive(self.checkbox.get_active())
        self.entry.set_size_request(300,-1)
        label = gtk.Label()
        label.set_text(_("Autoreply message:"))
        aligLabel = gtk.Alignment(xalign=0.0)
        aligLabel.add(label)
        aligLabel.set_padding(0,0,15,0)
        aligEntry = gtk.Alignment()
        aligEntry.set_padding(0, 0, 15, 15)
        aligEntry.add(self.entry)

        replyDialog.vbox.set_spacing(4)
        replyDialog.vbox.pack_start(self.checkbox, False, False)
        replyDialog.vbox.pack_start(aligLabel, False, False)
        replyDialog.vbox.pack_start(aligEntry, False, False)
        replyDialog.vbox.show_all()

        self.checkbox.connect('toggled', self.on_auto_reply_toggled)

        response = replyDialog.run()
        response_cb(response, self.entry.get_text())
        replyDialog.destroy()

    def on_auto_reply_toggled(self, check):
        self.entry.set_sensitive(check.get_active())

    def on_plugin_activate(self, *args):
        if not self.controller.preference_open:
            PreferenceWindow.PreferenceWindow(self.controller,
                self.config, self.controller.mainWindow, 6).show() #6 is the index of the plugin page
            self.controller.preference_open = True

    def on_get_live_activate(self, *args):
        link = 'https://signup.live.com/signup.aspx'
        desktop.open(link)
