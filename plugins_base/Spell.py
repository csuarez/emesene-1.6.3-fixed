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

VERSION = '0.3'

import gettext
import commands
import re

import Plugin
import dialog

ERROR = ''

try:
    import gtkspell
except:
    ERROR = _('You need to install gtkspell (python-gnome2-extras) to use Spell plugin')

class MainClass(Plugin.Plugin):
    '''Main plugin class'''
    
    description = _('SpellCheck for emesene')
    authors = { 'Roger Duran' : 'RogerDuran at gmail dot com' }
    website = 'http://www.rogerpc.com.ar'
    displayName = _('Spell')
    name = 'Spell'
    def __init__(self, controller, msn):
        '''Constructor'''
        
        Plugin.Plugin.__init__(self, controller, msn)
        
        self.description = _('SpellCheck for emesene')
        self.authors = { 'Roger Duran' : 'RogerDuran at gmail dot com' }
        self.website = 'http://www.rogerpc.com.ar'
        self.displayName = _('Spell')
        self.name = 'Spell'
        
        self.controller = controller
        self.config = controller.config
        self.conversationManager = self.controller.conversationManager
                
        self.config.readPluginConfig(self.name)
        self.lang = self.config.getPluginValue(self.name, 'lang', 'en')
        
        self.newConversationWindowId = 0
        self.closeConversationWindowId = 0
        self.onInputFormatChangedId = 0
        
    def onInputFormatChanged(self, controller, textView):

        buffer = textView.get_buffer()
        if not buffer:
            return
        
        table = buffer.get_tag_table()
        if not table:
            return
        
        tag = table.lookup('gtkspell-misspelled')
        if not tag:
            return
        
        tag.set_priority(table.get_size() - 1)
    
    def start(self):
        '''start the plugin'''
        # this signals should be emitted by conversationManager
        self.newConversationWindowId = self.conversationManager.connect(
            'new-conversation-ui', self.newConversationWindow)
        self.closeConversationWindowId = self.conversationManager.connect(
            'close-conversation-ui', self.closeConversationWindow)
        self.onInputFormatChangedId = self.controller.connect(
            'input-format-changed', self.onInputFormatChanged)
        
        self.enabled = True
        
        self.applyAllConv(self.setSpell)
        self.applyAllConv(self.setLang)
        
    def stop(self, removeSpell=True):
        '''stop the plugin'''
        self.conversationManager.disconnect(self.newConversationWindowId)
        self.conversationManager.disconnect(self.closeConversationWindowId)
        self.controller.disconnect(self.onInputFormatChangedId)
        
        self.applyAllConv(self.removeSpell)
        
        self.enabled = False
        
    def error(self, message, removeSpell=True):
        if self.enabled:
           dialog.error( message + " " + \
               _("Plugin disabled."))
        self.stop(removeSpell)

    def applyAllConv(self, command):
        '''Applies a command to all open convs'''
        if self.enabled:
            for conversation in self.getOpenConversations():
                textView = conversation.ui.input.input
                if not command(textView):
                    return False
        
    def removeSpell(self, textView):
        try:
            gtkspell.get_from_text_view(textView).detach()
        except (SystemError, Exception):
            print "Can't detach gtkspell. Ignoring."
            return
        
    def setSpell(self, textView):
        try:
            gtkspell.Spell(textView, self.lang)
        except Exception, e:
            print str(e)
            self.error(_('Error applying Spell to input (%s)') % e, False)
            return False
        
    def setLang(self, textView):
        if self.lang == '':
            self.lang = None
        try:
            gtkspell.get_from_text_view(textView).set_language(self.lang)
        except Exception, e:
            print str(e)
            self.error(_('Error applying Spell to input (%s)') % e, False)
            return False
        
    def check(self):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> (True, 'some message')
        else -> (False, 'error message')
        '''
        if ERROR != '':
            return (False, ERROR)
            
        return (True, 'Ok')

    def newConversationWindow(self, conversationmanager, conversation, win):
        textView = conversation.ui.input.input  #inputwidget.textview
        self.setSpell(textView)
        
    def closeConversationWindow(self, conversationManager, conversation, win):
        textView = conversation.ui.input.input  #inputwidget.textview
        try:
            gtkspell.get_from_text_view(textView).detach()
        except:
            pass

    def configure(self):
        '''display a configuration dialog'''
        # name, optionType, label, description, value, options
        
        status, langs = commands.getstatusoutput('enchant-lsmod -list-dicts')
        if status == 0:
            langs = sorted(list(set(re.sub(' \(.*?\)','', langs).split('\n'))))
        else:
            self.error(_("Error getting dictionaries list"))
            langs = []

        if not langs:
            self.error(_("No dictionaries found."))
            return
        
        l = []
        l.append(Plugin.Option('lang', list, _('Default language'),
            _('Set the default language'),
            self.config.getPluginValue(self.name, 'lang', ''), langs))
        
        response = Plugin.ConfigWindow(_('Spell configuration'), l).run()
        if response != None and response.has_key('lang'):
            self.config.setPluginValue(self.name, 'lang',
                str(response['lang'].value))
        
        self.lang = self.config.getPluginValue(self.name, 'lang', '')
        
        self.applyAllConv(self.setLang)
        
        return True
