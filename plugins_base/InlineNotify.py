# -*- coding: utf-8 -*-

import gtk
import gobject

import Plugin
import desktop
from emesenelib.common import escape
from emesenelib.common import unescape
from Parser import PangoDataType

ERROR = ''

class MainClass(Plugin.Plugin):
    '''Main plugin class'''
    
    description = _('Notifies various events through messages in your conversation')
    authors = {'Tito': 'tito@webtito.be'}
    website = 'http://perso.webtito.be'
    displayName = _('Inline notifications')
    name = 'InlineNotify'
    
    def __init__(self, controller, msn):
        '''Contructor'''
        Plugin.Plugin.__init__(self, controller, msn, 1000)
        self.controller = controller
        self.description = _('Notifies various events through messages in your conversation')
        self.authors = {'Tito': 'tito@webtito.be'}
        self.website = 'http://perso.webtito.be'
        self.displayName = _('Inline notifications')
        self.name = 'InlineNotify'

        self.enabled = False
        self.config = controller.config
        self.config.readPluginConfig(self.name)
        
        self.signals = {}
        self.signals['nick-changed'] = self.nick
        self.signals['contact-status-change'] = self.status
        self.signals['display-picture-changed'] = self.avatar
        self.signals['personal-message-changed'] = self.personal
        self.ids = []
        
        self.status = {
            'NLN' : _('online'),
            'AWY' : _('away'),
            'BSY' : _('busy'),
            'BRB' : _('be right back'),
            'PHN' : _('on the phone'),
            'LUN' : _('gone to lunch'),
            'IDL' : _('idle'),
            'FLN' : _('offline') }
        
    def start(self):
        self.enabled = True
        for (key, value) in self.signals.iteritems():
            self.ids.append(self.msn.connect(key, value))
    
    def stop(self):
        for identifier in self.ids:
            self.msn.disconnect(identifier)
        self.ids = []
        self.enabled = False
        return True
    
    def check(self):
        return (True, 'Ok')
    
    def nick(self, msnp, mail, nick):
        result = self.controller.conversationManager.getOpenConversation(mail)
        if result != None:
            window, conversation = result
            alias = self.controller.contacts.get_display_name(mail)
            if alias != nick: mail = alias
            text = _('%(mail)s is now called %(nick)s') % {'mail': mail, 'nick': nick}
            conversation.appendOutputText(None, text, 'information')
    
    def status(self, msnp, mail, status):
        result = self.controller.conversationManager.getOpenConversation(mail)
        if result != None:
            window, conversation = result
            nick = self.controller.contacts.get_display_name(mail)
            text = _('%(nick)s is now %(status)s') % {'nick' : nick, 'status' : self.status[status]}
            conversation.appendOutputText(None, text, 'information')
    
    def avatar(self, mnsp, p2p, msnobj, mail):
        result = self.controller.conversationManager.getOpenConversation(mail)
        if result != None:
            window, conversation = result
            nick = self.controller.contacts.get_display_name(mail)
            text = _('%s has a new avatar') % nick
            conversation.appendOutputText(None, text, 'information')
    
    def personal(self, msnp, mail, pm):
        result = self.controller.conversationManager.getOpenConversation(mail)
        if result != None:
            window, conversation = result
            nick = self.controller.contacts.get_display_name(mail)
            if pm != '': text = _('%(nick)s has a new personal message : %(message)s') % {'nick' : nick, 'message' : pm}
            else: text = _('%s doesn\'t have personal message anymore') % nick
            conversation.appendOutputText(None, text, 'information')
