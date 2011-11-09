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
import re
import time

import paths
import emesenelib.common
from Parser import ConversationDataType


tagRe = re.compile('%(.*?)%')

class ConversationLayoutManager(object):
    ''' This class handles the conversation theming system '''

    def __init__(self, controller):
        self.infos = {}
        self.theme = {}
        self.reset()
        self.setDefault()
        self.controller = controller
        self.config = controller.config
        self.unifiedParser = controller.unifiedParser

    def reset(self):
        ''' Resets the theme '''
        self.infos['name'] = ''
        self.infos['description'] = ''
        self.infos['author'] = ''
        self.infos['website'] = ''
        self.theme['incoming'] = ''
        self.theme['consecutive_incoming'] = ''
        self.theme['offline_incoming'] = ''
        self.theme['outgoing'] = ''
        self.theme['consecutive_outgoing'] = ''
        self.theme['information'] = ''
        self.theme['error'] = ''

    def setValue(self, key, value):
        ''' Sets a key according to the given value '''
        if key in self.theme.keys():
            self.theme[key] = value
        elif key in self.infos.keys():
            self.infos[key] = value
        else:
            emesenelib.common.debug(key + ' is not a valid property for a conversation layout !')

    def resolveValue(self):
        ''' Resolve shortcut like "incoming=outgoing" '''
        for key, value in self.theme.iteritems():
            if value in self.theme.keys():
                self.theme[key] = self.theme[value]

    def setDefault(self):
        ''' Sets the default theme (you should use that when a load fails) '''
        self.theme['incoming'] = '<span style="font-weight: bold;">%nick% says :</span><br/>    [%h%:%m%:%s%] %formattedmessage%<br/>'
        self.theme['consecutive_incoming'] = '    [%h%:%m%:%s%] %formattedmessage%<br/>'
        self.theme['offline_incoming'] = 'incoming'
        self.theme['outgoing'] = 'incoming'
        self.theme['consecutive_outgoing'] = 'consecutive_incoming'
        self.theme['information'] = '    [%h%:%m%:%s%] <span style="font-weight: bold;">%message%</span><br/>'
        self.theme['error'] = '    [%h%:%m%:%s%] <span style="font-weight: bold; color: #FF0000;">%message%</span><br/>'
        self.resolveValue()

    def load(self, name):
        '''Loads a theme, return true on success, false otherwise.
        It seeks the theme in config dir, and then in app dir.
        If the loads fails, the old layout is restored'''
        def doLoad(filename):
            self.reset()
            themefile = None
            try:
                themefile = open(filename, 'r')
                themestring = themefile.read()

                for i in themestring.splitlines():
                    i = i.lstrip()
                    if i != '' and not i.startswith('#'):
                        delim = i.find('=')
                        key = i[:delim].lower()
                        value = i[delim+1:]
                        self.setValue(key, value)

                self.resolveValue()
                themefile.close()

                if not self.isValid():
                    return False
                else:
                    return True

            except:
                if themefile:
                    themefile.close()
                return False

        oldInfos = self.infos
        oldTheme = self.theme

        filename = paths.CONVTHEMES_HOME_PATH + os.sep + name + os.sep + 'theme'
        if not os.path.exists(filename):
            filename = paths.CONVTHEMES_SYSTEM_WIDE_PATH + os.sep + name + \
                os.sep + 'theme'

        if os.path.exists(filename):
            success = doLoad(filename)
        else:
            success = False

        if not success:
            self.infos = oldInfos
            self.theme = oldTheme

        return success

    def isValid(self):
        ''' Checks if the theme is valid '''
        for value in self.theme.values():
            if value == None or value in self.theme.keys():
                return False
        return True

    def listAvailableThemes(self):
        ''' Lists all available and valid themes and return a list '''
        conversationLayout = ConversationLayoutManager(self.controller)
        validThemesList = []

        try:
            homethemes = os.listdir(paths.CONVTHEMES_HOME_PATH)
        except OSError:
            homethemes = []
        try:
            globalthemes = os.listdir(paths.CONVTHEMES_SYSTEM_WIDE_PATH)
        except OSError:
            globalthemes = []

        for currentTheme in homethemes + globalthemes:
            if conversationLayout.load(currentTheme):
                validThemesList.append(currentTheme)

        return validThemesList

    def layout(self, username, message, format, conversation, type, timestamp, \
               ink=False, p4c=False):
        ''' Returns HTML code according to the the current theme '''
        if type not in self.theme.keys():
            return ''

        switchboard = conversation.switchboard

        if not ink:
            messageDataObject = self.unifiedParser.getParser(message, ConversationDataType)
            messageDataObject.setConversation(conversation)
            messageDataObject.setUser(username)

            message = messageDataObject.get(smileys=self.config.user['parseSmilies'])

            message = message.replace('\n', '<br/>')
        else:
            if os.name == 'posix':
                message = '<img src="file://%s" alt="Ink message" />' % message
            else:
                message = '<img src="file://localhost/%s" alt="Ink message" />' % message

        arguments = {}

        # Fills nick
        arguments['nick'] = ''
        if username:
            if username.find("@") == -1: #if it's not an email
                arguments['nick'] = username
            else: #may catch nicknames with the char "@"
                arguments['nick'] = self.controller.msn.getUserDisplayName(username)

        # prevent lowercasing nick when an oim is received
        #if type == 'offline_incoming' and username.find("@") != -1:
        #    arguments['nick'] = username

        # Fills email
        arguments['email'] = username
        
        # Fills message
        arguments['message'] = message

        # Fills avatar
        arguments['avatar'] = ''
        if type == 'outgoing' or type == 'consecutive_outgoing':
            arguments['avatar'] = self.controller.avatar.getImagePath()
        elif type == 'incoming' or type == 'consecutive_incoming':
            arguments['avatar'] = self.controller.msn.cacheDir + os.sep + \
                username.split('@')[0] + '.tmp'

        # Fills (?) timestamp
        arguments['timestamp'] = timestamp

        # Layout
        if format is None:
            parser = LayoutTagParser(self, arguments, self.getCssStyle(), type)
        else:
            parser = LayoutTagParser(self, arguments, format, type)

        result = tagRe.sub(parser.sub, self.theme[type])

        return '<span><span style="font-size: %spt;">%s</span></span>' % \
               (self.config.user['fontSize'], result)

    def getPreview(self):
        ''' Returns a preview of the layout '''
        preview = ''
        arguments = {}
        userStyle = self.getCssStyle()

        # Fills arguments with faked ones
        # First message
        arguments['nick'] = self.controller.msn.nick
        arguments['email'] = 'youremail@hotmail.com'
        arguments['message'] = _('This is an outgoing message')
        arguments['avatar'] = self.controller.avatar.getImagePath()
        arguments['timestamp'] = time.time()
        parser = LayoutTagParser(self, arguments, userStyle, 'outgoing')
        preview += tagRe.sub(parser.sub, self.theme['outgoing'])

        # Second message
        arguments['message'] = _('This is a consecutive outgoing message')
        parser = LayoutTagParser(self, arguments, userStyle, 'consecutive_outgoing')
        preview += tagRe.sub(parser.sub, self.theme['consecutive_outgoing'])

        # Third message
        arguments['nick'] = 'John Doe'
        arguments['email'] = 'john_doe@hotmail.com'
        arguments['message'] = _('This is an incoming message')
        # TODO : have an example picture
        arguments['avatar'] = self.controller.avatar.getImagePath()
        parser = LayoutTagParser(self, arguments, None, 'incoming')
        preview += tagRe.sub(parser.sub, self.theme['incoming'])

        # Fourth message
        arguments['message'] = _('This is a consecutive incoming message')
        parser = LayoutTagParser(self, arguments, None, 'consecutive_incoming')
        preview += tagRe.sub(parser.sub, self.theme['consecutive_incoming'])

        # Information message
        arguments['message'] = _('This is an information message')
        parser = LayoutTagParser(self, arguments, None, 'information')
        preview += tagRe.sub(parser.sub, self.theme['information'])

        # Fourth message
        arguments['message'] = _('This is an error message')
        parser = LayoutTagParser(self, arguments, None, 'error')
        preview += tagRe.sub(parser.sub, self.theme['error'])

        return '<span><span style="font-size: %spt;">%s</span></span>' % \
               (self.config.user['fontSize'], preview)

    def getCssStyle(self):
        '''return the css style of the user'''

        style = ''

        if self.config.user['fontBold']:
            style += 'font-weight: bold;'

        if self.config.user['fontItalic']:
            style += 'font-style: italic;'

        if self.config.user['fontUnderline']:
            if self.config.user['fontStrike']:
                style += 'text-decoration: underline line-through;'
            else:
                style += 'text-decoration: underline;'
        elif self.config.user['fontStrike']:
            style += 'text-decoration: line-through;'

        style += 'font-size: ' + str(self.config.user['fontSize']) + 'pt;'
        style += 'color: ' + str(self.config.user['fontColor']) + ';'
        style += 'font-family: ' + str(self.config.user['fontFace']) + ';'

        return style

    def getName(self):
        return self.infos['name']

    def getDescription(self):
        return self.infos['description']

    def getAuthor(self):
        return self.infos['author']

    def getWebsite(self):
        return self.infos['website']

