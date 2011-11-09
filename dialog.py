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

'''a module that defines the api of objects that display dialogs'''

import os
import gtk
import gobject
import paths
import Avatar
import urllib
import Theme
import thread
import time

import gc

import abstract.stock as stock

_avatar_chooser = None

def window_add_image(window, stock_id):
    '''add a stock image as the first element of the window.hbox'''

    image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_DIALOG)
    window.hbox.pack_start(image, False)
    image.show()

    return image

def window_add_button(window, stock_id, label=''):
    '''add a button to the window'''

    button = gtk.Button(label, stock=stock_id)
    window.bbox.pack_start(button, True, True)
    button.show()

    return button

def window_add_label(window, text):
    '''add a label with the text (as pango) on the window'''

    label = gtk.Label()
    label.set_selectable(True)
    label.set_use_markup(True)
    label.set_markup('<span>' + \
        text + "</span>")
    window.hbox.pack_start(label, True, True)
    label.show()

    return label

def close_cb(widget, event, window, response_cb, *args):
    '''default close callback, call response_cb with args if it's not
    None'''

    if response_cb:
        response_cb(*args)

    window.hide()

def default_cb(widget, window, response_cb, *args):
    '''default callbacks, call response_cb with args if it's not
    None'''

    if response_cb:
        response_cb(*args)

    window.hide()

def entry_cb(widget, window, response_cb, *args):
    '''callback called when the entry is activated, it call the response
    callback with the stock.ACCEPT and append the value of the entry
    to args'''
    args = list(args)
    args.append(window.entry.get_text())

    if response_cb:
        if type(widget) == gtk.Entry:
            response_cb(stock.ACCEPT, *args)
        else:
            response_cb(*args)

    window.hide()

def add_contact_cb(widget, window, response_cb, response):
    '''callback called when a button is selected on the add_contact dialog'''

    alias = window.entryAlias.get_text()
    contact = window.entry.get_text()
    group = window.groupComboEntry.get_children()[0].get_text()

    window.hide()
    response_cb(response, contact, group, alias)

def set_picture_cb(widget, window, response_cb, response, path):
    '''callback called when a button is selected on the set_picture dialog'''
    window.hide()
    response_cb(response, path)

def common_window(message, stock_id, response_cb, title):
    '''create a window that displays a message with a stock image'''
    window = new_window(title, response_cb)
    window_add_image(window, stock_id)
    window_add_label(window, message)

    return window

def message_window(message, stock_id, response_cb, title):
    '''create a window that displays a message with a stock image
    and a close button'''
    window = common_window(message, stock_id, response_cb, title)
    btn = add_button(window, gtk.STOCK_CLOSE, stock.CLOSE, response_cb, \
        default_cb)
    window.set_focus(btn)

    return window

def entry_window(message, text, response_cb, title, *args):
    '''create a window that contains a label and a entry with text set
    and selected, and two buttons, accept, cancel'''
    window = new_window(title, response_cb)
    window_add_label(window, message)

    entry = gtk.Entry()
    entry.set_text(text)
    entry.select_region(0, -1)

    entry.connect('activate', entry_cb, window, response_cb, *args)

    window.hbox.pack_start(entry, True, True)
    add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
        entry_cb, *args)
    add_button(window, gtk.STOCK_OK, stock.ACCEPT, response_cb,
        entry_cb, *args)

    setattr(window, 'entry', entry)

    window.set_focus(entry)
    entry.show()

    return window

def add_button(window, gtk_stock, stock_id, response_cb,
    callback, *args):
    '''add a button and connect the signal'''
    button = gtk.Button(stock=gtk_stock)
    window.bbox.pack_start(button, True, True)
    button.connect('clicked', callback, window, response_cb,
        stock_id, *args)

    button.show()

    return button

def new_window(title, response_cb, *args):
    '''build a window with the default values and connect the common
    signals, return the window'''

    window = gtk.Window()
    window.set_title(title)
    window.set_default_size(150, 100)
    window.set_position(gtk.WIN_POS_CENTER)
    window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
    window.set_resizable(False)
    window.set_border_width(8)

    vbox = gtk.VBox(spacing=4)
    hbox = gtk.HBox(spacing=4)
    bbox = gtk.HButtonBox()
    bbox.set_spacing(4)
    bbox.set_layout(gtk.BUTTONBOX_END)

    vbox.pack_start(hbox, True, True)
    vbox.pack_start(bbox, False)

    window.add(vbox)

    setattr(window, 'vbox', vbox)
    setattr(window, 'hbox', hbox)
    setattr(window, 'bbox', bbox)

    args = list(args)
    args.insert(0, stock.CLOSE)
    window.connect('delete-event', close_cb, window,
        response_cb, *args)

    vbox.show_all()

    return window

def error(message, response_cb=None, title=_("Error!")):
    '''show an error dialog displaying the message, this dialog should
    have only the option to close and the response callback is optional
    since in few cases one want to know when the error dialog was closed,
    but it can happen, so return stock.CLOSE to the callback if its set'''
    message_window(message, gtk.STOCK_DIALOG_ERROR, response_cb,
        title).show()

def warning(message, response_cb=None, title=_("Warning")):
    '''show a warning dialog displaying the messge, this dialog should
    have only the option to accept, like the error dialog, the response
    callback is optional, but you have to check if it's not None and
    send the response (that can be stock.ACCEPT or stock.CLOSE, if
    the user closed the window with the x)'''
    message_window(message, gtk.STOCK_DIALOG_WARNING, response_cb,
        title).show()

def information(message, response_cb=None,
                        title=_("Information"),):
    '''show a warning dialog displaying the messge, this dialog should
    have only the option to accept, like the error dialog, the response
    callback is optional, but you have to check if it's not None and
    send the response (that can be stock.ACCEPT or stock.CLOSE, if
    the user closed the window with the x)'''
    message_window(message, gtk.STOCK_DIALOG_INFO, response_cb,
        title).show()

def exception(message, response_cb=None, title=_("Exception"),):
    '''show the message of an exception on a dialog, useful to
    connect with sys.excepthook'''
    window = new_window(title, response_cb)
    label = window_add_label(window, message)
    add_button(window, gtk.STOCK_CLOSE, stock.CLOSE, response_cb,
        default_cb)
    window.set_resizable(False)
    window.show()

def yes_no(message, response_cb, *args):
    '''show a confirm dialog displaying a question and two buttons:
    Yes and No, return the response as stock.YES or stock.NO or
    stock.CLOSE if the user closes the window'''
    window = common_window(message, gtk.STOCK_DIALOG_QUESTION,
        response_cb, _("Confirm"))
    add_button(window, gtk.STOCK_YES, stock.YES, response_cb,
        default_cb, *args)
    add_button(window, gtk.STOCK_NO, stock.NO, response_cb,
        default_cb, *args)
    window.set_resizable(False)
    window.show()

