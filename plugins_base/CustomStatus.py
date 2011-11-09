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

import Plugin
import gtk
import re
import gobject
from Parser import TAGS_NONE

PLUGIN_NAME = 'CustomStatus'
DIALOG_TYPE_SET = 0
DIALOG_TYPE_CONFIG = 1


class MainClass(Plugin.Plugin):
    '''
    Main class of the plugin. It listens for self-status-changed event, 
    connects to unifiedParser, and provide a configuration dialog.
    '''

    description = _('Enable the use of customs status')
    authors = {'Alessandro Orrù' : 'casadiale@tiscali.it'}
    website = ''
    displayName = _('Custom Status')
    name = 'CustomStatus'
    def __init__(self, controller, msn):
        '''Constructor'''

        Plugin.Plugin.__init__(self, controller, msn)
        self.description = _('Enable the use of customs status')
        self.authors = {'Alessandro Orrù' : 'casadiale@tiscali.it'}
        self.website = ''
        self.displayName = _('Custom Status')
        self.name = PLUGIN_NAME
        self.config = controller.config
        self.config.readPluginConfig(self.name)
        self.customStatus = CustomStatus(controller, msn, self.config)
        self.enabled = False

    def start(self):
        self.onStatusChangeId = self.controller.msn.connect(\
                        'self-status-changed', self.customStatus.statusChanged)
        self.customStatusParserId = self.controller.unifiedParser.connect(\
                        'filter', self.customStatus.customStatusParser)
        self.controller.emit('preferences-changed')  
        self.customStatus.unsetCustomStatus()
        self.customStatus.register_slash_commands()
        self.statusMenuItem = gtk.MenuItem (_('Custom status...'), False)
        self.statusMenuItem.connect("activate", self.on_status_menu_activated)
        self.controller.mainWindow.userPanel.statusMenu.add(self.statusMenuItem)
        self.enabled = True

    def stop(self):
        self.disconnect(self.onStatusChangeId)
        self.controller.unifiedParser.disconnect(self.customStatusParserId)
        self.customStatus.unregister_slash_commands()
        self.controller.mainWindow.userPanel.statusMenu.remove(self.statusMenuItem)
        self.enabled = False

    def check(self):
        return (True, 'Ok')

    def configure(self):
        CustomStatusDialog(self.customStatus, DIALOG_TYPE_CONFIG).run()
        return True

    def on_status_menu_activated(self, item):
        self.customStatus.statusChanged(None, "AWY")

