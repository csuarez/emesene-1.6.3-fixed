# -*- coding: utf-8 -*-

# This file is part of emesene.
#
# Emesene is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# emesene is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with emesene; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import gtk
import os
import gobject
import shutil
import paths
import Theme
import UserList
import htmltextview
import desktop
from emesenelib import soap
from htmltextview import HtmlTextView
import dialog
import abstract.stock
from Widgets import WidgetToggleBox

HAVE_WEBCAM = 1
try:
     import WebcamDevice
except:
     print 'Webcam unavailable'
     HAVE_WEBCAM = 0
# gstreamer and /dev/ folder is not in windows or mac, isn't it?
if os.name != 'posix':
     HAVE_WEBCAM = 0

# For the ListStore
LIST = [ 
    {'stock_id' : gtk.STOCK_HOME, 'text' : _('General')},
    {'stock_id' : gtk.STOCK_SELECT_COLOR,'text' : _('Theme')},
    {'stock_id' : gtk.STOCK_MEDIA_NEXT,'text' : _('Sounds')},
    {'stock_id' : gtk.STOCK_FULLSCREEN,'text' : _('Interface')},
    {'stock_id' : gtk.STOCK_ORIENTATION_PORTRAIT,'text' : _('Privacy')},
    {'stock_id' : gtk.STOCK_NETWORK,'text' : _('Connection')},
    {'stock_id' : gtk.STOCK_DISCONNECT,'text' : _('Plugins')},
    {'stock_id' : gtk.STOCK_LEAVE_FULLSCREEN,'text' : _('Desktop')},
    {'stock_id' : gtk.STOCK_DIALOG_WARNING,'text' : _('Advanced')},
]

XALIGN = 0.50 #0.50
XSCALE = 0.90 #0.90

SPACING = 8
PADDING = 5

class PreferenceWindow(gtk.Window):

    def __init__(self, controller, config, parent, setPage=0):
        '''Contructor'''
        gtk.Window.__init__(self)

        self.controller = controller
        self.set_default_size(600, 400)
        #self.set_size_request(600,400) #600, 400
        self.set_title(_('Preferences'))
        self.set_role('preferences')
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_resizable(False)
        pix = self.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU)
        self.set_icon(pix)

        self.config = config
        self.set_transient_for(parent)

        self.set_border_width(6)

        # Create the close button.
        bClose = gtk.Button(stock=gtk.STOCK_CLOSE)

        ''' TREE VIEW STUFF '''
        # Create the list store model for the treeview.
        listStore = gtk.ListStore(gtk.gdk.Pixbuf, str)

        # This is mimicing the "self.controller.connected" flag
        self.connected = self.controller.connected

        # Append items to the model
        if self.connected:
            for i in LIST:
                #we should use always the same icon size, we can remove that field in LIST
                listStore.append([self.render_icon(i['stock_id'], \
                                  gtk.ICON_SIZE_LARGE_TOOLBAR), i['text']])
        else:
            for j in [0, 5, 7, 8]:
                i = LIST[j]
                listStore.append([self.render_icon(i['stock_id'], \
                                  gtk.ICON_SIZE_LARGE_TOOLBAR), i['text']])

        # Create the TreeView
        treeView = gtk.TreeView(listStore)

        # Create the renders
        cellText = gtk.CellRendererText()
        cellPix = gtk.CellRendererPixbuf()

        # Create the single Tree Column
        treeViewColumn = gtk.TreeViewColumn('Categories')

        treeViewColumn.pack_start(cellPix, expand=False)
        treeViewColumn.add_attribute(cellPix, 'pixbuf',0)
        treeViewColumn.pack_start(cellText, expand=True)
        treeViewColumn.set_attributes(cellText, text=1)

        treeView.append_column(treeViewColumn)
        treeView.set_headers_visible(False)
        treeView.connect('cursor-changed', self._on_row_activated)
        self.treeview = treeView

        ''' FRAME STUFF '''
        '''
        frame = gtk.AspectFrame(ratio=1.39,obey_child=True) 
        frame.set_shadow_type(gtk.SHADOW_NONE)
        self.aspect_frame = frame
        '''
        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.notebook.set_resize_mode(gtk.RESIZE_QUEUE)
        self.notebook.set_scrollable(True)

        ''' PACK TREEVIEW, FRAME AND HBOX '''
        vbox = gtk.VBox()
        vbox.set_spacing(4)
        hbox = gtk.HBox(homogeneous=False, spacing=5)
        hbox.pack_start(treeView, True,True) # False, True
        hbox.pack_start(self.notebook, True, True)
        vbox.pack_start(hbox, True,True) # hbox, True, True
        
        ''' BUTTON BOX FOR CLOSE BUTTON '''
        hButBox = gtk.HButtonBox()
        hButBox.set_spacing(4)
        hButBox.set_layout(gtk.BUTTONBOX_END)
        hButBox.pack_start(bClose)
        vbox.pack_start(hButBox, False, False)

        # Create a dict that stores each page
        self.page_dict = []

        # If emesene is connected, show all the settings.  If not, only show connection.
        if self.connected:
            # Keep local copies of the objects
            self.general_page = GeneralPage(self.config, self.controller)
            self.theme_page = ThemePage(self.config, self.controller)
            self.sounds_page = SoundsPage(self.config, self.controller)
            self.interface_page = InterfacePage(self.config, self.controller)
            self.privacy_page = PrivacyPage(self.config, self.controller)
            self.connection_page = ConnectionPage(self.config, self.controller)
            self.plugins_page = PluginsPage(self.config, self.controller)
            self.desktop_page = DesktopPage(self.config, self.controller)
            self.advanced_page = AdvancedPage(self.config, self.controller)

            # Whack the pages into a dict for future reference
            self.page_dict.append(self.general_page)
            self.page_dict.append(self.theme_page)
            self.page_dict.append(self.sounds_page)
            self.page_dict.append(self.interface_page)
            self.page_dict.append(self.privacy_page)
            self.page_dict.append(self.connection_page)
            self.page_dict.append(self.plugins_page)
            self.page_dict.append(self.desktop_page)
            self.page_dict.append(self.advanced_page)

            if HAVE_WEBCAM == 1:
                listStore.append([self.controller.theme.getImage('cam'), _('Webcam')])
                self.webcam_page = WebcamPage(self.config, self.controller)
                self.page_dict.append(self.webcam_page)

            self.controller.msn.connect('user-disconnected', self.close)
            self.controller.msn.connect('connection-problem', self.close)
            self.controller.msn.connect('connection-closed', self.close)
            self.controller.msn.connect('disconnected', self.close)
            self.controller.mainWindow.menu.disconnectItem.connect(\
                                        'button-release-event', self.close)
                                        #why the 'activate' signal is not emmited??
            if self.controller.trayIcon != None and \
               self.controller.trayDisconnect != None:
                self.controller.trayDisconnect.connect('activate', self.close)

        # These can appear if connection is False.
        else:
            self.general_page = GeneralPage(self.config, self.controller)
            self.connection_page = ConnectionPage(self.config, self.controller)
            self.desktop_page = DesktopPage(self.config, self.controller)
            self.advanced_page = AdvancedPage(self.config, self.controller)
            self.page_dict.append(self.general_page)
            self.page_dict.append(self.connection_page)
            self.page_dict.append(self.desktop_page)
            self.page_dict.append(self.advanced_page)
            self.set_modal(True)

        for i in range(len(self.page_dict)):
            self.notebook.append_page(self.page_dict[i])

        # Add the VBox to the Window
        self.add(vbox)

        # Set the pages visiblities.
        self.treeview.set_cursor(setPage) #the row-selected signal callback calls the showPage

        self.show_all()

        # Register events for the close button and window
        self.connect('delete-event', self.close)
        bClose.connect('clicked', self.close)

    def close(self, *args):
        '''Close the window'''
        self.hide()
        self.save()
        self.destroy()
        self.controller.preference_open = False

    def save(self):
        ''' Call code to save the preferences'''
        for page in self.page_dict:
                page.save()

    def _on_row_activated(self,treeview):
        # Get information about the row that has been selected
        cursor, obj = treeview.get_cursor()
        self.showPage(cursor[0])

    def showPage(self, index):
        self.notebook.set_current_page(index)
        self.current_page = index

        