def yes_no_cancel(message, response_cb, *args):
    '''show a confirm dialog displaying a question and three buttons:
    Yes and No and Cancel, return the response as stock.YES, stock.NO,
    stock.CANCEL or stock.CLOSE if the user closes the window'''
    window = common_window(message, gtk.STOCK_DIALOG_QUESTION,
        response_cb, _("Confirm"))
    add_button(window, gtk.STOCK_YES, stock.YES, response_cb,
        default_cb, *args)
    add_button(window, gtk.STOCK_NO, stock.NO, response_cb,
        default_cb, *args)
    add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
        default_cb, *args)
    window.set_resizable(False)
    window.show()

def accept_cancel(message, response_cb, *args):
    '''show a confirm dialog displaying information and two buttons:
    Accept and Cancel, return stock.ACCEPT, stock.CANCEL or
    stock.CLOSE'''
    window = common_window(message, gtk.STOCK_DIALOG_QUESTION,
        response_cb, _("Confirm"))
    add_button(window, gtk.STOCK_OK, stock.ACCEPT, response_cb,
        default_cb, *args)
    add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
        default_cb, *args)
    window.set_resizable(False)
    window.show()

def contact_added_you(accounts, response_cb,
                            title=_("User invitation")):
    '''show a dialog displaying information about users
    that added you to their userlists, the accounts parameter is
    a tuple of mails that represent all the users that added you,
    the way you confirm (one or more dialogs) doesn't matter, but
    you should call the response callback only once with a tuple
    like: ((mail1, stock.YES), (mail2, stock.NO), (mail3, stock.CANCEL))
    YES means add him to your userlist, NO means block him, CANCEL
    means remind me later.'''
    raise NotImplementedError("This method isn't implemented")

def add_contact(groups, group, response_cb, genericAvatarPixbuf=None, title=_("Add user")):
    '''show a dialog asking for an user address, and (optional)
    the group(s) where the user should be added, the response callback
    receives the response type (stock.ADD, stock.CANCEL or stock.CLOSE)
    the account and a tuple of group names where the user should be
    added (give a empty tuple if you don't implement this feature,
    the controls are made by the callback, you just ask for the email,
    don't make any control, you are just implementing a GUI! :P'''
    #genericAvatarPixbuf has the blank avatar shown in the dialog

    window = new_window(title, response_cb)

    label = gtk.Label(_("Account"))
    label_align = gtk.Alignment(0.0, 0.5)
    label_align.add(label)
    entry = gtk.Entry()

    labelAlias = gtk.Label(_("Alias"))
    labelAlias_align = gtk.Alignment(0.0, 0.5)
    labelAlias_align.add(labelAlias)
    entryAlias = gtk.Entry()   

    group_label = gtk.Label(_("Group"))
    groupsList = gtk.ListStore(gobject.TYPE_STRING)
    groupComboEntry = gtk.ComboBoxEntry(groupsList, 0)
    groupCompletion = gtk.EntryCompletion()
    groupCompletion.set_model(groupsList)
    groupComboEntry.get_children()[0].set_completion(groupCompletion)
    groupCompletion.set_text_column(0)

    group_label_align = gtk.Alignment(0.0, 0.5)
    group_label_align.add(group_label)

    #fill groups combo box
    for i in groups:
        groupsList.append([i])

    table = gtk.Table(3, 2)
    table.attach(label_align, 0, 1, 0, 1)
    table.attach(entry, 1, 2, 0, 1)
    table.attach(labelAlias_align, 0, 1, 1, 2)
    table.attach(entryAlias, 1, 2, 1, 2)
    table.attach(group_label_align, 0, 1, 2, 3)
    table.attach(groupComboEntry, 1, 2, 2, 3)
    table.set_row_spacings(2)
    table.set_col_spacings(8)

    if genericAvatarPixbuf:
        genericAvatar = gtk.Image()
        genericAvatar.set_size_request(96, 96)
        genericAvatar.set_from_pixbuf(genericAvatarPixbuf)
        window.hbox.pack_start(genericAvatar, True, True)

    window.hbox.pack_start(table, True, True)
    window.hbox.set_spacing(10)

    add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
        add_contact_cb)
    add_button(window, gtk.STOCK_OK, stock.ACCEPT, response_cb,
        add_contact_cb)

    setattr(window, 'entryAlias', entryAlias)
    setattr(window, 'entry', entry)
    setattr(window, 'groupComboEntry', groupComboEntry)

    entry.connect('activate', add_contact_cb, window, response_cb,
        stock.ACCEPT)
    groupComboEntry.get_children()[0].connect('activate', add_contact_cb, window, response_cb, stock.ACCEPT)
    window.set_resizable(False)
    window.set_focus(entry)
    window.show_all()

def add_group(response_cb, title=_("Add group")):
    '''show a dialog asking for a group name, the response callback
    receives the response (stock.ADD, stock.CANCEL, stock.CLOSE)
    and the name of the group, the control for a valid group is made
    on the controller, so if the group is empty you just call the
    callback, to make a unified behaviour, and also, to only implement
    GUI logic on your code and not client logic
    cb args: response, group_name'''
    window = entry_window(_("Group name"), '', response_cb, title)
    window.set_resizable(False)
    window.show()

def set_nick(nick, response_cb, title=_("Change nick")):
    '''show a dialog asking for a new nick and displaying the current
    one, the response_cb receives the old nick, the new nick,
    and the response (stock.ACCEPT, stock.CANCEL or stock.CLOSE)
    cb args: response, old_nick, new_nick'''
    window = entry_window(_("New nick"), nick, response_cb, title,
    nick)
    window.set_resizable(False)
    window.show()

def set_message(message, response_cb,
    title=_("Change personal message")):
    '''show a dialog asking for a new personal message and displaying
    the current one, the response_cb receives the old personal message
    , the new personal message and the response
    (stock.ACCEPT, stock.CANCEL or stock.CLOSE)
    cb args: response, old_pm, new_pm'''
    window = entry_window(_("New personal message"),
        message, response_cb, title, message)
    window.set_resizable(False)
    window.show()