class CustomStatus:
    '''
    This is the core class of the plugin. It gives methods to parse the custom
    statuses of users, to change or remove custom status of current user, and 
    to save and remove custom statuses.
    '''

    def __init__ (self, controller, msn, config):
        '''Constructor'''
        self.controller = controller
        self.msn = msn
        self.config = config
        self.name = PLUGIN_NAME
        self.slash = controller.Slash

        # We need a semaphore to block the status changing
        self.doChange = True

        # Status list permitted as custom status
        self.permitted_status = ['AWY', 'BSY']

    def customStatusParser(self, obj, parser, filterdata):
        '''This method (connected to unifiedParser) replaces ugly {..} tag
        to a nicer (..) grey color tag.'''

        color = self.config.getPluginValue(PLUGIN_NAME, 'color', '#AAAAAA')
        format, objects = filterdata.serialize(filterdata.list)

        # We search the occurrence of the custom status tag
        statusTag = re.compile('[\s\xc2\xa0]*{[^{}]*}$')
        foundTag = statusTag.search(format)
        
        if foundTag:
            customTag = format[foundTag.start():foundTag.end()]            

            # We build a newTag and replace the old one to avoid replacing 
            # wrong { or }. We also check if pango is supported or not.
            # If it is, we put color codes, otherwise we remove the status.
            if not (parser and parser.tags != TAGS_NONE):
                format = statusTag.sub('', format)
            else:
                newTag = customTag.replace('\xc2\xa0{',\
                                            '<span foreground="'+color+'"> (')
                if newTag != customTag:
                    newTag = newTag.replace('}', ')</span>')
            	# We replace the old tag with newTag
           	    format = statusTag.sub(newTag, format)                

        # We pack the objects back
        filterdata.list = filterdata.deserialize(format, objects)        

    def statusChanged(self, msnp, status):
        '''We unset any previous custom status, then we open custom status 
        dialog if the status has changed to a valid one. Valid statuses are 
        defined by self.permitted_status.'''

        self.unsetCustomStatus()
        if self.doChange and status in self.permitted_status:
            # We temporary block custom status changing to avoid double-dialog
            self.doChange = False

            response = CustomStatusDialog(self, DIALOG_TYPE_SET, status, "status_changed").run()
            if response != None:
                status_type, status_name,\
                    automessage, automessage_text, slash_command = response
                self.setCustomStatus(status_type, status_name,\
                                        automessage, automessage_text)
            # We enable again custom status changing
            self.doChange = True

    def setCustomStatus(self, status_type, custom_status, automessage_enabled, 
                        autoreply_message):
        '''Method that sets a new custom status appending {..} tag to nickname,
        and eventually an autoreply message'''
       
        if custom_status != '': 
            self.msn.changeStatus(status_type)
            self.msn.changeNick(self.msn.getNick().rstrip() + \
                                '\xc2\xa0{'+custom_status+'}')
       
        if automessage_enabled and autoreply_message != '':            
            self.controller.config.user['autoReply'] = True
            self.controller.autoReplyMessage = autoreply_message
            self.controller.config.user['autoReplyMessage'] = autoreply_message

    def unsetCustomStatus(self):
        '''Method that strips the custom status tag (if any) from nickname'''
        
        statusTag = re.compile('[\s\xc2\xa0]*{[^{}]*}$')
        newnick = statusTag.sub('', self.msn.getNick())
        if self.msn.getNick() != newnick:
            self.msn.changeNick(statusTag.sub('', self.msn.getNick()))
        self.controller.config.user['autoReply'] = False

    def loadSavedStatus(self):
        '''Method that loads saved custom statuses. It returns a list of lists 
        [statustype, statusname, autoreplyenabled, autoreplymessage, slashcommand]'''

        numStatus = self.config.getPluginValue(self.name,\
                                                'custom_status_count', 0)
        data=[]         

        # We load all the custom status
        for i in range(int(numStatus)):
            cStatus = cName = cAR = cARMessage = None
            cStatus = self.config.getPluginValue(self.name,\
                                                    'cStatus'+str(i), None)
            cName = self.config.getPluginValue(self.name,\
                                                    'cName'+str(i), None)
            cAR = self.config.getPluginValue(self.name,\
                                                    'cAR'+str(i), None)
            cARMessage = self.config.getPluginValue(self.name,\
                                                    'cARMessage'+str(i), None)
            cCommand = self.config.getPluginValue(self.name, \
                                                    'cCommand'+str(i), "")

            if not (cStatus == None or cName == None or \
                    cAR == None or cARMessage == None):
                data.append([cStatus,cName,bool(int(cAR)),cARMessage, cCommand])        

        return data

    def saveSavedStatus(self, data):
        '''Method that saves the custom statuses saved list to config file.'''

        for i in range(len(data)):
            self.config.setPluginValue(self.name, 'cStatus'+str(i), data[i][0])
            self.config.setPluginValue(self.name, 'cName'+str(i), data[i][1])
            self.config.setPluginValue(self.name, 'cAR'+str(i), \
                                                        str(int(data[i][2])))
            self.config.setPluginValue(self.name, 'cARMessage'+str(i), \
                                                        data[i][3])
            self.config.setPluginValue(self.name, 'cCommand'+str(i), \
                                                        data[i][4])

        # We need to update custom statuses count
        self.config.setPluginValue(self.name, 'custom_status_count', len(data))

    def register_slash_commands(self):
        numStatus = self.config.getPluginValue(self.name,\
                                                'custom_status_count', 0)
        for i in range(int(numStatus)):
            cCommand = self.config.getPluginValue(self.name, \
                                                    'cCommand'+str(i), None)
            if not ((cCommand == None) or (cCommand == "")):
                self.slash.register(cCommand, self.on_slash_command, \
                                          _("Applies a custom status"))

    def unregister_slash_commands(self):
        numStatus = self.config.getPluginValue(self.name,\
                                                'custom_status_count', 0)
        for i in range(int(numStatus)):
            cCommand = self.config.getPluginValue(self.name, \
                                                    'cCommand'+str(i), None)
            if not ((cCommand == None) or (cCommand == "")):
                self.slash.unregister(cCommand)

    #search for al the custom statuses the one that matches the slash command
    def on_slash_command(self, slash_action):
        self.doChange = False
        data = self.loadSavedStatus()
        for i in data: #search every status
            if i[4] == slash_action.name: #if slash_command = custom status command
                self.setCustomStatus(i[0],i[1],i[2],i[3]) #change status
        self.doChange = True