class GeneralPage(gtk.VBox):
    ''' This represents the General page. '''

    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        ''' VBox Properties '''
        self.config = controller.config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10) #10

        ''' LABELS FOR THE SECTIONS '''
        ### Separator Stuff ###
        # General Sep
        sepLabelGeneral = gtk.Label()
        sepLabelGeneral.set_markup(_("<b>Account Settings</b>"))
        sepLabelCList = gtk.Label()
        sepLabelCList.set_markup(_("<b>Contact List</b>"))
        # File Transfer Sep
        sepLabelTransfer = gtk.Label()
        sepLabelTransfer.set_markup(_("<b>Downloads</b>"))

        # Boxes to keep separator & label
        hBoxSep1 = gtk.HBox(homogeneous=False, spacing=4)
        hBoxSep2 = gtk.HBox(homogeneous=False, spacing=4)
        hBoxSep3 = gtk.HBox(homogeneous=False, spacing=4)

        # Pack the labels & Separators
        hBoxSep1.pack_start(sepLabelGeneral, False, True, padding=5)
        hBoxSep2.pack_start(sepLabelTransfer, False, True, padding=5)
        hBoxSep3.pack_start(sepLabelCList, False, True, padding=5)

        hBoxSep1.show_all()
        hBoxSep2.show_all()
        hBoxSep3.show_all()

        ''' ACCOUNT SETTINGS LABELS & ENTRIES '''
        labelNick = gtk.Label(_("Nickname:"))
        labelNick.set_alignment(0.00,0.50)
        self.entryNick = gtk.Entry(max=129)
        labelPM = gtk.Label(_("Personal Message:"))
        self.entryPM = gtk.Entry(max=129)

        if self.controller.connected:
            self.controller.msn.connect('self-personal-message-changed', self.update_pm_entry)
            self.controller.msn.connect('self-nick-changed', self.update_nick_entry)

        labelStartup = gtk.Label(_('Start-up Mode:'))
        labelStartup.set_alignment(0.00, 0.50)

        ''' START UP MODE '''
        configValue = self.config.glob['startup']
        self.startup = gtk.combo_box_new_text()
        self.startup.append_text(_('Normal'))
        if not self.config.glob['disableTrayIcon']:
            self.startup.append_text(_("Notification Icon Only"))
            self.values2 = {'default':0,'iconify':1,'minimize':2}
        else:
            if configValue == 'iconify': configValue = 'minimize'
            self.values2 = {'default':0,'minimize':1}
        self.startup.append_text(_("Minimized"))
        self.values1 = {_('Normal'):'default',_("Notification Icon Only"):'iconify',_("Minimized"):'minimize'}
        self.startup.set_active(self.values2[configValue])
        self.startup.connect("changed", self.save)

        vbGLabel = gtk.VBox(homogeneous=False, spacing=5)
        vbGLabel.pack_start(labelNick, True,True)
        vbGLabel.pack_start(labelPM, True, True)
        vbGLabel.pack_start(labelStartup, True, True)
        vbGLabel.show_all()

        vbGEntry = gtk.VBox(homogeneous=False, spacing=5)
        vbGEntry.pack_start(self.entryNick, True,True)
        vbGEntry.pack_start(self.entryPM, True,True)
        vbGEntry.pack_start(self.startup, True, True)
        vbGEntry.show_all()

        ''' PACK THE ACCOUNT SETTINGS STUFF '''
        # Create a HBox
        hbox1 = gtk.HBox(homogeneous=False, spacing=SPACING)

        # I can never bloody remember what the parameters mean in the pack_start stuff...
        # pack_start(child, expand=True, fill=True, padding=0)
        hbox1.pack_start(vbGLabel,False,True) # False, false
        hbox1.pack_start(vbGEntry, True, True)
        hbox1.show_all()

        ''' BUSY CHECK BOX '''
        checkBusy = gtk.CheckButton(_('_Do not disturb when status is Busy.'))
        vboxGeneral = gtk.VBox(homogeneous=False, spacing=5)
        vboxGeneral.pack_start(hbox1, False, True)
        vboxGeneral.pack_start(checkBusy, False, True)
        vboxGeneral.show_all()

        ''' FILE TRANSFERS '''
        # Checkbox for sorting transfers into users folders
        checkFT = gtk.CheckButton(_('Sort received _files by sender'))

        # Dialog that the directory button will display
        self.pathChooser = gtk.FileChooserDialog(
            title=_('Choose a Directory'),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK)
            )
        
        # Button to chose directory
        targetbutton = gtk.FileChooserButton(self.pathChooser)

        # Label for the combo box
        target = gtk.Label(_('_Save files to:'))
        target.set_alignment(0.0, 0.5)
        target.set_use_underline(True)
        
        # Position the label & combo box in this.
        targetHBox = gtk.HBox(homogeneous=False, spacing=5)
        targetHBox.pack_start(target, False, False)
        targetHBox.pack_start(targetbutton, True, True)
        targetHBox.show_all()
        
        vboxFT = gtk.VBox(homogeneous=False, spacing=5) #hmg True, spc 4
        vboxFT.pack_start(checkFT, False, False)
        vboxFT.pack_start(targetHBox, False, True)
        vboxFT.show_all()
        
        ''' CONTACT LIST '''
        
        vBoxCL = gtk.VBox(homogeneous=False, spacing=5)
        # Create a HBox to put two radio buttons side by side
        hbCLSize = gtk.HBox(homogeneous=False, spacing=4)
        # Get the icon size from the settings
        # Create Radio Button controls
        rbCLLarge = gtk.RadioButton()
        rbCLSmall = gtk.RadioButton(group=rbCLLarge)

        #fill user values or disable widgets
        if self.controller.connected:
            self.entryNick.set_text(self.controller.msn.nick.replace('\n', ' '))
            self.entryPM.set_text(self.controller.msn.personalMessage.replace('\n', ' '))
            checkBusy.set_active(self.config.user['dontDisturbOnBusy'])
            checkBusy.connect('toggled', self.onToggled, 'dontDisturbOnBusy')
            setattr(self, 'dontDisturbOnBusy', checkBusy)
            checkFT.set_active(self.config.user['receivedFilesSortedByUser'])
            checkFT.connect('toggled', self.onToggled, 'receivedFilesSortedByUser')
            setattr(self, 'receivedFilesSortedByUser', checkFT)
            targetbutton.set_current_folder(os.path.expanduser(self.config.user['receivedFilesDir']))
            # Set attribute
            rbCLSmall.connect('toggled', self.onToggled, 'smallIcons')
            iconSize = self.config.user['smallIcons']
            # Set their default active states
            rbCLLarge.set_active(not iconSize)
            rbCLSmall.set_active(iconSize)
        else:
            self.entryNick.set_sensitive(False)
            self.entryPM.set_sensitive(False)
            checkBusy.set_sensitive(False)
            checkFT.set_sensitive(False)
            targetbutton.set_sensitive(False)
            rbCLLarge.set_sensitive(False)
            rbCLSmall.set_sensitive(False)
        
        smIc = paths.DEFAULT_THEME_PATH + 'icon16.png'
        lgIc = paths.DEFAULT_THEME_PATH + 'icon32.png'
        

        #pixSmall = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 16, 16)
        imgSmall = gtk.Image()
        imgLarge = gtk.Image()
        
        imgSmall.set_from_file(smIc)
        imgLarge.set_from_file(lgIc)

        imgSmall.show()
        imgLarge.show()
        
        rbCLLarge.set_image(imgLarge)
        rbCLSmall.set_image(imgSmall)
        
        # Tool tips for the icons
        ttLarge = gtk.Tooltip()
        ttSmall = gtk.Tooltip()

        rbCLLarge.set_tooltip_text(_('Large Icon'))
        rbCLSmall.set_tooltip_text(_('Small Icon'))

        
        # Add to self
        self.list_large = rbCLLarge
        self.list_small = rbCLSmall
        
        # Label for the contact list icon sizes
        lbCL = gtk.Label(_('Icon size:'))
        
        hbCLSize.pack_start(lbCL, False, True)
        hbCLSize.pack_start(rbCLLarge, False, True, padding=20)
        hbCLSize.pack_start(rbCLSmall, False, True, padding=20)
        hbCLSize.show_all()
        vBoxCL.pack_start(hbCLSize, True, True)
        
        vBoxCL.show_all()
        
        alignGeneral = gtk.Alignment(xalign=XALIGN, xscale=XSCALE)
        alignGeneral.set_padding(0,0,20,0)
        alignGeneral.add(vboxGeneral)
        
        alignFT = gtk.Alignment(xalign=XALIGN, xscale=XSCALE)
        alignFT.set_padding(0,0,20,0)
        alignFT.add(vboxFT)
        
        alignCL = gtk.Alignment(xalign=XALIGN, xscale=XSCALE)
        alignCL.set_padding(0,0,20,0)
        alignCL.add(vBoxCL)
        
        
        ''' PACK EVERYTHING UP '''
        # Ok, so this seems to work nicely for the vertical spacing
        self.pack_start(hBoxSep1, False, True, padding=5)
        self.pack_start(alignGeneral, False, True) # hbox1
        
        self.pack_start(hBoxSep3, False, True, padding=5)
        self.pack_start(alignCL, False, True)
        
        self.pack_start(hBoxSep2, False, True, padding=5)
        self.pack_start(alignFT, False, True)

        self.show_all()

    def update_nick_entry(self, msnp, oldNick, newNick):
        self.entryNick.set_text(newNick)

    def update_pm_entry(self, msnp, user, pm):
        self.entryPM.set_text(pm)
        
    def onToggled(self, radio, option):

        self.config.user[option] = radio.get_active()
    
    def save(self, widget=None):
        ''' general '''
        if self.controller.connected:
            self.controller.contacts.set_nick(self.entryNick.get_text())
            self.controller.contacts.set_message(self.entryPM.get_text())
            self.config.user['smallIcons'] = self.list_small.get_active()
            self.config.user['receivedFilesDir'] = self.pathChooser.get_filename()
        startup = self.startup.get_active_text()
        self.config.glob['startup'] = self.values1[startup]