def set_picture(controller, path_current, cache_path,
        response_cb, title=_("Change picture")):
    '''show a dialog asking for the display picture and return the selected
    one, path_current is the path of the current selected picture.
    cache_path is a folder where the avatars are loaded and saved
     Return the response and a new path or None if no new picture
    is selected'''
    global _avatar_chooser

    def _on_hide(window):
        global _avatar_chooser
        
        if _avatar_chooser:
            _avatar_chooser.stop_and_clear()
            del _avatar_chooser
                
        _avatar_chooser = None

    if not _avatar_chooser:
        _avatar_chooser = AvatarChooser(controller, response_cb,
            path_current, cache_path)

        _avatar_chooser.connect('hide', _on_hide)
        _avatar_chooser.show()
    else:
        _avatar_chooser.grab_focus()

def set_custom_emoticon(ce_dir, response_cb, smilie_list):
    '''show a dalog to create a custome emotion, ce_dir is the
    directory where the image chooser dialog will open'''
    CEChooser(ce_dir, response_cb, smilie_list).show()

def show_profile(controller, nick, psm, currentAvatarPath, response_cb):
    '''shows the user profile (nick, psm, avatar) and the
    The user can change any of them'''
    Profile(controller, nick, psm, currentAvatarPath, response_cb)

def rename_group(name, response_cb, title=_("Rename group")):
    '''show a dialog with the group name and ask to rename it, the
    response callback receives stock.ACCEPT, stock.CANCEL or stock.CLOSE
    the old and the new name.
    cb args: response, old_name, new_name
    '''
    window = entry_window(_("New group name"), name, response_cb,
        title, name)
    window.set_resizable(False)
    window.show()

def set_contact_alias(account, alias, response_cb,
                        title=_("Set alias")):
    '''show a dialog showing the current alias and asking for the new
    one, the response callback receives,  the response
    (stock.ACCEPT, stock.CANCEL, stock.CLEAR <- to remove the alias
    or stock.CLOSE), the account, the old and the new alias.
    cb args: response, account, old_alias, new_alias'''
    alias = alias or ''
    window = entry_window(_("Contact alias"), alias, response_cb,
        title, account, alias)
    add_button(window, gtk.STOCK_CLEAR, stock.CLEAR, response_cb,
        entry_cb, account, alias)
    window.set_resizable(False)
    window.show()

def about_dialog(name, version, copyright, comments, license, website,
    authors, translators, logo_path):
    '''show an about dialog of the application:
    * title: the title of the window
    * name: the name of the appliaction
    * version: version as string
    * copyright: the name of the copyright holder
    * comments: a description of the application
    * license: the license text
    * website: the website url
    * authors: a list or tuple of strings containing the contributors
    * translators: a string containing the translators
    '''

    def close_about(widget, response_id):
        if response_id == gtk.RESPONSE_CANCEL:
            widget.destroy()

    about = gtk.AboutDialog()
    about.set_name(name)
    about.set_version(version)
    about.set_copyright(copyright)
    about.set_comments(comments)
    about.connect('response', close_about)
    about.set_license(license)
    about.set_website(website)

    about.set_authors(authors)
    about.set_translator_credits(translators)
    icon = gtk.image_new_from_file(logo_path)
    about.set_icon(icon)
    about.set_logo(icon)
    about.run()

def _callback(*args):
    '''a callback that print all the arguments'''
    print(args)

def _test():
    '''a test method'''
    '''error("Error!", _callback)
    warning("Warning!", _callback)
    information("Information", _callback)
    yes_no("to_be || !to_be", _callback, "foo")
    yes_no_cancel("to_be or not to_be", _callback, "bar")
    accept_cancel("Silly question", _callback, "baz")
    add_contact(('c', 'b', 'a'), _callback)
    add_group(_callback)
    set_nick("my other nick is a ferrari", _callback)
    set_message("too personal", _callback)
    rename_group("Groupal", _callback)
    set_contact_alias("dude@live.com", "some dude", _callback)
    exception("*implodes*")'''
    set_picture('', _callback)
    gtk.main()