class CustomStatusDialog(gtk.Dialog):
    '''
    Class that defines Custom Status gtk dialog. It permits to apply, save or
    delete a previously defined custom status, or to use one on-the-fly.
    '''

    def __init__(self, customStatus, dialog_type=DIALOG_TYPE_SET, \
                        current_status=None, source=""):
        '''Constructor'''
        
        gtk.Dialog.__init__(self , _('Custom status setting'), None, \
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, \
            gtk.STOCK_CANCEL, gtk.RESPONSE_CLOSE))

        self.dialog_type = dialog_type
        self.customStatus = customStatus
        self.controller = self.customStatus.controller

        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_size_request(550,-1)
        self.set_resizable(True)
        self.set_border_width(10)
        self.set_has_separator(False)
        self.vbox.set_spacing(15)

        #if the dialog appears changing status, the timer starts
        #if the dialog is open with the Configure button in plugins manager, no timer 
        if source == "status_changed":
            self.timer_time = 10
            self.title_text = _('Custom status setting - Closing in: %ds')
            text = self.title_text % self.timer_time
            self.set_property("title",text)
            self.timer = gobject.timeout_add(1000,self.updateTimer)
            self.set_focus_on_map(False) #dialog appears unfocused
            self.connect('focus-in-event', self.disableTimer) #when focused, stop the timer

        # We load the saved custom statuses
        self.data = self.customStatus.loadSavedStatus()

        # We add the panels to the dialog
        self.select_panel = CustomStatusAddRemoveContainer(self, self.data)
        if dialog_type == DIALOG_TYPE_SET:
            self.create_panel = CustomStatusCreate(self, current_status)
        else:
            self.create_panel = CustomStatusCreate(self)

        self.vbox.pack_start(self.select_panel)
        self.vbox.pack_start(gtk.HSeparator())
        self.vbox.pack_start(self.create_panel) 
        self.vbox.show_all()

        # Listeners
        self.connect('delete-event', self.closeCancel)
        self.create_panel.custom_status.connect('activate', self.closeAccept)
        self.create_panel.custom_autoreply_message.connect(\
                                                'activate', self.closeAccept)
        self.select_panel.btn_add.connect('clicked', self.addStatus)
        self.select_panel.btn_remove.connect('clicked', self.delStatus)
        if dialog_type == DIALOG_TYPE_SET:
            self.select_panel.treeview.connect(\
                                        'row-activated', self.statusChoosed)
            self.select_panel.btn_use.connect('clicked', self.applyStatus)

    def addStatus(self, *args):
        '''Method that adds a custom status inserted in create_panel to the
        custom status treeview when we click on btn_add button'''
        
        status = self.create_panel.getStatus()

        if status == None:
            return

        status_type,status_name, automessage, automessage_text, command = status
        if automessage == False:
            automessage_text = ''
        self.select_panel.data.append([status_type, status_name, \
                                        automessage, automessage_text, command])
        self.select_panel.treeview.addStatusRow(status_type, status_name, \
                                                automessage,automessage_text,command)
        self.create_panel.clear()

    def delStatus(self, *args):
        '''Method that deletes a custom status from the custom statuses list'''
        row = self.select_panel.treeview.delStatusRow()

    def applyStatus(self, *args):
        '''Method that applies a custom status selected from the treeview with
        a double-click on the row, and closes the gtk dialog'''
        self.dataOK = self.select_panel.treeview.getSelectedRow()
        self.response(gtk.RESPONSE_OK)

    def statusChoosed (self, path, view_column, *args):
        '''Method that applies a custom status selected from the treeview
        selecting the row and clicking on the Apply button. It also closes the
        gtk dialog.'''
        self.dataOK = self.data[view_column[0]]
        self.response(gtk.RESPONSE_OK)

    def closeAccept(self, *args):
        '''Click on Accept button'''
        self.response(gtk.RESPONSE_ACCEPT)

    def closeCancel(self, *args):
        '''Click on Cancel button'''
        self.response(gtk.RESPONSE_CLOSE)

    def run(self):
        '''Method that manage the open and close of the dialog.'''
        response = gtk.Dialog.run(self)
        self.destroy()

        # If we want to enable a custom status...
        if response == gtk.RESPONSE_ACCEPT or response == gtk.RESPONSE_OK:
            self.customStatus.unregister_slash_commands()

            # We save the configuration
            self.customStatus.saveSavedStatus(self.select_panel.data)

            self.customStatus.register_slash_commands()

            # We return the list containing choosed status settings.
            # If response is ACCEPT we use form data, else we use treeview data
            if response == gtk.RESPONSE_ACCEPT:
                return (self.create_panel.getStatus())
            return (self.dataOK)
        # ... or if we click on Cancel button
        else:   
            return None

    #this method updates the title of the dialog if the timer is running
    def updateTimer(self):
        self.timer_time = self.timer_time - 1
        text = self.title_text % self.timer_time
        self.set_property("title", text)
        if self.timer_time == 0:
            self.closeCancel()
            return False
        else:
            return True

    #disable the timer and change the title bar
    def disableTimer(self, widget, event):
        if self == widget:
            gobject.source_remove(self.timer)
            self.set_property("title", _('Custom status setting'))