class ThemePage(gtk.VBox):
    ''' This represents the Theme page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10)
        self.clm = self.controller.conversationLayoutManager
        self.installNewText = _('Install new...')
        
        ''' Section Labels '''
        lbTab = gtk.Label()
        lbTab.set_markup(_('<b>Themes</b>'))
        lbConv = gtk.Label()
        lbConv.set_markup(_('Conversation Theme:'))
        lbIcons = gtk.Label()
        lbIcons.set_markup(_('Icon Theme:'))
        lbSmilies = gtk.Label()
        lbSmilies.set_markup(_('Smilies:'))
        lbColours = gtk.Label()
        lbColours.set_markup(_('<b>Colour Scheme</b>'))

        hbTabLabel = gtk.HBox()
        hbConvLabel = gtk.HBox()
        hbIconsLabel = gtk.HBox()
        hbSmiliesLabel = gtk.HBox()
        hbColoursLabel = gtk.HBox()
        
        hbTabLabel.pack_start(lbTab, False, True, padding=5)
        hbConvLabel.pack_start(lbConv, False, True, padding=20)
        hbIconsLabel.pack_start(lbIcons, False, True, padding=20)
        hbSmiliesLabel.pack_start(lbSmilies, False, True, padding=20)
        hbColoursLabel.pack_start(lbColours, False, True, padding=5)

        ''' CONVERSATION LAYOUT WIDGETS '''
        currentTheme = self.config.user['conversationLayout']
        layoutChooser = gtk.combo_box_new_text()
        themes = self.clm.listAvailableThemes()
        count = 0
        index=None
        self.convDefaultIndex=None
        # add themes to the combo and saves the index of the current theme
        for theme in themes:
            layoutChooser.append_text(theme)
            if theme == currentTheme:
                index = count
            if theme == "default":
                self.convDefaultIndex = count
            count += 1

        layoutChooser.append_text(self.installNewText)

        # set the active theme of the combo
        if not index == None:
            layoutChooser.set_active(index)
        else:
            layoutChooser.set_active(self.convDefaultIndex)
        layoutChooser.connect('changed',self.setLayout)

        ''' CONVERSATION PREVIEW '''
        self.conv_theme = self.preview()
        self.conv_theme.set_left_margin(5)
        scroll = gtk.ScrolledWindow()
        scroll.add(self.conv_theme)
        scroll.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_OUT)
        hbScroll = gtk.HBox()
        hbScroll.pack_start(scroll, True, True, padding=5)
        
        self.disableFormat = gtk.CheckButton(_('Disable text formatting'))
        self.disableFormat.set_active(self.config.user['disableFormat'])
        self.disableFormat.connect("clicked", self.onDisableFormatClicked)

        ''' ICON THEME WIDGETS '''
        currentTheme = self.config.user['theme']
        iconThemesList = gtk.ListStore(str, gtk.gdk.Pixbuf)
        iconChooser = gtk.ComboBox(iconThemesList)
        themes = self.config.getThemes()
        count = 0
        index=None
        self.iconsDefaultIndex=None
        for theme in themes:
            iconThemesList.append([theme,self.getThemeSample(theme)])
            if theme == currentTheme:
                index = count
            if theme == "default":
                self.iconsDefaultIndex = count
            count += 1

        iconThemesList.append([self.installNewText,None])

        # set the active theme of the combo
        if not index == None:
            iconChooser.set_active(index)
        else:
            iconChooser.set_active(self.iconsDefaultIndex)


        cellRenderer = gtk.CellRendererText()
        sampleImage = gtk.CellRendererPixbuf()
        sampleImage.set_property('xalign', 1.0)
        iconChooser.pack_start(cellRenderer, False)
        iconChooser.add_attribute(cellRenderer, 'markup', 0)
        iconChooser.pack_start(sampleImage, True)
        iconChooser.add_attribute(sampleImage, 'pixbuf', 1)
        iconChooser.connect('changed',self.setIconTheme)


        ''' SMILIES WIDGETS '''
        currentTheme = self.config.user['smilieTheme']
        smiliesThemesList = gtk.ListStore(str, gtk.gdk.Pixbuf)
        smiliesChooser = gtk.ComboBox(smiliesThemesList)
        themes = self.config.getSmilieThemes()
        count = 0
        index=None
        self.smilieDefaultIndex=None
        for theme in themes:
            smiliesThemesList.append([theme,self.getSmilieSample(theme)])
            if theme == currentTheme:
                index = count
            if theme == "default":
                self.smilieDefaultIndex = count
            count += 1

        smiliesThemesList.append([self.installNewText,None])

        # set the active theme of the combo
        if not index == None:
            smiliesChooser.set_active(index)
        else:
            smiliesChooser.set_active(self.smilieDefaultIndex)

        smiliesCellRenderer = gtk.CellRendererText()
        smiliesSampleImage = gtk.CellRendererPixbuf()
        smiliesSampleImage.set_property('xalign', 1.0)
        smiliesChooser.pack_start(smiliesCellRenderer, False)
        smiliesChooser.add_attribute(smiliesCellRenderer, 'markup', 0)
        smiliesChooser.pack_start(smiliesSampleImage, True)
        smiliesChooser.add_attribute(smiliesSampleImage, 'pixbuf', 1)
        smiliesChooser.connect('changed',self.setSmilieTheme)

        ''' COLOUR SCHEME WIDGETS '''
        hbColours = gtk.HBox(homogeneous=True, spacing=0)

        lbColourMsgWaiting = gtk.Label(_('New Message'))
        lbColourTyping = gtk.Label(_('Contact Typing'))
        lbColourPM = gtk.Label(_('Personal Message'))

        lbColourMsgWaiting.set_alignment(0.50, 0.50)
        lbColourTyping.set_alignment(0.50, 0.50)
        lbColourPM.set_alignment(0.50, 0.50)

        self.btnWait = CreateColourButton(self.config,'messageWaitingColor')
        alignBtnWait = gtk.Alignment(0.5,0.5,0,0)
        alignBtnWait.add(self.btnWait)
        self.btnType = CreateColourButton(self.config, 'typingColor')
        alignBtnType = gtk.Alignment(0.5,0.5,0,0)
        alignBtnType.add(self.btnType)
        self.btnPM = CreateColourButton(self.config, 'personalMessageColor')
        alignBtnPM = gtk.Alignment(0.5,0.5,0,0)
        alignBtnPM.add(self.btnPM)
        restoreButton = gtk.Button(stock = gtk.STOCK_CLEAR)
        restoreButton.connect('clicked', self.restoreColors)

        mwColumn = gtk.VBox()
        mwColumn.pack_start(lbColourMsgWaiting, False, False)
        mwColumn.pack_start(alignBtnWait, False, False)

        ctColumn = gtk.VBox()
        ctColumn.pack_start(lbColourTyping, False,False)
        ctColumn.pack_start(alignBtnType, False, False)

        pmColumn = gtk.VBox()
        pmColumn.pack_start(lbColourPM, False,False)
        pmColumn.pack_start(alignBtnPM, False, False)

        hbColours.pack_start(mwColumn, True, True)
        hbColours.pack_start(ctColumn, True, True)
        hbColours.pack_start(pmColumn, True, True)

        hbColorAndRestore = gtk.HBox(homogeneous=False)
        hbColorAndRestore.pack_start(hbColours, True, True)
        hbColorAndRestore.pack_start(restoreButton, False, False)

        ''' PACK LABELS ANS COMBOS TO BE ALIGNED '''
        labels = gtk.VBox(homogeneous=True, spacing=4)
        labels.pack_start(hbIconsLabel, False, False)
        labels.pack_start(hbSmiliesLabel, False, False)
        labels.pack_start(hbConvLabel, False, False)

        hbIconChooser = gtk.HBox(homogeneous=False, spacing=5)
        hbSmilieChooser = gtk.HBox(homogeneous=False, spacing=5)
        hbConvChooser = gtk.HBox(homogeneous=False, spacing=5)
        hbIconChooser.pack_start(iconChooser, True, True, padding=12)
        hbSmilieChooser.pack_start(smiliesChooser, True, True, padding=12)
        hbConvChooser.pack_start(layoutChooser, True, True, padding=12)

        combos = gtk.VBox(homogeneous=True, spacing=4)
        combos.pack_start(hbIconChooser, False, True)
        combos.pack_start(hbSmilieChooser, False, True)
        combos.pack_start(hbConvChooser, False, True)

        hbThemes = gtk.HBox(homogeneous=False, spacing=0)
        hbThemes.pack_start(labels, False, False)
        hbThemes.pack_start(combos, True, True)
        
        ''' PACK EVERYTHING HERE FOR THE MAIN VBOX '''
        self.pack_start(hbTabLabel,False, True, padding=5)
        self.pack_start(hbThemes, False, False)
        self.pack_start(self.disableFormat, False)
        self.pack_start(hbScroll, True, True)
        self.pack_start(hbColoursLabel, False, True)
        self.pack_start(hbColorAndRestore, False, True)

        self.show_all()

    def restoreColors(self, retoreButton):
        ''' Restore default colors '''
        self.btnWait.set_color(gtk.gdk.color_parse(self.config.user.getDefault('messageWaitingColor')))
        self.btnType.set_color(gtk.gdk.color_parse(self.config.user.getDefault('typingColor')))
        self.btnPM.set_color(gtk.gdk.color_parse(self.config.user.getDefault('personalMessageColor')))
        self.btnWait.emit('color-set')
        self.btnType.emit('color-set')
        self.btnPM.emit('color-set')

    ''' THEME SELECTED CALLBACKS '''
    def setLayout(self, combo):
        ''' set the layout selected in the combobox '''
        active = combo.get_active_text()
        if active == self.installNewText:
            installed = self.installTheme(gtk.FILE_CHOOSER_ACTION_OPEN,self.convInstaller,_("Select theme file"))
            if not installed == "":
                active = installed
                combo.prepend_text(active)
                self.convDefaultIndex += 1
                combo.set_active(0)
            else:
                combo.set_active(self.convDefaultIndex)
                active = "default"
        self.clm.load(active)
        self.conv_theme.set_buffer(self.preview().get_buffer())
        self.config.user['conversationLayout'] = active

    def setIconTheme(self, combo):
        active = combo.get_active_text()
        if active == self.installNewText:
            installed = self.installTheme(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,self.iconInstaller)
            if not installed == "":
                active = installed
                combo.get_model().prepend([active,self.getThemeSample(active)])
                self.iconsDefaultIndex += 1
                combo.set_active(0)
            else:
                combo.set_active(self.iconsDefaultIndex)
                active = "default"
        self.controller.theme.setTheme(active)
        self.config.user['theme'] = active

    def setSmilieTheme(self, combo):
        active = combo.get_active_text()
        if active == self.installNewText:
            installed = self.installTheme(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,self.smilieInstaller)
            if not installed == "":
                active = installed
                combo.get_model().prepend([active,self.getSmilieSample(active)])
                self.smilieDefaultIndex += 1
                combo.set_active(0)
            else:
                combo.set_active(self.smilieDefaultIndex)
                active = "default"
        self.controller.theme.smilies.setTheme(active)
        self.config.user['smilieTheme'] = active
        return

    ''' THEME INSTALLERS '''
    def installTheme(self, chooserAction, installFunction, chooserTitle=_("Select theme's folder"), validateFunction=None):
        ''' chooserAction is a gtk.FILE_CHOOSER_ACTION specifying file or folder action '''
        fileChooser = gtk.FileChooserDialog(title=chooserTitle, action=chooserAction,\
                                                             buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,\
                                                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fileChooser.set_select_multiple(False)
        response = fileChooser.run()
        if response == gtk.RESPONSE_ACCEPT:
            selectedPath = fileChooser.get_filename()
            themeName = installFunction(selectedPath)
            fileChooser.destroy()
            return themeName
        else:
            fileChooser.destroy()
            return ""

    def convInstaller(self, path):
        ''' validates a theme and copy the file to the corresponding folder '''
        selectedFile = open(path)
        themeName = "unknownName"
        #read theme name
        for line in selectedFile:
            if "name=" in line:
                themeName = line.replace("name=","").split()[0]
                break
        selectedFile.close()
        #don't repeate the name of a theme
        if themeName in self.clm.listAvailableThemes():
            print "There's already a conversation layout with the same name"
            return ""
        #create the folder and copy the file inside
        conv_path=paths.CONVTHEMES_HOME_PATH + os.sep + themeName.lower()
        os.mkdir(conv_path)
        shutil.copyfile(path,conv_path + os.sep + "theme")
        return themeName.lower()

    def iconInstaller(self, path):
        #read theme name
        themeName = path.split(os.sep)[-1]
        if themeName in self.config.getThemes():
            print "There's already an icon theme with the same name"
            return ""
        #copy folder
        theme_path=paths.THEME_HOME_PATH + os.sep + themeName.lower()
        shutil.copytree(path,theme_path)
        return themeName.lower()

    def smilieInstaller(self, path):
        #read theme name
        themeName = path.split(os.sep)[-1]
        if themeName in self.config.getThemes():
            print "There's already a smilie theme with the same name"
            return ""
        #copy folder
        theme_path=paths.SMILIES_HOME_PATH + os.sep + themeName.lower()
        shutil.copytree(path,theme_path)
        return themeName.lower()

    ''' SAMPLES '''
    def preview(self):
        htmlview = htmltextview.HtmlTextView(self.controller)
        preview = self.clm.getPreview()
        htmlview.display_html(preview)
        #little hack to delete the last empty line
        start = htmlview.get_buffer().get_end_iter()
        start.backward_chars(1)
        end = htmlview.get_buffer().get_end_iter()
        htmlview.get_buffer().delete(start,end)
        return htmlview

    def getThemeSample(self, themeName):
        basetheme = Theme.BaseTheme()
        basetheme.pixbufs = {}
        basetheme.defaults = {}
        basetheme.HOME_PATH = self.controller.theme.HOME_PATH
        basetheme.SYSTEM_WIDE_PATH = self.controller.theme.SYSTEM_WIDE_PATH
        basetheme.defaultPath = self.controller.theme.defaultPath
        basetheme.setTheme(themeName)
        return basetheme.getImage('icon').scale_simple(20,20,gtk.gdk.INTERP_BILINEAR)

    def getSmilieSample(self, themeName):
        tempTheme = Theme.SmilieTheme(None, themeName)
        try:
            icon = tempTheme.getSmiley(':D').get_static_image().scale_simple(20,20,gtk.gdk.INTERP_BILINEAR)
            del tempTheme
            return icon
        except:
            pass

    def onDisableFormatClicked(self, button):
        self.config.user['disableFormat'] = self.disableFormat.get_active()
        self.conv_theme.set_buffer(self.preview().get_buffer())

    def save(self):
        return
        
        
class InterfacePage(gtk.VBox):
    ''' This represents the Interface page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10)

#        lbTitle = gtk.Label()
#        lbTitle.set_markup(_('<b>Interface</b>'))
#        hbTitleLabel = gtk.HBox()
#        hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
#        self.pack_start(hbTitleLabel, False, False, padding=5)

        self.label = gtk.Label()

        self.windowshbox = gtk.HBox()
        self.mainalign = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        posStatus = self.config.user['statusComboPos']
        self.mainWindowPreview(posStatus)

        pageOneLabel = gtk.Label()
        pageOneLabel.set_markup('<b>' + _('Layout') + '</b>')
        pageOneLabel.set_alignment(0.5, 0.0)
        self.mainalign.add(self.mainvbox)

        self.convalign = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        posAvatar = self.config.user['avatarsOnRight']
        self.convWindowPreview(posAvatar)

        pageTwoabel = gtk.Label()
        pageTwoabel.set_markup('<b>' + _('Advanced') + '</b>')
        pageTwoabel.set_alignment(0.5, 0.0)
        self.convalign.add(self.convbox1)
        self.thumbnailsHBox = gtk.HBox()
        self.thumbnailsHBox.pack_start(self.mainalign, True)
        self.thumbnailsHBox.pack_end(self.convalign, True)
        self.page_one = gtk.VBox()
        self.page_one.set_border_width(6)
        self.page_one.set_spacing(4)
        self.page_two = gtk.VBox()
        self.page_two.set_border_width(6)
        self.page_two.set_spacing(4)
        self.page_one.pack_start(self.thumbnailsHBox, False)

        notebook = gtk.Notebook()
        notebook.append_page(self.page_one, pageOneLabel)
        notebook.append_page(self.page_two, pageTwoabel)
        notebook.set_tab_pos(gtk.POS_TOP)
        
        self.pack_start(notebook, True, True)

        combosBox = gtk.HBox(False, 10)
        labelSide = gtk.VBox(homogeneous=True)
        label = gtk.Label(_('Avatars position'))
        label.set_alignment(0.0, 0.5)
        labelSide.pack_start(label, False, False)
        label1 = gtk.Label(_('Status selector position...'))
        label1.set_alignment(0.0, 0.5)
        labelSide.pack_start(label1, True, True)

        combosBox.pack_start(labelSide, False, False)

        comboSide = gtk.VBox(homogeneous=True)
        self.avatarsOnRight = gtk.combo_box_new_text()
        self.avatarsOnRight.append_text(_('Right side of conversation window'))
        self.avatarsOnRight.append_text(_('Left side of conversation window'))
        self.avatarsvalues = {_('Right side of conversation window'):True,_('Left side of conversation window'):False}
        self.avatarsvalues2 = {True:0,False:1}
        self.avatarsOnRight.set_active(self.avatarsvalues2[posAvatar])
        self.avatarsOnRight.connect('changed', self.on_toggle_avatar_side)

        comboSide.pack_start(self.avatarsOnRight, True, True)

        self.statusComboPos = gtk.combo_box_new_text()
        self.statusComboPos.append_text(_('Icon in user panel'))
        self.statusComboPos.append_text(_('Above contact list'))
        self.statusComboPos.append_text(_('Below contact list'))