#TODO: rewrite me on the contact_added_you method
import Widgets
class AddBuddy(gtk.Window):
    '''Confirm dialog informing that someone has added you
    ask if you want to add him to your contact list'''

    def __init__(self, controller):
        '''Constructor. Packs widgets'''
        gtk.Window.__init__(self)

        self.mails = []  # [(mail, nick), ...]
        self.pointer = 0
        self.controller = controller

        # window
        self.set_title(_("Add contact"))
        self.set_border_width(4)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_resizable(False)
        self.move(30, 30) # top-left
        self.connect('delete-event', self.cb_delete)

        ## widgets

        # main vbox
        self.vbox = gtk.VBox()

        # hbox with image, pages, and main text
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(4)
        self.hbox.set_border_width(4)

        # the contents of the hbox (image+vboxtext)
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_DIALOG_QUESTION, \
            gtk.ICON_SIZE_DIALOG)
        self.imagebox = gtk.HBox()
        self.imagebox.set_border_width(4)
        self.image.set_alignment(0.0, 0.5)

        # the vboxtext (pages+text)
        self.vboxtext = gtk.VBox()
        self.pages = self._buildpages()
        self.text = gtk.Label()
        self.text.set_selectable(True)
        self.text.set_ellipsize(3) #pango.ELLIPSIZE_END
        self.text.set_alignment(0.0, 0.0) # top left
        self.text.set_width_chars(60)

        # hboxbuttons + button box
        self.hboxbuttons = gtk.HBox()
        self.hboxbuttons.set_spacing(4)
        self.hboxbuttons.set_border_width(4)
        self.buttonbox = gtk.HButtonBox()
        self.buttonbox.set_layout(gtk.BUTTONBOX_END)

        # the contents of the buttonbox
        self.later = gtk.Button()
        self.later.add(gtk.Label(_('Remind me later')))
        self.later.connect('clicked', self.cb_cancel)
        self.addbutton = gtk.Button(stock=gtk.STOCK_ADD)
        self.addbutton.connect('clicked', self.cb_add)
        self.bReject = gtk.Button()
        self.bReject.add(gtk.Label(_('Reject')))
        self.bReject.connect('clicked', self.cb_rej)
        self.profile = gtk.Button()
        self.profile.add(gtk.Label(_('View profile')))
        self.profile.connect('clicked', self.cb_profile)
        self.showDetails = False
        self.bDetails = gtk.Button()
        self.bDetails.add(gtk.Label(_('Details')))
        self.bDetails.connect('clicked', self.cb_show_details)
        self.bHideDetails = gtk.Button()
        self.bHideDetails.add(gtk.Label(_('Hide details')))
        self.bHideDetails.connect('clicked', self.cb_hide_details)

        ## packing
        self.add(self.vbox)
        self.vbox.pack_start(self.hbox, True, True)
        self.vbox.pack_start(self.hboxbuttons, False, False)

        self.imagebox.pack_start(self.image)
        self.hbox.pack_start(self.imagebox, False, False)
        self.hbox.pack_start(self.vboxtext, True, True)
        self.vboxtext.pack_start(self.pages, False, False)
        self.vboxtext.pack_start(self.text, True, True)

        self.hboxbuttons.pack_start(self.bReject, False, False)
        self.hboxbuttons.pack_start(self.later, False, False)
        self.hboxbuttons.pack_start(self.addbutton, False, False)
        self.hboxbuttons.pack_end(self.buttonbox)
        self.buttonbox.pack_start(self.bDetails)

    def cb_show_details(self, button):
        #the widget that appears when the user clicks "details"
        self.detailsSection = gtk.HBox(spacing=5)
        genericAvatar = gtk.image_new_from_pixbuf(self.controller.theme.getImage('login'))
        genericAvatar.set_size_request(96, 96)
        labelAlias = gtk.Label(_("Alias"))
        labelAlias_align = gtk.Alignment(0.0, 0.5)
        labelAlias_align.add(labelAlias)
        self.entryAlias = gtk.Entry()

        group_label = gtk.Label(_("Group"))
        groupsList = gtk.ListStore(gobject.TYPE_STRING)
        self.groupComboEntry = gtk.ComboBoxEntry(groupsList, 0)
        groupCompletion = gtk.EntryCompletion()
        groupCompletion.set_model(groupsList)
        self.groupComboEntry.get_children()[0].set_completion(groupCompletion)
        groupCompletion.set_text_column(0)
        group_label_align = gtk.Alignment(0.0, 0.5)
        group_label_align.add(group_label)

        #fill groups combo box
        for i in self.controller.groups.groups.keys():
            groupsList.append([i])

        labelsVBox = gtk.VBox()
        labelsVBox.pack_start(labelAlias_align)
        labelsVBox.pack_start(group_label_align)

        entriesVBox = gtk.VBox()
        entriesVBox.pack_start(self.entryAlias)
        entriesVBox.pack_start(self.groupComboEntry)

        attributesHBox = gtk.HBox()
        attributesHBox.pack_start(labelsVBox)
        attributesHBox.pack_start(entriesVBox, True, True)

        profileHBox = gtk.HButtonBox()
        profileHBox.set_layout(gtk.BUTTONBOX_END)
        profileHBox.pack_start(self.profile)

        rightSideVBox = gtk.VBox()
        rightSideVBox.pack_start(attributesHBox)
        rightSideVBox.pack_start(profileHBox)

        self.detailsSection.pack_start(genericAvatar)
        self.detailsSection.pack_start(rightSideVBox, True, True)

        self.vbox.pack_end(self.detailsSection)
        self.detailsSection.show_all()

        self.buttonbox.remove(self.bDetails)
        self.buttonbox.pack_start(self.bHideDetails)
        self.profile.show_all()
        self.bHideDetails.show_all()
        self.showDetails = True

    def cb_hide_details(self, button):
        self.profile.get_parent().remove(self.profile)
        self.vbox.remove(self.detailsSection)
        self.detailsSection.destroy()
        self.buttonbox.remove(self.bHideDetails)
        self.buttonbox.pack_start(self.bDetails)
        self.bDetails.show_all()
        self.showDetails = False

    def _buildpages(self):
        '''Builds hboxpages, that is a bit complex to include in __init__'''
        hboxpages = gtk.HBox()

        arrowleft = gtk.Arrow(gtk.ARROW_LEFT,gtk.SHADOW_NONE)
        arrowleft.set_size_request(-1,15)
        self.buttonleft = gtk.Button()
        self.buttonleft.set_relief(gtk.RELIEF_NONE)
        self.buttonleft.add(arrowleft)
        self.buttonleft.connect('clicked', self.switchmail, -1)

        arrowright = gtk.Arrow(gtk.ARROW_RIGHT,gtk.SHADOW_NONE)
        arrowright.set_size_request(-1,15)
        self.buttonright = gtk.Button()
        self.buttonright.set_relief(gtk.RELIEF_NONE)
        self.buttonright.add(arrowright)
        self.buttonright.connect('clicked', self.switchmail, 1)

        self.currentpage = gtk.Label()

        hboxpages.pack_start(gtk.Label(), True, True) # align to right
        hboxpages.pack_start(self.buttonleft, False, False)
        hboxpages.pack_start(self.currentpage, False, False)
        hboxpages.pack_start(self.buttonright, False, False)

        return hboxpages

    def append(self, nick, mail):
        '''Adds a new pending user'''
        self.mails.append((mail, gobject.markup_escape_text(nick)))
        self.update()
        self.show_all()
        self.present()

    def update(self):
        '''Update the GUI, including labels, arrow buttons, etc'''
        try:
            mail, nick = self.mails[self.pointer]
        except IndexError:
            self.hide()
            return

        if nick != mail:
            mailstring = "<b>%s</b>\n<b>(%s)</b>" % (nick, mail)
        else:
            mailstring = '<b>%s</b>' % mail

        self.text.set_markup(mailstring + _(' has added you.\n'
            'Do you want to add him/her to your contact list?'))

        self.buttonleft.set_sensitive(True)
        self.buttonright.set_sensitive(True)
        if self.pointer == 0:
            self.buttonleft.set_sensitive(False)
        if self.pointer == len(self.mails) - 1:
            self.buttonright.set_sensitive(False)

        self.currentpage.set_markup('<b>(%s/%s)</b>' % \
            (self.pointer + 1, len(self.mails)))

        if self.showDetails:
            self.entryAlias.set_text("")
            self.groupComboEntry.child.set_text("")

    def switchmail(self, button, order):
        '''Moves the mail pointer +1 or -1'''
        if (self.pointer + order) >= 0:
            if (self.pointer + order) < len(self.mails):
                self.pointer += order
            else:
                self.pointer = 0
        else:
            self.pointer = len(self.mails) - 1

        self.update()

    def hide(self):
        '''Called to hide the window'''
        gtk.Window.hide(self)
        self.controller.addBuddy = None

    def cb_delete(self, *args):
        '''Callback when the window is destroyed'''
        self.controller.addBuddy = None
        self.destroy()

    def cb_cancel(self, button):
        '''Callback when the cancel button is clicked'''
        self.mails.pop(self.pointer)
        self.switchmail(None, -1)
        self.update()

    def cb_profile(self, button):
        '''Callback when the view profile button is clicked'''
        self.controller.seeProfile(self.mails[self.pointer][0])

    def cb_add(self, button):
        '''Callback when the add button is clicked'''
        mail, nick = self.mails[self.pointer]
        group = ''
        alias = ''
        if self.showDetails:
            group = self.groupComboEntry.get_children()[0].get_text()
            if group and not group in self.controller.groups.groups.keys():
                    self.controller.groups.add(group)
            alias = self.entryAlias.get_text()

        self.controller.contacts.add(mail, group, *(self.delayedAlias, mail, alias))