class CustomStatusTreeView(gtk.TreeView):
    '''
    Table view of custom status. It inherits from gtk.TreeView.
    It contains one row for every custom status defined in config file.
    '''

    def __init__(self, controller, data):
        '''Constructor'''
        
        self.liststore = gtk.ListStore(str, str, bool, str, str)
        self.controller = controller
        self.data = data

        gtk.TreeView.__init__(self, self.liststore)

        # Cells
        cell0 = gtk.CellRendererPixbuf()
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererToggle()
        cell3 = gtk.CellRendererText()
        cell4 = gtk.CellRendererText()

        cell1.set_property('editable', True)
        cell1.connect('edited', self.onEdited, self.liststore, 1)
        cell2.set_property('activatable', True)
        cell2.connect('toggled', self.onToggled, self.liststore, 2)
        cell3.set_property('editable', True)
        cell3.connect('edited', self.onEdited, self.liststore, 3)
        cell4.set_property('editable', True)
        cell4.connect('edited', self.onEdited, self.liststore, 4)

        # Columns
        col0 = gtk.TreeViewColumn(_('Status'), cell0)
        col0.set_cell_data_func(cell0, self.getStatusCellPixbuf)
        col1 = gtk.TreeViewColumn(_('Status Name'), cell1, text=1)
        col2 = gtk.TreeViewColumn(_('A.R.'), cell2, active=2)
        col3 = gtk.TreeViewColumn(_('Autoreply message'), cell3, text=3)
        col4 = gtk.TreeViewColumn(_('Command'), cell4, text=4)
        
        col1.set_resizable(True)
        col3.set_resizable(True)
        col4.set_resizable(True)
        
        self.append_column(col0)
        self.append_column(col1)
        self.append_column(col2)
        self.append_column(col3)
        self.append_column(col4)

        # We add the data to the table
        for item in self.data:
            self.liststore.append(item)
    
    def addStatusRow(self, status, status_name, automessage, automessage_text, command):
        '''Method that adds a row to the table using the liststore object'''
        self.liststore.append([status, status_name, \
                                automessage, automessage_text, command])

    def getSelectedRow(self):
        '''Method that returns the currently selected row'''
        selection = self.get_selection()       
        result = selection.get_selected()
        if result: # result could be None
            model, iter = result
            if iter is not None:
                return self.data[model.get_path(iter)[0]]
            else:
                return None
                
    def delStatusRow(self):
        '''Method that deletes the selected row from the table'''
        selection = self.get_selection()       
        result = selection.get_selected()
        if result: #result could be None
           model, iter = result
           try:
               del self.data[model.get_path(iter)[0]]
               model.remove(iter)
           except:
               pass

    def onToggled(self, cell, path, model, cellnumber):
        '''Method that updates the checkboxes'''
        new_status = not model[path][cellnumber]
        model[path][cellnumber] = new_status
        self.data[int(path)][cellnumber] = str(int(new_status))

    def onEdited(self, cell, path, new_text, model, cellnumber):
        '''Method that updates string cells'''
        model[path][cellnumber] = new_text.strip()
        self.data[int(path)][cellnumber] = new_text.strip()

    def getStatusCellPixbuf(self, layout, cell, model, iter):
        '''Method that shows pixbuf for custom statuses'''
        item = model[iter][0]
        
        if item == None: 
            return
        pixbuf = self.controller.theme.statusToPixbuf(item).scale_simple(20,20,gtk.gdk.INTERP_BILINEAR)
        cell.set_property('pixbuf', pixbuf)