#        self.comboOnTopvalues = {_('Icon in user panel'):0,_('Below contact list'):1,_('Above contact list'):2}
#        self.comboOnTopvalues2 = {False:0,True:1}
#        self.statusComboPos.set_active(self.comboOnTopvalues2[posStatus])
        self.statusComboPos.set_active(posStatus)
        self.statusComboPos.connect('changed', self.on_toggle_status_box)

        comboSide.pack_start(self.statusComboPos, True, True)

        combosBox.pack_start(comboSide, True, True)
        self.page_one.pack_start(combosBox, False, False)
        label = gtk.Label(_('Conversation toolbar button:'))
        toolbarHBox = gtk.HBox()
        toolbarHBox.set_spacing(10)
        toolbarHBox.pack_start(label, False, False)
        toolbarHBox.pack_start(ToggleToolbar(self.config, self.controller))
        self.page_one.pack_start(toolbarHBox, False, False)

        self.checks = []
        mkcheck(self.page_two, 'windows', _('Use multiple _windows'), self)
        mkcheck(self.page_two, 'parseSmilies', _('Display smilies'), self)
        mkcheck(self.page_two, 'showTabCloseButton', \
            _('Show close button on _each tab'), self)
        mkcheck(self.page_two, 'avatarsInUserList', \
            _('Show _avatars in user list'), self)
        mkcheck(self.page_two, 'avatarsInTaskbar', \
            _('Show avatars in task_bar'), self)
        mkcheck(self.page_two, 'hideNewWindow', \
            _('Hide new conversation window automatically'), self)
        mkcheck(self.page_two, 'showMailTyping', \
            _('Show ma_il on "is typing" message'), self)
        mkcheck(self.page_two, 'disableEsc', \
            _('Don\'t _close conversation by pressing ESC'), self)
        mkcheck(self.page_two, 'preventClosingTime', \
            _('Prevent closing window when a new message arrives'), self)
        mkcheck(self.page_two, 'showLastMessageReceivedAt', \
            _('Show "last message received at.." in conversation status bar'), self)      

    def addPreview(self, box, key, desc, size, packing=False, align=None, defsize=-1):
        widget = WidgetToggleBox(self.config, key, desc, self.label)
        widget.show()
        if type(box) == gtk.HBox:
            widget.set_size_request(size, defsize)
        else:
            widget.set_size_request(defsize, size)
        if align:
            align.add(widget)
            widget = align
        box.pack_start(widget, packing)

    def mainWindowPreview(self, pos):
        self.mainvbox = gtk.VBox()
        self.mainvbox.set_size_request(60, -1)
        self.addPreview(self.mainvbox, 'showMenu', _('Show _menu bar'), 10)
        self.addPreview(self.mainvbox, 'showUserPanel', _('Show _user panel'), 20)
        if pos==0:
            self.addPreview(self.mainvbox, 'showSearchEntry', _('Show _search entry'), 10)
            self.addPreview(self.mainvbox, None, None, 90)
        elif pos==1:
            self.addPreview(self.mainvbox, 'showStatusCombo', _('Always show _search entry'), 10)
            self.addPreview(self.mainvbox, 'showSearchEntry', _('Show _search entry'), 10)
            self.addPreview(self.mainvbox, None, None, 80)
        else:
            self.addPreview(self.mainvbox, 'showSearchEntry', _('Always show _search entry'), 10)
            self.addPreview(self.mainvbox, None, None, 80)
            self.addPreview(self.mainvbox, 'showStatusCombo', _('Show status _combo'), 10)

    def convWindowPreview(self, pos):
        self.convbox1 = gtk.VBox()
        self.convbox1.set_size_request(100, -1)
        self.addPreview(self.convbox1, 'showMenubar', _('Show _menu bar'), 10)
        self.addPreview(self.convbox1, 'showHeader', _('Show conversation _header'), 20)
        self.convbox2 = gtk.HBox()
        self.convbox3 = gtk.VBox()
        self.convbox4 = gtk.HBox()
        self.convbox5 = gtk.VBox()
        self.addPreview(self.convbox3, None, None, 50)
        self.convbox3.pack_start(self.convbox4)
        self.convbox4.pack_start(self.convbox5)
        self.convbox4.set_size_request(-1, 30)
        self.addPreview(self.convbox5, 'showToolbar', _('Show conversation _toolbar'), 10)
        self.addPreview(self.convbox5, None, None, -1, packing=True)
        self.addPreview(self.convbox4, 'showSendButton', _('S_how a Send button'), 15,
            align=gtk.Alignment(0.0, 0.5, 0.0, 0.0), defsize=10)
        self.addPreview(self.convbox3, 'showStatusBar', _('Show st_atusbar'), 10)
        if pos:
            self.convbox2.pack_start(self.convbox3)
            self.addPreview(self.convbox2, 'showAvatars', _('Show a_vatars'), 30)
        else:
            self.addPreview(self.convbox2, 'showAvatars', _('Show a_vatars'), 30)
            self.convbox2.pack_start(self.convbox3)
        self.convbox1.pack_start(self.convbox2)
            
    def on_toggle_status_box(self, combo):
        self.controller.mainWindow.toggle_status_box(combo) #move main window status selector
        self.thumbnailsHBox.remove(self.mainalign) #remove
        self.mainvbox.destroy() #delete
        self.mainWindowPreview(combo.get_active()) #create new
        self.mainvbox.show()
        self.mainalign.add(self.mainvbox) #add again
        self.thumbnailsHBox.pack_start(self.mainalign, True)

    def on_toggle_avatar_side(self, combo):
        self.thumbnailsHBox.remove(self.convalign) #remove
        self.convbox1.destroy() #delete
        self.convbox2.destroy() #delete
        self.convbox3.destroy() #delete
        self.convbox4.destroy() #delete
        self.convbox5.destroy() #delete
        self.convWindowPreview(self.avatarsvalues[combo.get_active_text()]) #create new
        self.convbox1.show_all()
        self.convalign.add(self.convbox1) #add again
        self.thumbnailsHBox.pack_end(self.convalign, True)

    def onToggled(self, radio, option):
        self.config.user[option] = radio.get_active()
        
#    def saveavatars(self, widget=None):
#        avatarsOnRight = self.avatarsOnRight.get_active_text()
#        self.config.user['avatarsOnRight'] = self.avatarsvalues[avatarsOnRight]
#    
    def savestatus(self, combo):
        self.config.user['statusComboPos'] = combo.get_active()
    
    def save(self, *args):
        avatarsOnRight = self.avatarsOnRight.get_active_text()
        self.config.user['avatarsOnRight'] = self.avatarsvalues[avatarsOnRight]
#        statusOnTop = self.statusComboPos.get_active_text()
        self.config.user['statusComboPos'] = self.statusComboPos.get_active()

