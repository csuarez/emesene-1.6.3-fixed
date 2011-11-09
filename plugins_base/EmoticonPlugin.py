import os
import base64
import gtk

import Plugin

class EmoticonContextMenu(gtk.Menu):
    def __init__(self, callback, active_item):
        gtk.Menu.__init__(self)
        # append two MenuItem's to this menu and set callbacks
        self.oneCharMenuItem = gtk.RadioMenuItem(None, _('Block one char emoticons'))
        self.oneCharMenuItem.set_name('one')
        if active_item == 'one':
            self.oneCharMenuItem.set_active(True)
        self.append(self.oneCharMenuItem)
        
        self.anyCharMenuItem = gtk.RadioMenuItem(self.oneCharMenuItem, _('Block any emoticon'))
        self.anyCharMenuItem.set_name('any')
        if active_item == 'any':
            self.anyCharMenuItem.set_active(True)
        self.append(self.anyCharMenuItem)
        
        self.disabledItem = gtk.RadioMenuItem(self.oneCharMenuItem, _('Show all emoticons'))
        self.disabledItem.set_name('no')
        if active_item == 'no':
            self.disabledItem.set_active(True)
        self.append(self.disabledItem)

        self.oneCharCallback = self.oneCharMenuItem.connect('activate', callback)
        self.anyCharCallback = self.anyCharMenuItem.connect('activate', callback)
        self.disabledCallback = self.disabledItem.connect('activate', callback)
        
        self.show_all()
    
    def clean(self):
        self.oneCharMenuItem.disconnect(self.oneCharCallback)
        self.anyCharMenuItem.disconnect(self.anyCharCallback)
        self.disabledItem.disconnect(self.disabledCallback)

class EmoticonButton(gtk.ToolButton):
    def __init__(self, conversation, EmoticonPlugin):
        gtk.ToolButton.__init__(self, gtk.STOCK_CANCEL)
        self.set_label(_('Block emoticons'))
        self.set_tooltip_text(_('Block emoticons'))
        self.conversation = conversation
       
        self.plugin = EmoticonPlugin
        self.blocked = []
        self.blockedType = {}

        active = "no"
        # stop emoticons from blocked users in config
        for user in self.conversation.getMembers():
            configValue = self.plugin.config.getPluginValue(self.plugin.name, user, "no")
            if configValue != 'no':
                self.block(user, configValue)
                active = configValue

        # create context menu for this button
        self.menu = EmoticonContextMenu(self.onChooseMenu, active)

        self.connect('clicked', self.onClick)
                
        # connect signal handlers
        self.emoTransferedCallback = self.conversation.switchboard.msn.connect('custom-emoticon-transfered', self.onEmoticonTransfered)
        self.emoReceivedCallback = self.conversation.switchboard.connect('custom-emoticon-received', self.onEmoticonReceived)
        
    # two methods to do the same thing.. not very pythonic but they could be changed/improved in some way
    # so i decided to keep them separated for clarity. They both delete temporary emoticons from blocked
    # users
    def onEmoticonReceived(self, switchboard, shortcut, msnobj):
        user = msnobj.creator
        
        if not self.conversation.customEmoticons.emoticons.has_key(user):
            return False
        
        if user in self.blocked:
            if self.blockedType[user] == 'one':
                if len(shortcut) == 1 and self.conversation.customEmoticons.emoticons[user].has_key(shortcut): 
                    del self.conversation.customEmoticons.emoticons[user][shortcut]
            else:
                self.conversation.customEmoticons.emoticons[user].clear()
        else:
            return False
                
        return True
        
    def onEmoticonTransfered(self, switchboard, to, msnobj, path):
        user = msnobj.creator
        
        if not self.conversation.customEmoticons.emoticons.has_key(user):
            return False
        
        if user in self.blocked:
            if self.blockedType[user] == 'one':
                shortcut = False
                # search for the right key in the emoticons' dictionary, that's the shortcut we're looking for
                # avoid RuntimeError due to a dictionary change during iteration
                try:
                    for key, value in self.conversation.customEmoticons.emoticons[user].iteritems():
                        if value == msnobj.sha1d:
                            shortcut = key
                except RuntimeError:
                    pass
                        
                if shortcut and len(shortcut) == 1 and self.conversation.customEmoticons.emoticons[user].has_key(shortcut):
                    del self.conversation.customEmoticons.emoticons[user][shortcut]
            else:
                self.conversation.customEmoticons.emoticons[user].clear()
        else:
            return False
                
        return True

    def onChooseMenu(self, menuitem):
        # get current switchboard's users, blacklist them in the config and block them
        if menuitem.get_name() == 'no':
            for user in self.conversation.getMembers():
                self.unblock(user)
                self.plugin.config.setPluginValue(self.plugin.name, user, "no");
        else:
            for user in self.conversation.getMembers():
                self.block(user, menuitem.get_name())
                # distinguish between users blacklisted for one character or any character emoticons
                self.plugin.config.setPluginValue(self.plugin.name, user, menuitem.get_name());

    def block(self, user, type):
        if self.conversation.customEmoticons.emoticons.has_key(user):
            # delete temporary emoticons coming from this user, depending on the choosen type of blacklisting (one or any char)
            if type == 'one':
                # avoid RuntimeError due to a dictionary change during iteration
                try:
                    for key, value in self.conversation.customEmoticons.emoticons[user].iteritems():
                        if len(key) == 1:
                            del self.conversation.customEmoticons.emoticons[user][key]
                except RuntimeError:
                    pass
                
            # this else assures backward compatibility with older configs
            else:
                self.conversation.customEmoticons.emoticons[user].clear()

        if user not in self.blocked:
            self.blocked.append(user)
        self.blockedType[user] = type
        
    def unblock(self, user):
        if user in self.blocked:
            self.blocked.remove(user)
            del self.blockedType[user]
        
    def onClick(self, button):
        self.menu.popup(None, None, None, 1, 0)

    def clean(self):
        for user in self.blocked:
            self.unblock()

        # disconnect handlers
        self.conversation.switchboard.msn.disconnect(self.emoTransferedCallback)
        self.conversation.switchboard.disconnect(self.emoReceivedCallback)

        self.menu.clean()
        self.destroy()