class CustomStatusAddRemoveContainer(gtk.VBox):
    '''
    Add/remove/edit container. VBox that provides an interface to previously 
    defined custom status. It permits the addition of new ones, the deletion of 
    old ones, and the edit of existing ones.
    '''

    def __init__(self, parent, data):
        gtk.VBox.__init__(self)
        self.controller = parent.controller
        self.data = data

        # Status table
        self.treeview = CustomStatusTreeView(self.controller, data)

        viewport = gtk.Viewport()
        viewport.set_size_request(-1, 150)
        viewport.set_shadow_type(gtk.SHADOW_IN)
        viewport.add(self.treeview)

        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledWindow.add(viewport) 

        # Add and remove buttons
        self.btn_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.btn_remove = gtk.Button(stock=gtk.STOCK_REMOVE)

        hbox = gtk.HBox()

        hbox_buttons = gtk.HButtonBox()        
        hbox_buttons.set_layout(gtk.BUTTONBOX_START)
        hbox_buttons.pack_start(self.btn_add)
        hbox_buttons.pack_start(self.btn_remove)

        hbox.pack_start(hbox_buttons)

        if parent.dialog_type == DIALOG_TYPE_SET:
            self.btn_use = gtk.Button(stock=gtk.STOCK_APPLY)
            hbox_buttons2 = gtk.HButtonBox()
            hbox_buttons2.set_layout(gtk.BUTTONBOX_END)
            hbox_buttons2.pack_start(self.btn_use)
            hbox.pack_start(hbox_buttons2)

        self.set_spacing(5)
        self.pack_start(scrolledWindow)
        self.pack_start(hbox)
        self.show_all()