class LayoutTagParser:
    '''thread-safe environment to parse layout tags'''

    def __init__(self, parent, arguments, format, type):
        self.parent = parent
        self.arguments = arguments
        self.format = format
        self.type = type

        self.controller = parent.controller
        self.config = parent.controller.config
        self.unifiedParser = parent.unifiedParser

    def sub(self, data):
        ''' Called by re.sub for each tag found '''
        tag = data.groups()[0].lower()

        if tag == 'nick':
            nick = self.arguments['nick']

            nickDataObject = self.unifiedParser.getParser(nick, ConversationDataType)
            nick = nickDataObject.get(urls=False, smileys=self.config.user['parseSmilies'])

            return nick

        elif tag == 'message' or \
             (self.config.user['disableFormat'] and tag == 'formattedmessage'):
            return self.arguments['message']

        elif tag == 'formattedmessage':
            message = self.arguments['message']
            return '<span style="%s">%s</span>' % (self.format, message)

        elif tag == 'h':
            return time.strftime('%H', time.localtime(self.arguments['timestamp']))

        elif tag == 'm':
            return time.strftime('%M', time.localtime(self.arguments['timestamp']))

        elif tag == 's':
            return time.strftime('%S', time.localtime(self.arguments['timestamp']))

        elif tag == 'date':
            return time.strftime('%Ex', time.localtime(self.arguments['timestamp']))

        elif tag == 'avatar':
            return '<img src="file://' + self.arguments['avatar'] + '"/>'

        elif tag == 'says':
            return _('says')
            
        elif tag == 'said':
            return _('said')
          
        elif tag == 'offline':
            return _('Offline message')

        elif tag == 'email':
            return self.arguments['email']

        else:
            return data.groups()[0]

    def extractArgument(self, tag):
        ''' Retrieves arguments from a tag '''
        start = tag.find('(')+1
        end = tag.find(')')
        arglist = tag[start:end].replace(' ', '')
        return arglist.split(',')