class MainClass(Plugin.Plugin):
    description = _("Hides annoying emoticons with a simple click in a conversation window's button")
    authors = {'Lorenzo Rovigatti': 'lorenzo dot rovigatti at gmail dot com', \
               'arielj' : 'arieljuod@gmail.com' }
    website = ''
    displayName = _('Emoticon Stopper')
    name = 'EmoticonPlugin'
    
    def __init__(self, controller, msn):
        Plugin.Plugin.__init__(self, controller, msn)
        
        # load the plugin's config
        self.config = controller.config
        self.config.readPluginConfig(self.name)

        encodedimage = \
        """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
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
"""
        decodedimage = base64.decodestring(encodedimage)
        self.pixbuf = gtk.gdk.pixbuf_new_from_data(decodedimage, \
                                 gtk.gdk.COLORSPACE_RGB, True, 8, 24, 24, 96)

    def addButtonToConv(self, conversationManager=None, conversation=None, window=None):
        # initialize a button for emoticon stopping
        button = EmoticonButton(conversation, self)
        imagenoicons = gtk.Image()
        imagenoicons.set_from_pixbuf(self.pixbuf)
        imagenoicons.show()
        button.set_icon_widget(imagenoicons)
        button.show()
        # add the button to the toolbar
        conversation.ui.input.toolbar.add(button)
        
    def removeButtonFromConv(self, conversationManager=None, conversation=None, window=None):
        # remove the button from the toolbar
        for button in conversation.ui.input.toolbar.get_children():
            if type(button) == EmoticonButton:
                conversation.ui.input.toolbar.remove(button)
                button.destroy()

    def start(self):
        # tell the controller to call the function addButtonToConv to add the stopEmoticon button
        # every time a new conversation is created, and append it to all the active conversations
        for conversation in self.getOpenConversations():
            self.addButtonToConv(conversation=conversation)
        
        self.convOpen = self.controller.conversationManager.connect_after(\
                                 'new-conversation-ui', self.addButtonToConv)
        
        self.convClose = self.controller.conversationManager.connect(\
                          'close-conversation-ui', self.removeButtonFromConv)
        
        self.enabled = True

    def stop(self):
        # clean up everything
        self.controller.conversationManager.disconnect(self.convOpen)
        self.controller.conversationManager.disconnect(self.convClose)
        
        for conversation in self.getOpenConversations():
            self.removeButtonFromConv(conversation=conversation)

        self.enabled = False

    def check(self):
        # this plugin really needs nothing to work :)
        return (True, 'Ok')