#        self.controller.contacts.add(mail, group)
        self.cb_cancel(None)

    def delayedAlias(self, account, alias):
        self.controller.contacts.set_alias(account, alias)
        return False

    def cb_rej(self, button):
        mail, nick = self.mails[self.pointer]
        self.controller.contacts.remove_from_pending_list(mail)
        self.cb_cancel(None)

class Profile(gtk.Window):
    '''Dialog where user can change nick, psm and avatar'''
    def __init__(self, controller, nick, psm, avatarPath, response_cb):
        gtk.Window.__init__(self)

        #window properties
        self.set_border_width(10)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_resizable(False)

        self.controller = controller
        self.response_cb = response_cb
        self.nick = nick
        self.psm = psm
        self.currentAvatarPath = avatarPath
        self.newAvatarPath = avatarPath

        #build the window
        #nick and pm labels and entries
        self.set_title(_('My profile'))
        self.nickLabel=gtk.Label(_('Nick:'))
        self.nickLabel.set_alignment(0.0,0.5)
        self.nickEntry=gtk.Entry()
        self.nickEntry.set_text(self.nick)
        self.psmLabel=gtk.Label(_('Personal Message:'))
        self.psmLabel.set_alignment(0.0,0.5)
        self.psmEntry=gtk.Entry()
        self.psmEntry.set_text(self.psm)
        self.vbox = gtk.VBox()
        self.vbox.add(self.nickLabel)
        self.vbox.add(self.nickEntry)
        self.vbox.add(self.psmLabel)
        self.vbox.add(self.psmEntry)
        self.vbox.set_size_request(300, -1)

        #avatar frame
        self.currentAvatar = gtk.Image()
        self.currentAvatar.set_size_request(96, 96)
        if os.path.exists(avatarPath):
            pixbuf = gtk.gdk.pixbuf_new_from_file(avatarPath)
            self.currentAvatar.set_from_pixbuf(pixbuf)
        self.frame_current = gtk.Frame(_("Avatar"))
        self.frame_current.add(self.currentAvatar)
        self.avatarEventBox = gtk.EventBox()
        self.avatarEventBox.add(self.frame_current)
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(10)
        self.hbox.add(self.avatarEventBox)
        self.hbox.add(self.vbox)

        #accept/cancel buttons
        self.acceptButton = gtk.Button(stock=gtk.STOCK_OK)
        self.cancelButton = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.buttonshbox = gtk.HButtonBox()
        self.buttonshbox.set_layout(gtk.BUTTONBOX_END)
        self.buttonshbox.add(self.cancelButton)
        self.buttonshbox.add(self.acceptButton)

        self.vbox2 = gtk.VBox()
        self.vbox2.add(self.hbox)
        self.vbox2.add(self.buttonshbox)

        #connect signals
        self.avatarEventBox.connect("button-press-event", self.choose_picture)
        self.acceptButton.connect("clicked", self.on_accept)
        self.cancelButton.connect("clicked", self.on_cancel)
        self.connect('delete-event', self.on_close)
        self.nickEntry.connect('activate', self.on_accept)
        self.psmEntry.connect('activate', self.on_accept)
        self.controller.connect('avatar-changed', self.updateAvatar)
        self.controller.msn.connect('self-personal-message-changed', self.update_pm_entry)
        self.controller.msn.connect('self-nick-changed', self.update_nick_entry)

        #add everything to the window and show it
        self.add(self.vbox2)
        self.show_all()

    #this method updates the avatar if it's changed using another method while the dialog is open
    #but if the third parameter is not None, it can be called from other places
    def updateAvatar(self, controller, path=None):
        if path != None:
            avatarPath = path
        else:
            avatarPath = controller.config.user['avatarPath']
        if os.path.exists(avatarPath):
            pixbuf = gtk.gdk.pixbuf_new_from_file(avatarPath)
            self.currentAvatar.set_from_pixbuf(pixbuf)

    def update_nick_entry(self, msnp, oldNick, newNick):
        self.nickEntry.set_text(newNick)

    def update_pm_entry(self, msnp, user, pm):
        self.psmEntry.set_text(pm)

    #this method show the avatar chooser dialog and saves the new avatar if any
    #this method does not change the actual avatar, just the dialog's avatar
    def choose_picture(self, widget, event):
        def _on_picture_selected(response, path):
            if response == stock.ACCEPT and path != self.currentAvatarPath:
                self.newAvatarPath = path
                self.updateAvatar(self.controller,path)

        avatar_cache = self.controller.config.getAvatarsCachePath()
        set_picture(self.controller, self.currentAvatarPath, avatar_cache, _on_picture_selected)

    #if nick, psm or avatar was changed, callback the new values
    def on_accept(self, button):
        '''method called when the user clicks the button'''
        
        newNick = self.nickEntry.get_text()
        newPsm = self.psmEntry.get_text()
        
        if self.nick != newNick or self.psm != newPsm or self.currentAvatarPath != self.newAvatarPath:
            self.destroy()
            self.response_cb(stock.ACCEPT, newNick, newPsm, self.newAvatarPath)
        else:
            self.destroy()
            self.response_cb(stock.CANCEL, '', '', '')

    def on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.destroy()
        self.response_cb(stock.CANCEL, '', '', '')

    def on_close(self, window, event):
        '''called when the user click on close'''
        self.destroy()
        self.response_cb(stock.CLOSE, '', '', '')