class CustomStatusCreate(gtk.VBox):
    '''
    Status creation container. VBox that provides an interface for defining a 
    custom status. It can be used as an interface to a temporary status, or as 
    an interface for adding a new status to saved ones.
    '''

    def __init__(self, parent, selected_status = None):
        '''Constructor'''
        
        gtk.VBox.__init__(self)
        self.controller = parent.controller
        self.selected_status = selected_status
        self.dialog_type = parent.dialog_type

        self.set_spacing(20)

        label_status_type = gtk.Label(_('Status type: '))
        label_status_type.set_alignment(0.0, 0.5)

        # Status selector combobox. It takes statuses from permitted_status.
        self.list_store = gtk.ListStore(str, str)
        self.status_type = gtk.ComboBox(self.list_store)
        status_cell = gtk.CellRendererPixbuf()
        status_cellname = gtk.CellRendererText()
        self.status_type.pack_start(status_cell, False)
        self.status_type.pack_start(status_cellname, True)
        self.status_type.set_cell_data_func(\
                                        status_cell, self.getStatusCellPixbuf)
        self.status_type.add_attribute(status_cellname, 'text', 1)

        for i in parent.customStatus.permitted_status:
            status_number = self.controller.status_ordered[0].index(i)
            self.list_store.append(\
                        [i, self.controller.status_ordered[2][status_number]])

        for i in range(len(parent.customStatus.permitted_status)):
            if list(self.list_store[i])[0] == selected_status:
                self.status_type.set_active(i)
                break
        else:
            self.status_type.set_active(0)

        hbox0 = gtk.HBox()
        hbox0.pack_start(label_status_type)
        hbox0.pack_start(self.status_type)
        self.pack_start(hbox0)

        # Custom status text entry
        label_custom_status = gtk.Label(_('Custom status: '))
        label_custom_status.set_alignment(0.0, 0.5)
        self.custom_status = gtk.Entry()
        self.custom_status.set_width_chars(30)
        
        hbox1 = gtk.HBox()
        hbox1.pack_start(label_custom_status)
        hbox1.pack_start(self.custom_status)
        self.pack_start(hbox1)

        # Autoreply enabler checkbox and text entry
        self.custom_autoreply_checkbox = gtk.CheckButton(_('Enable'))
        self.custom_autoreply_checkbox.set_active(False)
        self.custom_autoreply_checkbox.connect('toggled', self.enableAutoreply)

        self.label_custom_autoreply_message = gtk.Label(_('Message: '))
        self.label_custom_autoreply_message.set_alignment(0.0, 0.5)
        self.label_custom_autoreply_message.set_width_chars(15)
        self.label_custom_autoreply_message.set_sensitive(False)
        self.custom_autoreply_message = gtk.Entry()
        self.custom_autoreply_message.set_width_chars(30)
        self.custom_autoreply_message.set_text(\
                            self.controller.config.user['autoReplyMessage'])
        self.custom_autoreply_message.set_sensitive(False)

        tablebox_autoreply = gtk.Table(2, 2)
        tablebox_autoreply.set_border_width(12)
        tablebox_autoreply.set_row_spacings(5)
        tablebox_autoreply.attach(self.custom_autoreply_checkbox, 0, 2, 0, 1)
        tablebox_autoreply.attach(self.label_custom_autoreply_message, \
                                                                    0, 1, 1, 2)
        tablebox_autoreply.attach(self.custom_autoreply_message, 1, 2, 1, 2)

        frame_autoreply = gtk.Frame(_('Autoreply'))
        frame_autoreply.add(tablebox_autoreply)

        self.pack_start(frame_autoreply)

    def clear(self):
        '''Method that clears the form'''
        self.custom_status.set_text('')
        self.custom_autoreply_checkbox.set_active(False)
        self.custom_autoreply_message.set_text('')

    def setStatus(self, status):
        '''Method that fills the form with status'''
        self.custom_status.set_text(status[0])
        self.custom_autoreply_checkbox.set_active(status[1])
        self.custom_autoreply_message.set_text(status[2])
        self.status_type.set_active(0)

    def getStatus(self):
        '''Method that returns a list containing the status parameters'''
        if self.custom_status.get_text().strip() == '':
            return None

        return (list(self.status_type.get_model()[ \
                                    self.status_type.get_active_iter()])[0], \
                 self.custom_status.get_text().strip(), \
                 self.custom_autoreply_checkbox.get_active(), \
                 self.custom_autoreply_message.get_text().strip(),"")

    def enableAutoreply (self, *args):
        '''Method that enables autoreply text entry'''
        if self.custom_autoreply_checkbox.get_active():
            self.label_custom_autoreply_message.set_sensitive(True)
            self.custom_autoreply_message.set_sensitive(True)
        else:
            self.label_custom_autoreply_message.set_sensitive(False)
            self.custom_autoreply_message.set_sensitive(False)


    def getStatusCellPixbuf(self, layout, cell, model, iter):
        '''Method that shows pixbuf for statuses'''
        item = model[iter][0]
        
        if item == None: 
            return
        pixbuf = self.controller.theme.statusToPixbuf(item).scale_simple(20,20,gtk.gdk.INTERP_BILINEAR)
        cell.set_property('pixbuf', pixbuf)