class ToggleToolbar(gtk.HBox):
    ''' This represents the fake window toolbar to enable or disable buttons '''
    def __init__(self, config, controller):
        gtk.HBox.__init__(self)
        self.config = config
        self.controller = controller

        self.fontFace = gtk.ToggleButton()
        fontfaceicon = self.controller.theme.getImage('fontface')
        if fontfaceicon != None:
            self.fontFace.set_image(gtk.image_new_from_pixbuf(fontfaceicon))
        else:
            self.fontFace.set_image(gtk.image_new_from_stock(gtk.STOCK_SELECT_FONT,gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.fontFace.set_active(not self.config.user['toolFontType'])
        self.fontFace.set_tooltip_text(_('Font selection'))

        self.fontFace.connect('clicked', self.on_toggled, 'toolFontType')
        self.pack_start(self.fontFace, False, False)

        #font color
        self.fontColor = gtk.ToggleButton()
        fontcoloricon = self.controller.theme.getImage('fontcolor')
        if fontcoloricon != None:
            self.fontColor.set_image(gtk.image_new_from_pixbuf(fontcoloricon))
        else:
            self.fontColor.set_image(gtk.image_new_from_stock(gtk.STOCK_SELECT_COLOR,gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.fontColor.set_active(not self.config.user['toolFontColor'])
        self.fontColor.set_tooltip_text(_('Font color selection'))

        self.fontColor.connect('clicked', self.on_toggled, 'toolFontColor')
        self.pack_start(self.fontColor, False, False)

        #font style button
        self.fontStyleButton = gtk.ToggleButton()
        fontStyleIcon = self.controller.theme.getImage('fontstyle')
        if fontStyleIcon != None:
            self.fontStyleButton.set_image(gtk.image_new_from_pixbuf(fontStyleIcon))
        else: 
            self.fontStyleButton.set_image(gtk.image_new_from_stock(gtk.STOCK_BOLD,gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.fontStyleButton.set_active(not self.config.user['toolFontStyle'])
        self.fontStyleButton.set_tooltip_text(_('Font styles'))

        self.fontStyleButton.connect('clicked', self.on_toggled, 'toolFontStyle')
        self.pack_start(self.fontStyleButton, False, False)

        self.pack_start(gtk.SeparatorToolItem(), False, False)

        #smilie button, fixed for mac4lin
        smilieicon = gtk.image_new_from_pixbuf(self.controller.theme.getImage('smilie'))
        self.smilieButton = gtk.ToggleButton()
        self.smilieButton.set_image(smilieicon)
        self.smilieButton.set_active(not self.config.user['toolSmilies'])
        self.smilieButton.set_tooltip_text(_('Insert a smilie'))

        self.smilieButton.connect('clicked', self.on_toggled, 'toolSmilies')
        self.pack_start(self.smilieButton, False, False)

        #nudge button, fixed for mac4lin
        nudgeicon = gtk.image_new_from_pixbuf(self.controller.theme.getImage('nudge'))
        self.nudgeButton = gtk.ToggleButton()
        self.nudgeButton.set_image(nudgeicon)
        self.nudgeButton.set_active(not self.config.user['toolNudge'])
        self.nudgeButton.set_tooltip_text(_('Send nudge'))

        self.nudgeButton.connect('clicked', self.on_toggled, 'toolNudge')
        self.pack_start(self.nudgeButton, False, False)

        self.pack_start(gtk.SeparatorToolItem(), False, False)

        #invite button
        self.inviteButton = gtk.ToggleButton()
        inviteIcon = self.controller.theme.getImage('invite')
        if inviteIcon != None:
            self.inviteButton.set_image(gtk.image_new_from_pixbuf(inviteIcon))
        else:
            self.inviteButton.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.inviteButton.set_active(not self.config.user['toolInvite'])
        self.inviteButton.set_tooltip_text(_('Invite a friend to the conversation'))

        self.inviteButton.connect('clicked', self.on_toggled, 'toolInvite')
        self.pack_start(self.inviteButton, False, False)


        #send a file
        self.sendfileButton = gtk.ToggleButton()
        sendIcon = self.controller.theme.getImage('sendfile')
        if sendIcon != None:
            self.sendfileButton.set_image(gtk.image_new_from_pixbuf(sendIcon))
        else:
            self.sendfileButton.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_TOP,gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.sendfileButton.set_active(not self.config.user['toolSendFile'])
        self.sendfileButton.set_tooltip_text(_('Send a file'))

        self.sendfileButton.connect('clicked', self.on_toggled, 'toolSendFile')
        self.pack_start(self.sendfileButton, False, False)


        # webcam send hax
        camicon = gtk.image_new_from_pixbuf(self.controller.theme.getImage('cam'))
        self.sendWebcamButton = gtk.ToggleButton()
        self.sendWebcamButton.set_image(camicon)
        self.sendWebcamButton.set_tooltip_text(_('Send your Webcam'))
        self.sendWebcamButton.set_active(not self.config.user['toolWebcam'])

        self.sendWebcamButton.connect('clicked', self.on_toggled, 'toolWebcam')
        self.pack_start(self.sendWebcamButton, False, False)

        self.pack_start(gtk.SeparatorToolItem(), False, False)

        #clear conversation toolbar button
        self.clearButton = gtk.ToggleButton()
        clearIcon = self.controller.theme.getImage('clear')
        if clearIcon != None:
            self.clearButton.set_image(gtk.image_new_from_pixbuf(clearIcon))
        else:
            self.clearButton.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR,gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.clearButton.set_active(not self.config.user['toolClear'])
        self.clearButton.set_tooltip_text(_('Clear conversation'))

        self.clearButton.connect('clicked', self.on_toggled, 'toolClear')
        self.pack_start(self.clearButton, False, False)

    def on_toggled(self, button, conf):
        self.config.user[conf] = not button.get_active()

class PrivacyPage(gtk.VBox):
    ''' This represents the Privacy page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10)

        '''Constructor'''

        gtk.VBox.__init__(self)

        self.controller = controller
        
        ##Draw the statusBar
        eventBox = gtk.EventBox()
        box = gtk.HBox(False, 0)
        otherBox = gtk.VBox(False, 0) #False, 0
        box.set_size_request(40, 40) #40,40
        eventBox.add(box)
        eventBox.modify_bg(gtk.STATE_NORMAL, self.controller.tooltipColor)
        markup = '<span foreground="black"> %s </span>'
        firstLabel = gtk.Label()
        text = _('Yellow contacts are not in your contact list.')
        firstLabel.set_markup(markup % text)
        secondLabel = gtk.Label()
        text = _('Purple contacts don\'t have you in their contact list.')
        secondLabel.set_markup(markup % text)
        image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_LARGE_TOOLBAR)
        box.pack_start(image, False, False, 10) # False, False, 10
        otherBox.pack_start(firstLabel, True, True, 2)
        otherBox.pack_start(secondLabel, False, True, 2)
        box.pack_start(otherBox, False, False, 50)  #10
        self.pack_start(eventBox, False, False, 0) #5

        hbox = gtk.HBox()
        self.add(hbox)
        
        scroll1 = gtk.ScrolledWindow()
        scroll1.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll1.set_shadow_type(gtk.SHADOW_OUT)
        hbox.add(scroll1)
        self.model1 = gtk.ListStore(gobject.TYPE_STRING)
        self.view1 = gtk.TreeView(self.model1)
        self.view1.connect('button-press-event', self.right_click1)
        self.view1.connect("key-press-event", self.onKeyPressOfView1)
        self.view1.set_border_width(1)
        scroll1.add(self.view1)
        render1 = gtk.CellRendererText()
        col1 = gtk.TreeViewColumn(_('Allow list:'), render1, text=0)
        col1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col1.set_cell_data_func(render1, self.func)
        self.view1.append_column(col1)

        vbox = gtk.VBox()
        button1 = gtk.Button()
        image1 = gtk.image_new_from_stock(gtk.STOCK_GO_BACK, gtk.ICON_SIZE_BUTTON)
        button1.set_image(image1)
        button1.connect('clicked', self.unblock)
        button2 = gtk.Button()
        image2 = gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_BUTTON)
        button2.set_image(image2)
        button2.connect('clicked', self.block)
        vbox.pack_start(button1, True, False)
        vbox.pack_start(button2, True, False)
        hbox.pack_start(vbox, False)

        scroll2 = gtk.ScrolledWindow()
        scroll2.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll2.set_shadow_type(gtk.SHADOW_OUT)
        hbox.add(scroll2)
        self.model2 = gtk.ListStore(gobject.TYPE_STRING)
        self.view2 = gtk.TreeView(self.model2)
        self.view2.connect('button-press-event', self.right_click2)
        self.view2.connect("key-press-event", self.onKeyPressOfView2)
        scroll2.add(self.view2)
        render2 = gtk.CellRendererText()
        col2 = gtk.TreeViewColumn(_('Block list:'), render2, text=0)
        col2.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col2.set_cell_data_func(render2, self.func)
        self.view2.append_column(col2)

        for contact in self.controller.msn.contactManager.lists['Allow']:
            self.model1.append([contact])
        for contact in self.controller.msn.contactManager.lists['Block']:
            self.model2.append([contact])

      
 
    def right_click1(self, view, event):
        '''Occurs when somebody clicks in the allow list'''
        selection = self.view2.get_selection()
        selection.unselect_all()
        path = view.get_path_at_pos(int(event.x),int(event.y))
        if not path:
            selection = view.get_selection()
            selection.unselect_all()
            return
        if event.button != 3:
            return
        iter = self.model1.get_iter(path[0])
        contact = self.model1.get_value(iter, 0)

        menu = gtk.Menu()
        item1 = gtk.MenuItem(_('Add to contacts'))
        item1.connect('activate', self.addcon, contact)
        menu.append(item1)
        if contact in self.controller.msn.contactManager.contacts:
            item1.set_state(gtk.STATE_INSENSITIVE)
        item2 = gtk.MenuItem(_('Move to block list'))
        item2.connect('activate', self.block, iter)
        menu.append(item2)
        item3 = gtk.MenuItem(_('Delete'))
        item3.connect('activate', self.deleteConfirmation1, iter)
        if contact in self.controller.msn.contactManager.lists['Reverse']:
            item3.set_state(gtk.STATE_INSENSITIVE)
        menu.append(item3)
        menu.popup(None, None, None, event.button, event.time)
        menu.show_all()

    def right_click2(self, view, event):
        '''Occurs when somebody clicks in the block list'''
        selection = self.view1.get_selection()
        selection.unselect_all()
        path = view.get_path_at_pos(int(event.x),int(event.y))
        if not path:
            selection = view.get_selection()
            selection.unselect_all()
            return
        if event.button != 3:
            return
        iter = self.model2.get_iter(path[0])
        contact = self.model2.get_value(iter, 0)

        menu = gtk.Menu()
        item1 = gtk.MenuItem(_('Add to contacts'))
        item1.connect('activate', self.addcon, contact)
        menu.append(item1)
        if contact in self.controller.msn.contactManager.contacts:
            item1.set_state(gtk.STATE_INSENSITIVE)
        item2 = gtk.MenuItem(_('Move to allow list'))
        item2.connect('activate', self.unblock, iter)
        menu.append(item2)
        item3 = gtk.MenuItem(_('Delete'))
        item3.connect('activate', self.deleteConfirmation2, iter)
        if contact in self.controller.msn.contactManager.lists['Reverse']:
            item3.set_state(gtk.STATE_INSENSITIVE)
        menu.append(item3)
        menu.popup(None, None, None, event.button, event.time)
        menu.show_all()

    def addcon(self, item, contact):
      self.controller.contacts.add(contact, '')

    def delete1(self, item, iter):
      contact = self.model1.get_value(iter, 0)
      self.model1.remove(iter)
      self.controller.msn.contactManager.lists['Allow'].remove(contact)
      if self.controller.contacts.exists(contact):
            self.controller.msn.removeUser(contact)
      if contact not in self.controller.msn.contactManager.contacts:
            soap.requests.delete_role(self.controller.msn.proxy, 'Allow', contact, None, None)

    def delete2(self, item, iter):
      contact = self.model2.get_value(iter, 0)
      self.model2.remove(iter)
      self.controller.msn.contactManager.lists['Block'].remove(contact)
      if self.controller.contacts.exists(contact):
            self.controller.msn.removeUser(contact)
      if contact not in self.controller.msn.contactManager.contacts:
            soap.requests.delete_role(self.controller.msn.proxy, 'Block', contact, None, None)

    def block(self, button, iter=None):
      if not iter:
            iter = self.view1.get_selection().get_selected()[1]
            if not iter:
                 return
      contact = self.model1.get_value(iter, 0)
      self.model1.remove(iter)
      self.model2.append([contact])
      if contact in self.controller.msn.contactManager.contacts:
            self.controller.contacts.block(contact)
      else:
            self.controller.msn.blockUser(contact)

    def unblock(self, button, iter=None):
      if not iter:
            iter = self.view2.get_selection().get_selected()[1]
            if not iter:
                 return
      contact = self.model2.get_value(iter, 0)
      self.model2.remove(iter)
      self.model1.append([contact])
      if contact in self.controller.msn.contactManager.contacts:
            self.controller.contacts.unblock(contact)
      else:
            self.controller.msn.unblockUser(contact)

    def func(self, column, render, model, iter):
      contact = model.get_value(iter, 0)
      if contact not in self.controller.msn.contactManager.lists['Reverse']:
            render.set_property('background', '#FF00FF')
      elif contact not in self.controller.msn.contactManager.contacts:
            render.set_property('background', '#FFF000')
      else:
            render.set_property('background', None)

    def onKeyPressOfView1(self , widget, event):
      '''called when the user press a key'''
      if event.keyval == gtk.keysyms.Right or event.keyval == gtk.keysyms.Return:
            self.block(None)

    def onKeyPressOfView2(self , widget, event):
      '''called when the user press a key'''
      if event.keyval == gtk.keysyms.Left or event.keyval == gtk.keysyms.Return:
            self.unblock(None)

    def manageDeleteConfirmation1(self, *args):
      iter = args[1]
      if args[0] == abstract.stock.YES:
            self.delete1(None, iter)

    def deleteConfirmation1(self, item, iter):
      contactName = self.model1.get_value(iter, 0)
      message = _('Are you sure you want to delete %s from your authorized contacts?') % contactName
      dialog.yes_no(message, self.manageDeleteConfirmation1, iter)

    def manageDeleteConfirmation2(self, *args):
      iter = args[1]
      if args[0] == abstract.stock.YES:
            self.delete2(None, iter)

    def deleteConfirmation2(self, item, iter):
      contactName = self.model2.get_value(iter, 0)
      message = _('Are you sure you want to delete %s from your blocked contacts?') % contactName
      dialog.yes_no(message, self.manageDeleteConfirmation2, iter)

    def save(self):
        pass


class ConnectionPage(gtk.VBox):
    ''' This represents the Connection page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10)

        # Create a test item, like a label
        lbTitle = gtk.Label()
        lbTitle.set_markup(_('<b>Connection</b>'))
        hbTitleLabel = gtk.HBox()
        hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
        self.pack_start(hbTitleLabel, False, False, padding=5)


        self.httpMethod =  gtk.CheckButton(_('_Use HTTP method'))
        self.httpMethod.set_active(self.config.glob['httpMethod'])

        self.proxySettings = ProxySettings(self.config)
        frame = gtk.Frame(_('Proxy settings'))
        frame.set_border_width(4)
        frame.add(self.proxySettings)

        self.pack_start(self.httpMethod, False, False)

        if self.config.currentUser != '':
            self.sendKeepalive = gtk.CheckButton(_('_Keepalive opened conversations'))
            self.sendKeepalive.set_active(self.config.user['sendKeepalive'])
            self.receiveP4context = gtk.CheckButton(_('Support msn _groups friendly names (restart required)'))
            self.receiveP4context.set_active(self.config.user['receiveP4context'])
            self.pack_start(self.sendKeepalive, False, False)
            self.pack_start(self.receiveP4context, False, False)

        proxyBox = gtk.VBox(spacing=2)
        proxyBox.set_border_width(4)
        proxyBox.pack_start(frame, False, False)

        self.pack_start(proxyBox, True, True)

        self.show_all()

    def save(self):
        '''save the actual setting'''
        self.config.glob['httpMethod'] = self.httpMethod.get_active()
        if self.config.currentUser != '':
            self.config.user['sendKeepalive'] = self.sendKeepalive.get_active()
            self.config.user['receiveP4context'] = self.receiveP4context.get_active()
        self.proxySettings.save()

class ProxySettings(gtk.VBox):
    '''This class represents the panel with the proxy variables
    in the config file, used in Connection page'''

    def __init__(self, config):
        '''Constructor'''
        gtk.VBox.__init__(self)

        self.config = config

        self.set_spacing(8)
        self.set_border_width(8)

        self.useProxy = gtk.CheckButton(_('_Use proxy'))
        self.useProxy.set_active(self.config.glob['useProxy'])

        self.host = gtk.Entry()
        self.host.set_text(self.config.glob['proxyHost'])
        self.port = gtk.Entry()
        self.port.set_text(str(self.config.glob['proxyPort']))
        self.username = gtk.Entry()
        self.username.set_text(str(self.config.glob['proxyUsername']))
        self.password = gtk.Entry()
        self.password.set_text(str(self.config.glob['proxyPassword']))
        self.password.set_visibility(False)
          
        table = gtk.Table(2, 4)
        table.set_row_spacings(2)
        table.set_col_spacings(2)

        host = gtk.Label(_('_Host:'))
        host.set_alignment(0.0, 0.5)
        host.set_use_underline(True)
        host.set_mnemonic_widget(self.host)
        port = gtk.Label(_('_Port:'))
        port.set_alignment(0.0, 0.5)
        port.set_use_underline(True)
        port.set_mnemonic_widget(self.port)
        username = gtk.Label(_('_Username:'))
        username.set_alignment(0.0, 0.5)
        username.set_use_underline(True)
        username.set_mnemonic_widget(self.username)
        password = gtk.Label(_('Pass_word:'))
        password.set_alignment(0.0, 0.5)
        password.set_use_underline(True)
        password.set_mnemonic_widget(self.password)
        table.attach(host, 0, 1, 0, 1)
        table.attach(port , 0, 1, 1, 2)
        table.attach(username, 0, 1, 2, 3)
        table.attach(password , 0, 1, 3, 4)

        table.attach(self.host, 1, 2, 0, 1)
        table.attach(self.port, 1, 2, 1, 2)
        table.attach(self.username, 1, 2, 2, 3)
        table.attach(self.password, 1, 2, 3, 4)

        self.useProxyToggled(self.useProxy)
        self.useProxy.connect('toggled', self.useProxyToggled)
        self.pack_start(self.useProxy)
        self.pack_start(table)

        self.show_all()

    def save(self):
        '''save the actual setting'''
        host = self.host.get_text()
        if host.startswith('http://'):
            host = host.split('http://')[1]
        if host.find('/') != -1:
            host = host.split('/')[0]

        self.config.glob['useProxy'] = self.useProxy.get_active()
        self.config.glob['proxyHost'] = host
        self.config.glob['proxyPort'] = self.port.get_text()
        self.config.glob['proxyUsername'] = self.username.get_text()
        self.config.glob['proxyPassword'] = self.password.get_text()

    def useProxyToggled(self, check):
        '''callback for the toggled signal'''

        if self.useProxy.get_active():
            self.host.set_sensitive(True)
            self.port.set_sensitive(True)
            self.username.set_sensitive(True)
            self.password.set_sensitive(True)
        else:
            self.host.set_sensitive(False)
            self.port.set_sensitive(False)
            self.username.set_sensitive(False)
            self.password.set_sensitive(False)

class WebcamPage(gtk.VBox):
    ''' This represents the Webcam page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10)

        lbTitle = gtk.Label()
        lbTitle.set_markup(_('<b>Webcam</b>'))
        hbTitleLabel = gtk.HBox()
        hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
        self.pack_start(hbTitleLabel, False, False, padding=5)

        self.webcam = None
        self.webcamList = []
        self.movie_window = gtk.DrawingArea()
        self.movie_window.set_colormap(gtk.gdk.colormap_get_system())
        self.movie_window.set_size_request(320,240)

        self.deviceID = controller.config.user['webcamDevice']
        self.deviceIndex = 0
        self.hadj = gtk.Adjustment(controller.config.user['webcamHue'], -1.0, 1.0, 0.1)
        self.sadj = gtk.Adjustment(controller.config.user['webcamSaturation'], 0.0, 2.0, 0.1)
        self.badj = gtk.Adjustment(controller.config.user['webcamBrightness'], -1.0, 1.0, 0.1)
        self.cadj = gtk.Adjustment(controller.config.user['webcamContrast'], 0.0, 2.0, 0.1)

        devLabel = gtk.Label(_('Select webcam:'))
        devLabel.set_alignment(0.0, 0.5)
        devLabel.set_use_underline(True)
          
        devHBox = gtk.HBox()

        self.combobox = gtk.combo_box_new_text()
        self.combobox.append_text(_('No webcam'))
        self.combobox.set_active(0)
        self.get_device_list()
        self.combobox.connect('changed', self.on_set_device)

        devHBox.pack_start(self.combobox)

        self.hue = gtk.HScale(self.hadj)
        self.saturation = gtk.HScale(self.sadj)
        self.brightness = gtk.HScale(self.badj)
        self.contrast = gtk.HScale(self.cadj)

        hueLabel= gtk.Label(_('Hue:'))
        satLabel= gtk.Label(_('Saturation:'))
        conLabel= gtk.Label(_('Contrast:'))
        briLabel= gtk.Label(_('Brightness:'))

        labelsVBox = gtk.VBox(homogeneous=True)
        labelsVBox.pack_start(hueLabel)
        labelsVBox.pack_start(satLabel)
        labelsVBox.pack_start(conLabel)
        labelsVBox.pack_start(briLabel)

        slidesVBox = gtk.VBox(homogeneous=True)
        slidesVBox.pack_start(self.hue)
        slidesVBox.pack_start(self.saturation)
        slidesVBox.pack_start(self.contrast)
        slidesVBox.pack_start(self.brightness)

        controlsHBox = gtk.HBox()
        controlsHBox.set_spacing(4)
        controlsHBox.pack_start(labelsVBox, False, False)
        controlsHBox.pack_start(slidesVBox, True, True)

        self.defButton = gtk.Button(_('Restore Defaults'))
        self.defButton.connect('clicked', self.on_set_default)
        self.defButton.set_sensitive(False)

        self.hue.set_sensitive(False);
        self.saturation.set_sensitive(False);
        self.contrast.set_sensitive(False);
        self.brightness.set_sensitive(False);

        self.hadj.connect('value-changed',self.on_hue_changed)
        self.sadj.connect('value-changed',self.on_saturation_changed)
        self.badj.connect('value-changed',self.on_brightness_changed)
        self.cadj.connect('value-changed',self.on_contrast_changed)

        confVBox = gtk.VBox()
        confVBox.set_spacing(4)
        confVBox.pack_start(devLabel)
        confVBox.pack_start(devHBox, False)
        confVBox.pack_start(controlsHBox,False)
        confVBox.pack_start(self.defButton, False)

        webcamHBox = gtk.HBox()
        webcamHBox.set_spacing(4)
        webcamHBox.pack_start(self.movie_window,False,False)
        webcamHBox.pack_start(confVBox,True, True)

        self.pack_start(webcamHBox,False,False)
        #wait until the page is selected to activate the device
        self.connect('map', self.on_map)
        self.connect("unmap", self.closeWebcam)

    def get_device_list(self):
        if not HAVE_WEBCAM:
            return
        count = 1
        for device, name in WebcamDevice.list_devices():
            if name is not None:
                self.combobox.append_text(name)
                self.webcamList.append((device, name))
                if device == self.deviceID:
                    self.deviceIndex = count
                count += 1

    def on_set_device(self,button):
        self.deviceIndex = self.combobox.get_active()
        if not HAVE_WEBCAM or self.deviceIndex < 0:
            return
        if self.webcam is not None:
            self.webcam.stop()
        if not self.deviceIndex == 0:
            self.config.user['webcamDevice'] = self.webcamList[self.deviceIndex-1][0]
            self.webcam = WebcamDevice.WebcamDevice(None, self.movie_window.window.xid ,self.controller)
            self.defButton.set_sensitive(True)
            self.hue.set_sensitive(True)
            self.saturation.set_sensitive(True)
            self.brightness.set_sensitive(True)
            self.contrast.set_sensitive(True)
        else:
            #turn controls off if "No webcam" is selected
            self.defButton.set_sensitive(False)
            self.hue.set_sensitive(False)
            self.saturation.set_sensitive(False)
            self.brightness.set_sensitive(False)
            self.contrast.set_sensitive(False)

    def on_map(self,widget):
        self.combobox.set_active(self.deviceIndex)

    #when the page is unmapped (change to another page), it closes the webcam
    def closeWebcam(self,widget):
        if self.webcam is not None:
            self.webcam.stop()
        index = self.combobox.get_active()
        self.combobox.set_active(0) #to reload the right device later if mapped again
        self.deviceIndex = index

    def on_set_default(self,button):
        self.hue.set_value(0.0)
        self.saturation.set_value(1.0)
        self.contrast.set_value(1.0)
        self.brightness.set_value(0.0)

    def on_hue_changed(self,adj):
        if not HAVE_WEBCAM:
            return
        self.webcam.setHue(adj.value)

    def on_saturation_changed(self,adj):
        if not HAVE_WEBCAM:
            return
        self.webcam.setSaturation(adj.value)

    def on_brightness_changed(self,adj):
        if not HAVE_WEBCAM:
             return
        self.webcam.setBrightness(adj.value)

    def on_contrast_changed(self,adj):
        if not HAVE_WEBCAM:
            return
        self.webcam.setContrast(adj.value)

    def save(self):
        if self.webcam is not None:
            self.webcam.stop()
        if self.combobox.get_active() > 0:
            self.config.user['webcamDevice'] = self.webcamList[self.combobox.get_active()-1][0]
        self.config.user['webcamContrast'] = self.cadj.value
        self.config.user['webcamHue'] = self.hadj.value
        self.config.user['webcamBrightness'] = self.badj.value
        self.config.user['webcamSaturation'] = self.sadj.value         

class PluginsPage(gtk.VBox):
    ''' This represents the Plugins page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.pluginManager = controller.pluginManager
        self.set_spacing(SPACING)
        self.set_border_width(10)

        lbTitle = gtk.Label()
        lbTitle.set_markup(_('<b>Plugins</b>'))
        hbTitleLabel = gtk.HBox()
        hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
        self.pack_start(hbTitleLabel, False, False, padding=5)

        #plugins list
        cellRendererTextName = gtk.CellRendererText()
        cellRendererToggle = gtk.CellRendererToggle()
        cellRendererToggle.set_property( 'activatable', True )

        plugOn = gtk.TreeViewColumn(_('Active'), cellRendererToggle, active=3)
        plugOn.set_resizable( False )
        plugName = gtk.TreeViewColumn(_('Name'), cellRendererTextName, markup=0)
        plugName.add_attribute( cellRendererTextName, 'text', 0 )
        plugName.set_resizable( True )

        self.listStore = gtk.ListStore( str, str, str, bool )
        self.list = gtk.TreeView( self.listStore )
        self.list.append_column( plugOn )
        self.list.append_column( plugName )
        self.list.set_reorderable( False )
        self.list.set_headers_visible( True )
        self.list.set_rules_hint( True )

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy( gtk.POLICY_NEVER , gtk.POLICY_AUTOMATIC )
        self.scroll.set_shadow_type( gtk.SHADOW_OUT )
        self.scroll.add( self.list )

        #right side of the plugins list
        self.descTitle = gtk.Label('<b>' + _( 'Description:' ) + '</b>')
        self.descTitle.set_use_markup(True)
        self.descTitle.set_alignment(0.0,0.0)
        self.authTitle = gtk.Label('<b>' + _( 'Author:' ) + '</b>')
        self.authTitle.set_use_markup(True)
        self.authTitle.set_alignment(0.0,0.0)
        self.webTitle = gtk.Label('<b>' + _( 'Website:' ) + '</b>')
        self.webTitle.set_use_markup(True)
        self.webTitle.set_alignment(0.0,0.0)

        self.description = gtk.Label("")
        self.description.set_line_wrap(True)
        self.description.set_justify(gtk.JUSTIFY_FILL)
        self.description.set_alignment(0.0,0.0)
        self.author = gtk.Label("")
        self.author.set_line_wrap(True)
        self.author.set_alignment(0.0,0.0)
        self.web = gtk.Label("")
        self.web.set_line_wrap(True)
        self.web.set_alignment(0.0,0.0)


        #plugin related buttons
        self.bConfigure = gtk.Button(_( 'Configure' ))
        self.bConfigure.set_image(gtk.image_new_from_stock(gtk.STOCK_PROPERTIES, gtk.ICON_SIZE_BUTTON))
        self.bConfigure.set_sensitive(False)
        self.bReload = gtk.Button(_('Reload'))
        self.bReload.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON))
        self.bReload.set_sensitive(False)
        buttonsHBox = gtk.HButtonBox()
        buttonsHBox.set_spacing( 6 )
        buttonsHBox.set_layout( gtk.BUTTONBOX_SPREAD )
        buttonsHBox.pack_start(self.bConfigure)
        buttonsHBox.pack_start(self.bReload)

        rightPanelVBox = gtk.VBox(homogeneous=False)
        rightPanelVBox.set_spacing(3)
        rightPanelVBox.pack_start(self.descTitle, False, False)
        rightPanelVBox.pack_start(self.description, True, True)
        rightPanelVBox.pack_start(self.authTitle, False, False)
        rightPanelVBox.pack_start(self.author, False, False)
        rightPanelVBox.pack_start(self.webTitle, False, False)
        rightPanelVBox.pack_start(self.web, False, False)
        rightPanelVBox.pack_start(buttonsHBox, False, False)

        #ending buttons
        self.bRefresh = gtk.Button( _( 'Refresh List' ))
        self.bRefresh.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
        self.bInstall = gtk.Button(_( 'Install'))
        self.bInstall.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        hButBox = gtk.HButtonBox()
        hButBox.set_spacing( 6 )
        hButBox.set_layout( gtk.BUTTONBOX_SPREAD )
        hButBox.pack_start(self.bRefresh)
        hButBox.pack_start(self.bInstall)

        leftPanelVBox = gtk.VBox(homogeneous=False)
        leftPanelVBox.set_spacing(3)
        leftPanelVBox.pack_start(self.scroll, True, True)
        leftPanelVBox.pack_start(hButBox, False, False)

        panelSeparator = gtk.VSeparator()

        #list + right panel
        pluginHBox = gtk.HBox(homogeneous=False)
        pluginHBox.set_spacing(5)
        pluginHBox.pack_start(leftPanelVBox, False, False)
        pluginHBox.pack_start(panelSeparator, False, False)
        pluginHBox.pack_start(rightPanelVBox, True, True)

        #pack everything
        self.pack_start( pluginHBox, True, True )
        self.show_all()

        self.fillList()

        #connects
        self.bConfigure.connect( 'clicked', self.configurePlugin )
        self.bReload.connect( 'clicked', self.reloadPlugin )
        self.bRefresh.connect( 'clicked', self.refreshPlugins )
        self.bInstall.connect( 'clicked', self.installPlugin )
        self.list.connect( 'cursor-changed', self.row_selected )
        cellRendererToggle.connect( 'toggled', self.active_toggled, \
                ( self.listStore, 3 ) )

        #hack to fix the line wrap
        width = buttonsHBox.size_request()[0]+15 #to make it closer to the border
        self.description.set_size_request(width,-1)
        self.author.set_size_request(width,-1)
        self.web.set_size_request(width,-1)

    def fillList( self ):
        '''fills the plugin list'''
        self.listStore.clear()
        for i in sorted(self.pluginManager.getPlugins(), key=lambda x: x.lower()):
            plugin = self.pluginManager.getPluginData( i )
            if plugin:
                self.listStore.append(['<b>' + plugin['displayName'] + '</b>',
                    i, plugin['description'], self.pluginManager.isEnabled(i)])

    def getSelected( self ):
        '''Return the selected item'''
        model = self.list.get_model()
        selected = self.list.get_selection().get_selected()
        if selected[1]:
            return model.get(selected[1], 1)[0]
        else:
            return None

    def row_selected( self, *args ):
        '''callback for the row_selected event'''
        name = self.getSelected()
        plugin_instance = self.pluginManager.getPlugin(name)
        self.setDescription(name)
        if hasattr(plugin_instance, "configure") and callable(plugin_instance.configure) \
            and self.pluginManager.isEnabled(name):
            self.bConfigure.set_sensitive(True)
        else:
            self.bConfigure.set_sensitive(False)
        self.bReload.set_sensitive(True)

    def configurePlugin( self, *args ):
        '''call the configure method in the plugin'''
        plugin_instance = self.pluginManager.getPlugin( self.getSelected() )
        if hasattr(plugin_instance, "configure") and callable(plugin_instance.configure):
            plugin_instance.configure()

    def reloadPlugin( self, *args ):
        '''Reloads the plugin python code'''
        name = self.getSelected()
        self.pluginManager.restartPlugin(name)
        # update the metadata
        self.fillList()
        self.setDescription(name)

    def refreshPlugins( self, *args ):
        '''Loads new plugins'''
        for i in self.pluginManager.getNewModules():
            if i not in self.pluginManager.plugin_data:
                self.pluginManager.inspectPlugin(i)
            self.pluginManager.loadPlugin(i)
        self.fillList()

    def installPlugin( self, *args ):
        ''' chooserAction is a gtk.FILE_CHOOSER_ACTION specifying file or folder action '''
        fileChooser = gtk.FileChooserDialog(title=_("Select plugin's .py file"),\
                                                             action=gtk.FILE_CHOOSER_ACTION_OPEN,\
                                                             buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,\
                                                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        fileChooser.set_select_multiple(False)
        response = fileChooser.run()
        if response == gtk.RESPONSE_ACCEPT:
            selectedPath = fileChooser.get_filename()
            shutil.copy(selectedPath,paths.PLUGIN_HOME_PATH)
            fileChooser.destroy()
            self.refreshPlugins()
        else:
            fileChooser.destroy()

    def setDescription( self, name ):
        plugin_data = self.pluginManager.getPluginData(name)
        if plugin_data:
            self.description.set_label('' + plugin_data['description'] )
            string = ''
            for (author,mail) in plugin_data['authors'].iteritems():
                string += author + '\n(' + mail + ')\n'

            self.author.set_label( '' + string[:-1])
            self.web.set_label( '' + plugin_data['website'] )

    def active_toggled(self, cell, path, user_data):
        '''enable or disable the plugin'''
        model, column = user_data
        iterator= model.get_iter_from_string(path)
        plugin_name = model.get_value(iterator, 1)
        plugin_instance = self.pluginManager.getPlugin(plugin_name, True)

        if not plugin_instance:
            return
        if self.pluginManager.isEnabled(plugin_name):
            self.pluginManager.stopPlugin(plugin_name)
            model.set_value(iterator, column, False)

        plugins = self.config.user['activePlugins'].split( ',' )
        if plugin_name in plugins:
            plugins.pop( plugins.index(plugin_name))
            self.config.user['activePlugins'] = ','.join(plugins)
        else:
            status = self.pluginManager.checkPlugin(plugin_name)
            if status[0]:
                self.pluginManager.startPlugin(plugin_name)
                model.set_value(iterator, column, True)

                plugins = self.config.user['activePlugins'].split(',')
                if plugins[0] == '' and len(plugins) == 1:
                    self.config.user['activePlugins'] = plugin_name
                elif not plugin_name in plugins:
                    s = ','.join(plugins) + ',' + plugin_name
                    self.config.user['activePlugins'] = s
            else:
                dialog.error(_('Plugin initialization failed: \n') \
                      + status[1])

    def save(self):
      pass

class DesktopPage(gtk.VBox):
    ''' This represents the Webcam page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING-3)
        self.set_border_width(10)

        lbTitle = gtk.Label()
        lbTitle.set_markup(_('<b>Desktop Environment Integration</b>'))
        hbTitleLabel = gtk.HBox()
        hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
        self.pack_start(hbTitleLabel, False, False, padding=5)

        self.urlSettings = UrlSettings(config)
        frame1 = gtk.Frame(_('Links and files'))
#        frame1.set_border_width(4)
        frame1.add(self.urlSettings)
        
        self.emailSettings = EmailSettings(config)
        frame2 = gtk.Frame(_('E-mails'))
        #frame2.set_border_width(4)
        frame2.add(self.emailSettings)

        self.rgba = gtk.CheckButton(_('Enable rgba colormap (requires restart)'))
        self.rgba.set_active(self.config.glob['rgbaColormap'])
        self.rgba.set_tooltip_text(_('If enabled, it gives the desktop theme the ability' \
                                     ' to make transparent windows using the alpha channel'))

        self.disableTray = gtk.CheckButton(_('Disable tray icon (requires restart)'))
        self.disableTray.set_active(self.config.glob['disableTrayIcon'])

        self.pack_start(self.rgba, False)
        self.pack_start(self.disableTray, False)
        self.pack_start(frame1, False)
        self.pack_start(frame2, False)

    def save(self, widget=None):
        self.config.glob['rgbaColormap'] = self.rgba.get_active()
        self.config.glob['disableTrayIcon'] = self.disableTray.get_active()
        self.urlSettings.save()
        self.emailSettings.save()
        
class EmailSettings(gtk.VBox):
    def __init__(self, config):
        gtk.VBox.__init__(self)
        self.set_spacing(2)
        self.set_border_width(4)
        self.config = config

        self.markup = _('By default, your e-mails will be opened with <b>your webbrowser</b>.'
                'But you can change these settings, deciding to open you e-mails with a specific e-mail program.')

        self.infolabel = gtk.Label()
        self.infolabel.set_alignment(0.0, 0.0)

        self.hboxentry = gtk.HBox()
        self.entry = gtk.Entry()
        self.entry.connect('activate', self.save)
        self.hboxentry.set_spacing(3)
        self.hboxentry.pack_start(gtk.Label(_('Command:')), False)
        self.hboxentry.pack_start(self.entry)

        self.override = gtk.CheckButton(_('Override default settings'))
        self.override.set_active(self.config.glob['overrideMail'] != '')
        self.override.connect('toggled', self.toggleOverride)

        self.hboxtest = gtk.HBox()
        self.testbutton = gtk.Button(_('Click to test'))
        self.testbutton.connect('clicked', self.testMail)
        self.hboxtest.pack_start(gtk.Label())
        self.hboxtest.pack_start(self.testbutton, False, True, 6)

        self.hboxOverride = gtk.HBox()
        self.hboxOverride.set_spacing(10)
        self.hboxOverride.pack_start(self.override, False)
        self.hboxOverride.pack_start(self.hboxentry, True)

        self.pack_start(self.infolabel, False)
        self.pack_start(self.hboxOverride, False)
        self.pack_start(self.hboxtest, False)

        self.toggleOverride()
        self.connect('map', self.on_mapped)

    def toggleOverride(self, override=None):
        active = self.override.get_active()
        self.hboxentry.set_sensitive(active)
        self.hboxtest.set_sensitive(active)
        if active:
            self.entry.set_text(self.config.glob['overrideMail'])
        else:
            self.entry.set_text('')
        self.save()

    def save(self, widget=None):
        self.config.glob['overrideMail'] = self.entry.get_text()

    def testMail(self, button):
        self.save()
        try:
            os.popen(self.config.glob['overrideMail'])
        except OSError:
            pass

    def on_mapped(self, widget):
        #hack to fix the line wrap
        self.infolabel.set_size_request(self.hboxOverride.size_request()[0],-1)
        self.infolabel.set_justify(gtk.JUSTIFY_FILL)
        self.infolabel.set_line_wrap(True)
        self.infolabel.set_markup(self.markup)

class UrlSettings(gtk.VBox):
    def __init__(self, config):
        gtk.VBox.__init__(self)
        self.set_spacing(2)
        self.set_border_width(4)
        self.config = config

        detected = desktop.get_desktop(True)
        if detected:
            commandline = ' '.join(desktop.get_command(detected, '')).strip()
            tmp = {
                'detected': detected,
                'commandline': commandline,
            }
            self.markup = _('The detected desktop environment is '
                '<b>"%(detected)s"</b>. '
                '<span face="Monospace">%(commandline)s</span> '
                'will be used to open links and files') % tmp
        else:
            self.markup = _('<b>No desktop environment detected.</b> '
                'The first browser found will be used to open links')

        self.infolabel = gtk.Label()

        self.infolabel.set_alignment(0.0, 0.0)

        self.hboxentry = gtk.HBox()
        self.entry = gtk.Entry()
        self.entry.connect('activate', self.save)
        self.hboxentry.set_spacing(3)
        self.hboxentry.pack_start(gtk.Label(_('Command:')), False)
        self.hboxentry.pack_start(self.entry)

        self.override = gtk.CheckButton(_('Override detected settings'))
        self.override.set_active(self.config.glob['overrideDesktop'] != '')
        self.override.connect('toggled', self.toggleOverride)

        self.helplabel = gtk.Label()
        self.helplabel.set_markup(_('<i>Note:</i> %s is replaced by '
            'the actual url to be opened') % '%url%')
        self.helplabel.set_alignment(0.5, 1.0)

        self.hboxtest = gtk.HBox()
        self.testbutton = gtk.Button(_('Click to test'))
        self.testbutton.connect('clicked', self.testDesktop)
        self.hboxtest.pack_start(self.helplabel, True, False)
        self.hboxtest.pack_start(self.testbutton, False, True, 6)

        self.hboxOverride = gtk.HBox()
        self.hboxOverride.set_spacing(10)
        self.hboxOverride.pack_start(self.override, False)
        self.hboxOverride.pack_start(self.hboxentry, True)

        self.pack_start(self.infolabel, False)
        self.pack_start(self.hboxOverride, False)
        self.pack_start(self.hboxtest, False)

        self.toggleOverride()
        self.connect('map', self.on_mapped)

    def toggleOverride(self, override=None):
        active = self.override.get_active()
        self.hboxentry.set_sensitive(active)
        self.hboxtest.set_sensitive(active)
        if active:
            self.entry.set_text(self.config.glob['overrideDesktop'])
        else:
            self.entry.set_text('')
        self.save()

    def save(self, widget=None):
        desktop.override = self.entry.get_text()
        self.config.glob['overrideDesktop'] = self.entry.get_text()

    def testDesktop(self, button):
        self.save()
        try:
            desktop.open('http://www.emesene.org')
        except OSError:
            pass

    def on_mapped(self, widget):
        #hack to fix the line wrap
        self.infolabel.set_size_request(self.hboxOverride.size_request()[0],-1)
        self.infolabel.set_justify(gtk.JUSTIFY_FILL)
        self.infolabel.set_line_wrap(True)
        self.infolabel.set_markup(self.markup)

class AdvancedPage(gtk.VBox):
    ''' This represents the Webcam page. '''
    
    def __init__(self, config, controller):
        gtk.VBox.__init__(self)
        self.config = config
        self.controller = controller
        self.set_spacing(SPACING)
        self.set_border_width(10)

        lbTitle = gtk.Label()
        lbTitle.set_markup(_('<b>Advanced Settings</b>'))
        hbTitleLabel = gtk.HBox()
        hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
        self.pack_start(hbTitleLabel, False, False, padding=5)

        #debug
        debugLabel = gtk.Label(_("Debug"))
        self.debugChooser = gtk.combo_box_new_text()
        noDebugText = _("Don't show")
        debugText = _('Show debug in console')
        binaryText = _('Show binary codes in debug')
        bothDebugText = _('Show both types')
        self.debugChooser.append_text(noDebugText)
        self.debugChooser.append_text(debugText)
        self.debugChooser.append_text(binaryText)
        self.debugChooser.append_text(bothDebugText)
        debugConfig = self.config.glob['debug']
        binaryConfig = self.config.glob['binary']
        if debugConfig and not binaryConfig:
            self.debugChooser.set_active(1)
        elif debugConfig and binaryConfig:
            self.debugChooser.set_active(3)
        elif not debugConfig and binaryConfig:
            self.debugChooser.set_active(2)
        else:
            self.debugChooser.set_active(0)
        debugHBox = gtk.HBox()
        debugHBox.set_spacing(10)
        debugHBox.pack_start(debugLabel, False, False)
        debugHBox.pack_start(self.debugChooser, True, True)


        #login delay
        #disable "last message"
        #auto resize big emoticons
        self.canResize = gtk.CheckButton(\
            _('_Auto-resize big emoticons:\nmay be resource hungry but only when emoticon is visible'))
        if self.controller.connected:
            self.canResize.set_active(self.config.user['canResizeEmoticons'])
        else:
            self.canResize.set_sensitive(False)
        #prevent window closing if new message
        
        
        '''PACK EVERYTHING '''
        self.pack_start(debugHBox, False, False)
        self.pack_start(self.canResize, False, False)

    def save(self):
        #save global settings
        active = self.debugChooser.get_active()
        if active == 0:
            self.config.glob['debug'] = False
            self.config.glob['binary'] = False
        elif active == 1:
            self.config.glob['debug'] = True
            self.config.glob['binary'] = False
        elif active == 2:
            self.config.glob['debug'] = False
            self.config.glob['binary'] = True
        elif active == 3:
            self.config.glob['debug'] = True
            self.config.glob['binary'] = True

        #save user settings
        if self.controller.connected:
            self.config.user['canResizeEmoticons'] = self.canResize.get_active()

class SoundsPage(gtk.VBox):
   ''' This represents the Sounds page. '''   
   def __init__(self, config, controller):
      gtk.VBox.__init__(self)
      self.config = config
      self.controller = controller
      self.set_spacing(SPACING-3) #to fit the actual height
      self.set_border_width(10)
      self.handler = self.controller.sound
      self.installNewText = _('Install new...')
      
      lbTitle = gtk.Label()
      lbTitle.set_markup(_('<b>Sound notifications</b>'))
      hbTitleLabel = gtk.HBox()
      hbTitleLabel.pack_start(lbTitle, False, True, padding=5)
      self.pack_start(hbTitleLabel, False, False, padding=5)
      
      self.enablesounds = gtk.CheckButton(_('_Enable sound notifications'))
      self.enablesounds.set_active(self.config.user['enableSounds'])
      self.enablesounds.connect('toggled', self.soundsToggled)
      
      themes = os.listdir(paths.APP_PATH + os.sep + 'sound_themes')
      themes = [x for x in themes if not x.startswith('.')]
      self.theme = gtk.combo_box_new_text()
      labelTheme = gtk.Label(_('Theme:'))
      labelTheme.set_alignment(0.0, 0.5)
      labelTheme.set_use_underline(True)
      self.values2 = {}
      count=0
      self.soundsDefaultIndex = None
      for name in themes:
          self.theme.append_text(name)
          self.values2[name]=int(count)
          if name == 'default':
              self.soundsDefaultIndex = count
          count += 1
      self.theme.append_text(self.installNewText)
      if self.config.user['soundstheme'] in themes:
          self.theme.set_active(self.values2[self.config.user['soundstheme']])
      else:
          self.theme.set_active(0)
      self.theme.connect("changed", self.savetheme)
      
      vboxlabel = gtk.VBox(homogeneous=False, spacing=5)
      vboxlabel.pack_start(labelTheme, True, True)
      
      vboxentry = gtk.VBox(homogeneous=False, spacing=5)
      vboxentry.pack_start(self.theme, True, True)

      self.previewButton = gtk.Button()
      self.previewButton.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY,gtk.ICON_SIZE_SMALL_TOOLBAR))
      self.previewButton.connect('clicked', self.playPreview)
      self.previewButton.set_tooltip_text(_("Preview of the selected theme's incoming message sound"))
      
      hbox = gtk.HBox(homogeneous=False, spacing=SPACING)
      hbox.pack_start(vboxlabel, False, True)
      hbox.pack_start(vboxentry, True, True)
      hbox.pack_start(self.previewButton, False, False)
       
      self.playonline = gtk.CheckButton(_('Play a sound when someone gets online'))
      self.playonline.set_active(self.config.user['soundsplayOnline'])
      
      self.playoffline =  gtk.CheckButton(_('Play a sound when someone goes offline'))
      self.playoffline.set_active(self.config.user['soundsplayOffline'])
      
      self.playreceive =  gtk.CheckButton(_('Play a sound when someone sends you a message'))
      self.playreceive.set_active(self.config.user['soundsplayMessage'])
      
      self.playnudge =  gtk.CheckButton(_('Play a sound when someone sends you a nudge'))
      self.playnudge.set_active(self.config.user['soundsplayNudge'])

      self.playtransfer =  gtk.CheckButton(_('Play a sound when someone sends you a file'))
      self.playtransfer.set_active(self.config.user['soundsplayTransfer'])
      
      self.playsend =  gtk.CheckButton(_('Play a sound when you send a message'))
      self.playsend.set_active(self.config.user['soundsplaySend'])
      
      self.playerror =  gtk.CheckButton(_("Play a sound whenever there's an error message"))
      self.playerror.set_active(self.config.user['soundsplayError'])
      
      settings1 = gtk.VBox()
      settings1.pack_start(self.playonline)
      settings1.pack_start(self.playoffline)
      settings1.pack_start(self.playreceive)
      settings1.pack_start(self.playnudge)
      settings1.pack_start(self.playtransfer)
      settings1.pack_start(self.playsend)
      settings1.pack_start(self.playerror)
      
      frame1 = gtk.Frame(_('Events notifications'))
      frame1.set_border_width(4)
      frame1.add(settings1)
      
      self.playinactive =  gtk.CheckButton(_('Play the message sound only when the window is inactive'))
      self.playinactive.set_active(self.config.user['soundsplayInactive'])
      
      self.disablebusy =  gtk.CheckButton(_('Disable sounds when busy'))
      self.disablebusy.set_active(self.config.user['soundsdisableBusy'])

      self.beep =  gtk.CheckButton(_('Play the system beep instead of sound files'))
      self.beep.set_active(self.config.user['soundsbeep'])
      
      settings2 = gtk.VBox()
      settings2.pack_start(self.playinactive)
      settings2.pack_start(self.disablebusy)
      settings2.pack_start(self.beep)
      
      frame2 = gtk.Frame(_('Notifications settings'))
      frame2.set_border_width(4)
      frame2.add(settings2)
      
      self.pack_start(self.enablesounds, False, False)
      self.pack_start(hbox, False, False)
      self.pack_start(frame1, False, False)
      self.pack_start(frame2, False, False)
      
      self.show_all()
      self.soundsToggled(self.enablesounds)

   def playPreview(self, button):
      self.handler.sound.play(self.theme.get_active_text(), 'type')
   def savetheme(self, combo):
      active = combo.get_active_text()
      if active == self.installNewText:
         installed = self.installTheme(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,self.audioInstaller)
         if not installed == "":
            active = installed
            print active
            combo.prepend_text(active)
            self.soundsDefaultIndex += 1
            combo.set_active(0)
         else:
            combo.set_active(self.soundsDefaultIndex)
            active = "default"
      self.config.user['soundstheme'] = active
      self.handler.update()
   
   def audioInstaller(self, path):
      #read theme name
      themeName = path.split(os.sep)[-1]
      themes = os.listdir(paths.APP_PATH + os.sep + 'sound_themes')
      themes = [x for x in themes if not x.startswith('.')]
      if themeName in themes:
         print "There's already an audio theme with the same name"
         return ""
      #create the folder and copy the file inside
      theme_path=paths.APP_PATH + os.sep + 'sound_themes' + os.sep + themeName.lower()
      shutil.copytree(path,theme_path)
      return themeName.lower()
   
   def installTheme(self, chooserAction, installFunction, chooserTitle=_("Select theme's folder"), validateFunction=None):
      ''' chooserAction is a gtk.FILE_CHOOSER_ACTION specifying file or folder action '''
      fileChooser = gtk.FileChooserDialog(title=chooserTitle, action=chooserAction,\
                                              buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,\
                                              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
      fileChooser.set_select_multiple(False)
      response = fileChooser.run()
      if response == gtk.RESPONSE_ACCEPT:
         selectedPath = fileChooser.get_filename()
         themeName = installFunction(selectedPath)
         fileChooser.destroy()
         return themeName
      else:
         fileChooser.destroy()
         return ""
   
   def save(self):
      '''save the actual setting'''      
      self.config.user['soundsplayOnline'] = self.playonline.get_active()
      self.config.user['soundsplayOffline'] = self.playoffline.get_active()
      self.config.user['soundsplayMessage'] = self.playreceive.get_active()
      self.config.user['soundsplayNudge'] = self.playnudge.get_active()
      self.config.user['soundsplayTransfer'] = self.playtransfer.get_active()
      self.config.user['soundsplaySend'] = self.playsend.get_active()
      self.config.user['soundsplayError'] = self.playerror.get_active()
      
      self.config.user['soundsplayInactive'] = self.playinactive.get_active()
      self.config.user['soundsdisableBusy'] = self.disablebusy.get_active()
      self.config.user['soundsbeep'] = self.beep.get_active()
      self.handler.update()
      if self.enablesounds.get_active() == False and self.config.user['enableSounds'] == True:
         self.handler.stop()
      elif self.enablesounds.get_active() == True and self.config.user['enableSounds'] == False:
         self.handler.__init__(self.controller, self.controller.msn, action='start')
      self.config.user['enableSounds'] = self.enablesounds.get_active()
     
   def soundsToggled(self, check):
      self.save()
      self.theme.set_sensitive(check.get_active())
      self.playinactive.set_sensitive(check.get_active())
      self.disablebusy.set_sensitive(check.get_active())
      self.beep.set_sensitive(check.get_active())
      self.playonline.set_sensitive(check.get_active())
      self.playoffline.set_sensitive(check.get_active())
      self.playreceive.set_sensitive(check.get_active())
      self.playnudge.set_sensitive(check.get_active())
      self.playtransfer.set_sensitive(check.get_active())
      self.playsend.set_sensitive(check.get_active())
      self.playerror.set_sensitive(check.get_active())
      self.previewButton.set_sensitive(check.get_active())

''' AUX METHODS '''

class CreateColourButton(gtk.ColorButton):
    def __init__(self, config, setting):
        gtk.ColorButton.__init__(self)
        self.config = config
        self.colourSetting = setting
        
        self.set_color(gtk.gdk.color_parse(config.user[self.colourSetting]))
        self.connect('color-set', self.save)
    
    def save(self, button):
        self.config.user[self.colourSetting] = rgbToHexa(self.get_color())

# moved from emesenecommon
def rgbToHexa(color):
    '''take a gtk.gdk.Color end returns a string with html way color.
    Eg.: #FFCC00'''

    red = color.red >> 8
    green = color.green >> 8
    blue = color.blue >> 8

    return '#'+'%02X%02X%02X' % (red, green, blue)

def mkcheck(self, id, label, realparent=None):
    '''little helper function to add checkbuttons'''
    check = gtk.CheckButton(label)
    if realparent is None:
        check.set_active(self.config.user[id])
        check.connect('toggled', self.onToggled, id)
        self.pack_start(check, False, False, padding=0)
        setattr(self, id, check)
        self.checks.append(id)
        return
    
    check.set_active(realparent.config.user[id])
    check.connect('toggled', realparent.onToggled, id)
    self.pack_start(check, False, False, padding=0)
    setattr(realparent, id, check)
    realparent.checks.append(id)