# Class that holds the iconview from the avatar chooser dialog
class IconView(gtk.HBox):
    def __init__(self, label, path_list, avatar_chooser):
        gtk.HBox.__init__(self)
        self.set_spacing(4)
        self.chooser = avatar_chooser
        self.model = gtk.ListStore(gtk.gdk.Pixbuf, str)   
        self.iconview = gtk.IconView(self.model)
        self.iconview.enable_model_drag_dest([('text/uri-list', 0, 0)], gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)
        self.iconview.connect("drag-data-received", self._drag_data_received)
        self.iconview.set_pixbuf_column(0)
        self.iconview.connect("item-activated", self._on_icon_activated)
        self.iconview.connect("button_press_event", self.pop_up)

        self.label = gtk.Label(label)
        
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_IN)
        self.scroll.add(self.iconview)
        self.pack_start(self.scroll, True, True)

        self.STOP = False
        # Start a new thread to fill the iconview with images from path_list
        thread.start_new_thread(self.fill, (path_list,))

    def stop_and_clear(self):
        self.STOP = True
        self.model.clear()

    def fill(self, path_list):
        '''fill the IconView with avatars from the list of pictures'''
        for search_path in path_list:
            if os.path.exists(search_path):
                for path in os.listdir(search_path):
                    name = os.path.splitext(path)[0]
                    if self.STOP:
                        return False
                    if not name.endswith('_thumb') and not path.endswith('tmp') \
                       and not path.endswith('xml') and not path.endswith('db'):
                        gtk.gdk.threads_enter()
                        self.add_picture(os.path.join(search_path, path))
                        # make update the iconview
                        self.iconview.queue_draw()
                        gtk.gdk.threads_leave()        
                        
                        # give some time to the main thread (for GUI updates)
                        time.sleep(0.001)
        # Force Garbage Collector to tidy objects
        # see http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
        gc.collect()
    
    def pop_up(self, iconview, event):
        if event.button == 3 and self.label.get_text() != _('System pictures'):
            path = self.iconview.get_path_at_pos(event.x, event.y)
            if path != None:
                self.iconview.select_path(path)
                remove_menu = gtk.Menu()
                remove_item = gtk.ImageMenuItem(_('Delete'))
                remove_item.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
                remove_item.connect('activate', self.chooser._on_remove)
                remove_menu.append(remove_item)
                remove_menu.popup(None, None, None, event.button, event.time)
                remove_menu.show_all()

    def _drag_data_received(self, treeview, context, x, y, selection, info, timestamp):
        '''method called on an image dragged to the view'''
        urls = selection.data.split('\n')
        for url in urls:
            path = url.replace('file://', '')
            path = path.replace('\r', '')

            # the '\x00' value makes an error
            path = path.replace(chr(0), '')

            # this seems to be an error on ntpath but we take care :S
            try:
                if os.path.exists(path):
                    self.add_picture(path)
            except TypeError, e:
                error(_("Could not add picture:\n %s") % (str(e),))

    def add_picture(self, path):
        '''Adds an avatar into the IconView'''
        try:
            if os.path.exists(path) and os.access(path, os.R_OK)\
                    and not self.is_in_view(path):
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(path)
                except:
                    try:
                        os.remove(path)
                    except:
                        pass
                    return
 
                # On nt images are 128x128 (48x48 on xp)
                # On kde, images are 64x64
                if (self.label.get_text() == _('System pictures') or \
                 self.label.get_text() == _('Contact pictures')) and \
                 (pixbuf.get_width() != 96 or pixbuf.get_height() != 96):
                    pixbuf = pixbuf.scale_simple(96, 96, gtk.gdk.INTERP_BILINEAR)

                if self.model != None and not self.STOP:
                    self.model.append([pixbuf, path])
                    # Esplicitely delete gtkpixbuf
                    # see http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
                    del pixbuf
            else:
                print path, 'not readable'
        except gobject.GError:
            print "image at %s could not be loaded" % path

    def is_in_view(self, filename):
        '''return True if filename already on the iconview'''
        if os.name != 'nt' and not self.STOP:
            for (pixbuf, path) in self.model:
                if os.path.samefile(filename, path):
                    return True
        return False

    def _on_icon_activated(self, *args):
        '''method called when a picture is double clicked'''
        self.chooser._on_accept(None)
    
    def get_selected_items(self):
        return self.iconview.get_selected_items()

class AvatarChooser(gtk.Window):
    '''A dialog to choose an avatar'''

    def __init__(self, controller, response_cb, picture_path='',
            cache_path='.'):
        '''Constructor, response_cb receive the response number, the new file
        selected and a list of the paths on the icon view.
        picture_path is the path of the current display picture,
        '''
        gtk.Window.__init__(self)

        self.controller = controller
        self.response_cb = response_cb
        self.cache_path = cache_path

        self.set_title(_("Avatar chooser"))
        self.set_default_size(640, 400)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        faces_paths = []
        if os.name == 'nt':
            appDataFolder = os.path.split(os.environ['APPDATA'])[1]
            faces_path = os.path.join(os.environ['ALLUSERSPROFILE'], appDataFolder, \
                         "Microsoft", "User Account Pictures", "Default Pictures")
            #little hack to fix problems with encoding
            unicodepath=u"%s" % faces_path
            faces_paths = [unicodepath]
        else:
            faces_paths = ['/usr/share/kde/apps/faces',\
                           '/usr/share/kde4/apps/kdm/pics/users', \
                           '/usr/share/pixmaps/faces']

        self.iconViews = []
        self.iconViews.append( IconView(_('Used'), [cache_path], self) )
        self.iconViews.append( IconView(_('System pictures'), faces_paths, self) )
        self.iconViews.append( IconView(_('Contact pictures'),[self.controller.config.getCachePath()], self) )

        vbox = gtk.VBox(spacing=4)
        side_vbox = gtk.VBox(spacing=4)
        hbox = gtk.HBox(spacing=4)

        hbbox = gtk.HButtonBox()
        hbbox.set_spacing(4)
        hbbox.set_layout(gtk.BUTTONBOX_END)

        vbbox = gtk.VButtonBox()
        vbbox.set_spacing(4)
        vbbox.set_layout(gtk.BUTTONBOX_START)

        b_clear = gtk.Button(_("No picture"))
        self.b_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.b_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.b_remove_all = gtk.Button(_("Remove all"))
        b_accept = gtk.Button(stock=gtk.STOCK_OK)
        b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        b_accept.set_sensitive(False)

        b_clear.connect('clicked', self._on_clear)
        self.b_add.connect('clicked', self._on_add)
        self.b_remove.connect('clicked', self._on_remove)
        self.b_remove_all.connect('clicked', self._on_remove_all)
        b_accept.connect('clicked', self._on_accept)
        b_cancel.connect('clicked', self._on_cancel)
        self.connect('delete-event', self._on_close)
        self.connect("key-press-event", self.onKeyPress)

        self.img_current = gtk.Image()
        self.img_current.set_size_request(96, 96)
        frame_current = gtk.Frame(_("Current"))
        frame_current.add(self.img_current)

        hbbox.pack_start(b_clear, False)
        hbbox.pack_start(b_cancel, False)
        hbbox.pack_start(b_accept, False)

        vbbox.pack_start(self.b_add, False)
        vbbox.pack_start(self.b_remove, False)
        vbbox.pack_start(self.b_remove_all, False)

        side_vbox.pack_start(frame_current, False)
        side_vbox.pack_start(vbbox)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(True)
        
        for view in self.iconViews:
            self.notebook.append_page(view, view.label)
            view.iconview.connect("selection-changed",\
                                self.onSelectionChanged, b_accept)
        self.notebook.connect("switch-page", self._on_tab_changed, b_accept)

        #close dialog at logout
        self.controller.msn.connect('user-disconnected', self._on_close)
        self.controller.msn.connect('connection-problem', self._on_close)
        self.controller.msn.connect('connection-closed', self._on_close)
        self.controller.msn.connect('disconnected', self._on_close)
        self.controller.mainWindow.menu.disconnectItem.connect(\
                                    'button-release-event', self._on_close)
        if self.controller.trayIcon != None and \
           self.controller.trayDisconnect != None:
            self.controller.trayDisconnect.connect('activate', self._on_close)

        hbox.pack_start(self.notebook, True, True)
        hbox.pack_start(side_vbox, False, False)

        vbox.pack_start(hbox, True, True)
        vbox.pack_start(hbbox, False)

        vbox.show_all()
        self.add(vbox)

        self.set_current_picture(picture_path)

    def onSelectionChanged(self, iconView, accept_button):
        selected = iconView.get_selected_items()
        if len(selected) == 0:
            accept_button.set_sensitive(False)
        else:
            accept_button.set_sensitive(True)
        
    def stop_and_clear(self):
        for view in self.iconViews:
            view.stop_and_clear()
        # Force Garbage Collector to tidy objects
        # see http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
        gc.collect()

    def _on_tab_changed(self, notebook, page, page_num, b_accept):
        view = self.iconViews[page_num]
        if view.label.get_text() == _('System pictures'):
            self.b_add.set_sensitive(False)
            self.b_remove.set_sensitive(False)
            self.b_remove_all.set_sensitive(False)
        elif view.label.get_text() == _('Contact pictures'):
            self.b_add.set_sensitive(False)
            self.b_remove.set_sensitive(True)
            self.b_remove_all.set_sensitive(True)
        else:
            self.b_add.set_sensitive(True)
            self.b_remove.set_sensitive(True)
            self.b_remove_all.set_sensitive(True)
        self.onSelectionChanged(view.iconview, b_accept)

    def set_current_picture(self, path):
        '''set the current picture on the frame'''
        if os.path.exists(path):
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            self.img_current.set_from_pixbuf(pixbuf)

    def get_selected(self):
        '''return a tuple (pixbuf, path) of the selection, or None'''
        iter = self.get_selected_iter()

        if iter:
            view = self.iconViews[self.notebook.get_current_page()]
            return view.model[iter]

        return None

    def get_selected_iter(self):
        '''return the selected iter or None'''
        view = self.iconViews[self.notebook.get_current_page()]
        if len(view.get_selected_items()) > 0:
            item = view.get_selected_items()[0]
            return view.model.get_iter(item)

        return None

    def get_iter_from_filename(self, path):
        '''return the iter of a filename or None'''
        view = self.iconViews[self.notebook.get_current_page()]
        for row in view.model:
            (pixbuf, filename) = row

            if self.samefile(filename, path):
                return row.iter

        return None

    def samefile(self, path1, path2):
        '''return True if the files are the same file 
        this is a workaround to os.path.samefile that doesn't exist
        on windows'''
        path1 = os.path.abspath(os.path.normpath(path1))
        path2 = os.path.abspath(os.path.normpath(path2))

        return ((hasattr(os.path, 'samefile') and \
           os.path.samefile(path1, path2)) or \
           (path1.lower() == path2.lower()))

    def remove(self, path):
        '''remove the avatar in path'''
        view = self.iconViews[self.notebook.get_current_page()]
        del view.model[self.get_iter_from_filename(path)]
        try:
            os.remove(path)
        except Exception, e:
            print "could not remove", path
            
        try:
            parts = os.path.splitext(path)
            os.remove(parts[0] + "_thumb" + parts[1])
        except Exception, e:
            pass

    def remove_selected(self):
        '''Removes avatar from a TreeIter'''
        selected = self.get_selected()

        if selected:
            (pixbuf, path) = selected
            self.remove(path)

    def remove_all(self):
        '''remove all the items on the view'''
        view = self.iconViews[self.notebook.get_current_page()]
        for (pixbuf, path) in view.model:
            self.remove(path)

        view.model.clear()

    def _on_add(self, button):
        '''called when the user select the add button'''
        def _on_image_selected(response, path):
            '''method called when an image is selected'''
            if response == gtk.RESPONSE_ACCEPT:
                try:
                    av = Avatar.Avatar(self.controller, path, self.cache_path, resizeDialog=True)
                    filename = av.getImagePath()
                    view = self.iconViews[self.notebook.get_current_page()] 
                    view.add_picture(av.getImagePath())
                except Exception, e:
                    error(str(e))

        ImageChooser(paths.HOME_DIR, _on_image_selected).run()

    def _on_remove(self, event):
        '''Removes the selected avatar'''
        self.remove_selected()

    def _on_remove_all(self, button):
        '''Removes all avatars from the cache'''
        def on_response_cb(response):
            '''response callback for the confirm dialog'''
            if response == stock.YES:
                self.remove_all()

        yes_no(_("Are you sure you want to remove all items?"),
            on_response_cb)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        selected = self.get_selected()
        filename = ''

        if selected:
            filename = selected[1]

            self.hide()
            self.response_cb(stock.ACCEPT, filename)
        else:
            error(_("No picture selected"))

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(stock.CANCEL, '')

    def _on_clear(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(stock.CLEAR, '')

    def _on_close(self, *args):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(stock.CLOSE, '')

    def onKeyPress(self , widget, event):
        '''called when the user press a key'''
        if event.keyval == gtk.keysyms.Delete:
            self.remove_selected()

class ImageChooser(gtk.FileChooserDialog):
    '''a class to select images'''

    def __init__(self, path, response_cb):
        '''class constructor, path is the directory where the
        dialog opens'''
        gtk.FileChooserDialog.__init__(self, _("Image Chooser"), \
                    parent=None, action=gtk.FILE_CHOOSER_ACTION_OPEN)

        self.response_cb = response_cb

        self.set_default_size(600, 400)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)

        self.vbox.set_spacing(4)

        self.set_current_folder(path)

        hbbox = gtk.HButtonBox()
        hbbox.set_spacing(4)
        hbbox.set_layout(gtk.BUTTONBOX_END)

        b_accept = gtk.Button(stock=gtk.STOCK_OK)
        b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        b_accept.connect('clicked', self._on_accept)
        b_cancel.connect('clicked', self._on_cancel)
        self.connect('delete-event', self._on_close)
        self.connect("file-activated",self._on_accept)

        hbbox.pack_start(b_cancel, False)
        hbbox.pack_start(b_accept, False)

        self.vbox.pack_end(hbbox, False)

        self.show_all()

        self._add_filters()
        self._add_preview()

    def _add_filters(self):
        '''
        Adds all the possible file filters to the dialog. The filters correspond
        to the gdk available image formats
        '''

        # All files filter
        all_files = gtk.FileFilter()
        all_files.set_name(_('All files'))
        all_files.add_pattern('*')

        # All images filter
        all_images = gtk.FileFilter()
        all_images.set_name(_( 'All images'))

        filters = []
        formats = gtk.gdk.pixbuf_get_formats()
        for format in formats:
            filter = gtk.FileFilter()
            name = "%s (*.%s)" % (format['description'], format['name'])
            filter.set_name(name)

            for mtype in format['mime_types']:
                filter.add_mime_type(mtype)
                all_images.add_mime_type(mtype)

            for pattern in format['extensions']:
                tmp = '*.' + pattern
                filter.add_pattern(tmp)
                all_images.add_pattern(tmp)

            filters.append(filter)


        self.add_filter(all_files)
        self.add_filter(all_images)
        self.set_filter(all_images)

        for filter in filters:
            self.add_filter(filter)

    def _add_preview(self):
        '''
        Adds a preview widget to the file chooser
        '''

        self.image = gtk.Image()
        self.image.set_size_request(128, 128)
        self.image.show()

        self.set_preview_widget(self.image)
        self.set_preview_widget_active(True)

        self.connect('selection-changed', self._on_update_preview)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        filename = get_filename(self)
        if os.path.isfile(filename):
            self.hide()
            self.response_cb(gtk.RESPONSE_ACCEPT, filename)
        else:
            error(_("No picture selected"))

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(gtk.RESPONSE_CANCEL, get_filename(self))

    def _on_close(self, window, event):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(gtk.RESPONSE_CLOSE, get_filename(self))

    def _on_update_preview(self, filechooser):
        '''
        Updates the preview image
        '''
        hasPreview = False

        path = get_preview_filename(self)

        if path:
            # if the file is smaller than 1MB we
            # load it, otherwise we dont
            if os.path.isfile(path) and os.path.getsize(path) <= 1000000:
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(get_filename(self))
                    if pixbuf.get_width() > 128 and pixbuf.get_height() > 128:
                        pixbuf = pixbuf.scale_simple(128, 128, gtk.gdk.INTERP_BILINEAR)
                    self.image.set_from_pixbuf(pixbuf)

                except gobject.GError:
                    self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                        gtk.ICON_SIZE_DIALOG)
            else:
                self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                    gtk.ICON_SIZE_DIALOG)

class CEChooser(ImageChooser):
    '''a dialog to create a custom emoticon'''
    SMALL = _("small (16x16)")
    BIG = _("big (50x50)")

    def __init__(self, path, response_cb, smilie_list):
        '''class constructor'''
        ImageChooser.__init__(self, path, None)

        self.response_cb = response_cb

        label = gtk.Label(_("Shortcut"))
        self.shortcut = gtk.Entry(7)
        self.combo = gtk.combo_box_new_text()

        tooltip_t = _("You can add an emoticon also by entering the url an image (url must start with www. or http:// and finish with a file extension of the supported files).")

        labelurl = gtk.Label(_("Or enter an image url"))
        labelurl.set_tooltip_text(tooltip_t)
        self.url = gtk.Entry()

        self.combo.append_text(CEChooser.SMALL)
        self.combo.append_text(CEChooser.BIG)
        self.combo.set_active(0)

        hbox0 = gtk.HBox()
        hbox1 = gtk.HBox()
        vbox1 = gtk.VBox()
        vbox2 = gtk.VBox()

        hbox1.add(self.shortcut)
        hbox1.add(self.combo)

        vbox2.add(self.url)
        vbox2.add(hbox1)

        vbox1.add(labelurl)
        vbox1.add(label)

        hbox0.add(vbox1)
        hbox0.add(vbox2)

        self.vbox.pack_start(hbox0, False)
        hbox0.show_all()

        self.smilie_list = smilie_list
        pygtk_v = gtk.pygtk_version
        if (pygtk_v[0] == 2 and pygtk_v[1] > 15) or (pygtk_v[0] > 2):
            self._on_changed(None)
            self.shortcut.connect('changed', self._on_changed)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        filename = get_filename(self)
        shortcut = self.shortcut.get_text()
        size = self.combo.get_model().get_value(self.combo.get_active_iter(), 0)

        URL = self.url.get_text()
        if URL.startswith('www.'):
            URL = 'http://'+URL

        ENDEXT = False
        for format in gtk.gdk.pixbuf_get_formats():
            for ext in format['extensions']:
                ENDEXT = ENDEXT or URL.endswith('.'+ext)

        if URL.startswith('http://') and ENDEXT == True:
            if not shortcut:
                error(_("Empty shortcut"))
            else:
                NAME = URL.split('/')[-1]
                DEST = paths.SMILIES_HOME_PATH + NAME
                emoticonimg = urllib.urlretrieve(URL, DEST)
                self.hide()
                self.response_cb(stock.ACCEPT, DEST, shortcut, size)
                os.remove(DEST)
        else:
            if os.path.isfile(filename):
                if not shortcut:
                    error(_("Empty shortcut"))
                else:
                    self.hide()
                    self.response_cb(stock.ACCEPT, filename, shortcut, size)
            else:
                error(_("No picture selected"))

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(stock.CANCEL, None, None, None)

    def _on_close(self, window, event):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(stock.CLOSE, None, None, None)

    def _on_changed(self, shortcut):
        '''called when the text in self.shortcut changes'''

        SHORTCUT = self.shortcut.get_text()

        if SHORTCUT in self.smilie_list or SHORTCUT == "":
            self.shortcut.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_ERROR)
        else:
            self.shortcut.set_property('secondary-icon-stock', None)

def get_filename(self):
    '''Shortcut to get a properly-encoded filename from a file chooser'''
    filename = self.get_filename()
    if filename and gtk.gtk_version >= (2, 10, 0):
        return gobject.filename_display_name(filename)
    else:
        return filename

def get_preview_filename(self):
    '''Shortcut to get a properly-encoded preview filename'''
    filename = self.get_filename()
    if filename and gtk.gtk_version >= (2, 10, 0):
        return gobject.filename_display_name(filename)
    else:
        return filename

if __name__ == '__main__':
    #_test()
    ac = AvatarChooser(_callback, '/home/mariano/default/icon96.png', '/home/mariano/default/', [])
    ac.show()
    #ic = ImageChooser('/home/mariano/default', _callback)
    #ic.show()
    #ce = CEChooser('/home/mariano/default', _callback)
    #ce.show()

    gtk.main()
