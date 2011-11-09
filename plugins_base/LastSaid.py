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

VERSION = '0.9.1'

import os
import emesenelib
import time
from Plugin import Plugin, Option, ConfigWindow
from datetime import datetime
from string import Template

#From LogConversation which took from aaPluginDownloader =)
try:
    import paths
    CONFIG_PATH = paths.CONFIG_DIR
except:
    import emesenelib.common
    from emesenecommon import PATH 
    CONFIG_PATH = PATH.CONFIG_DIR

DEFAULT_LINES = 8
DEFAULT_TS = 'None'
DEFAULT_SS = 'None'
DEFAULT_GT = '0'
GREY = "#909090"

# Link between what you see in config and
# what is needed to do substitutions
TIMESTYLES = {
    'None' : '',
    '[hour:minute]' : '[$hour:$minute] ',
    '(day/month)' : '($day/$month) ',
    '(day/month/year)' : '($day/$month/$year) ',
    '[day/month - hour:minute]' : '[$day/$month - $hour:$minute] '
}

SEPARATORSTYLES = {
    'None': '',
    '---' : '--------------------------------',
    '===' : '================================',
    '+++' : '++++++++++++++++++++++++++++++++',
    '***' : '********************************',
    '###' : '################################',
    '@@@' : '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
    '~~~' : '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
    '___' : '________________________________'
}


class MainClass(Plugin):

    description = _('Prints the last lines of conversation with a contact.')
    authors = {
        'Astu': 'astu88 at gmail dot com',
        'Marco Trevisan (Treviño)': 'mail at 3v1n0 dot net',
        'Nelson Dai': 'nelson at csie dot us'
        }
    website = 'http://emesene.org/smf/index.php/topic,466.0.html'
    displayName = _('Last said')
    name = 'LastSaid'

    def __init__(self, controller, msn):
        '''Constructor'''
        Plugin.__init__(self, controller, msn)

        self.description = _('Prints the last lines of conversation with a contact.')
        self.authors = {
            'Astu': 'astu88 at gmail dot com',
            'Marco Trevisan (Treviño)': 'mail at 3v1n0 dot net',
            'Nelson Dai': 'nelson at csie dot us'
            }
        self.website = 'http://emesene.org/smf/index.php/topic,466.0.html'
        self.displayName = _('Last said')
        self.name = 'LastSaid'
        
        self.function_list = {
            "Logger" : self.printLast_Logger, 
            "LogConversation" : self.printLast_LogConversation
        }

        self.used_plugin = ''
        self.lines = DEFAULT_LINES
        self.timestyle = DEFAULT_TS
        self.separatorstyle = DEFAULT_SS
        self.grey_text = DEFAULT_GT
        self.logger = None
        self.convmanagerId = 0

        self.controller = controller
        self.config = self.controller.config
        self.config.readPluginConfig(self.name)
        self.enabled = False


    def printLast(self, conversationManager, conversation, window):
        '''Prints last said lines and separator'''
        
        if not self.enabled:
            return

        self.members = conversation.getMembers()
        if len(self.members) != 1:
            return    # This is to avoid multichat
        
        # Call to the  proper function that prints logs
        self.function_list[self.used_plugin](conversation)
        
        # Printing separator
        if self.separatorstyle != DEFAULT_SS:
            separator = \
'<p><span style="font-weight: bold; color: #000000; text-align: center;">' + \
                        SEPARATORSTYLES[self.separatorstyle] + '</span></p>'
            conversation.ui.textview.display_html(separator)
        conversation.ui.textview.scrollLater()


################################################################################
    def printLast_Logger(self, conversation):
        '''Prints in the chat window the last said lines of conversation
            using Logger plugin'''

        # Added by Nelson, for group conversation history.
        previous_speaker = ''
        current_speaker = ''
        type = ''

        last = self.logger.get_last_conversation(self.members[0], self.lines)
        last.reverse()

        my_nick = emesenelib.common.unescape(self.controller.msn.nick)
        # Note that friend_nick works also with aliases
        friend_nick = emesenelib.common.unescape(
                      self.msn.contactManager.getContactNameToDisplay(\
                      self.members[0]))

        for (timestamp, n, msg) in last:
            if n == self.controller.msn.user:
                current_speaker = my_nick
                type = 'incoming'
            else:
                current_speaker = friend_nick
                type = 'outgoing'

            # Added by Nelson, group conversation history.
            msg_text = msg.split("\r\n")[2]
            msg_format = msg.split("\r\n")[0]


            if self.timestyle == DEFAULT_TS:
                # Message uses conversation layout
                if previous_speaker != current_speaker:
                    previous_speaker = current_speaker
                    message = self.controller.conversationLayoutManager.layout(\
                        current_speaker, msg_text, \
                        conversation.parseFormat('', msg_format), \
                        conversation, type, timestamp)
                else:
                    message = self.controller.conversationLayoutManager.layout(\
                        current_speaker, msg_text, \
                        conversation.parseFormat('', msg_format), \
                        conversation, 'consecutive_' + type, timestamp)

                if self.grey_text:
                    message = greify(message) # Message is now grey
                    
                try:
                    conversation.ui.textview.display_html(\
                        message.encode('ascii', 'xmlcharrefreplace'))
                except Exception, e:
                    print '[LastSaid] error trying to display "' + message + '"'
                    print e
            else:
                # Message doesn't use layout to allow timestyles
                dt = datetime.fromtimestamp(timestamp)
                msg_time = self.time_template.substitute(
                    year = dt.year,
                    month = dt.month,
                    day = dt.day,
                    hour = dt.hour,
                    minute = dt.minute)
                    
                if previous_speaker != current_speaker:
                    previous_speaker = current_speaker
                    message = current_speaker + ' says:\n    ' \
                        + msg_time + msg_text
                else:
                    message = '    ' + msg_time + msg_text
                conversation.appendOutputText(None, message, 'information')
            conversation.ui.textview.scrollLater()

################################################################################
    def printLast_LogConversation(self, conversation):
        '''Prints in the chat window the last said lines of conversation
            using LogConversation plugin'''

        #We would save logs in : 
        #paths.CONFIG_DIR join controller.config.getCurrentUser() join html_logs
        logDir = os.path.join(CONFIG_PATH, \
            self.controller.config.getCurrentUser()) 
        #this dir exist!
        month_year = time.strftime('%B_%Y', time.localtime())
        logDir = os.path.join(logDir, 'html_logs', month_year)
        
        #Create the log FileName
        logFileName = os.path.join(logDir, self.members[0] + '.html')
            
        if not os.path.exists(logFileName):
            return  #If logfile doesn't exist then there's nothing to show
        
        logFile = open(logFileName, 'r')
        logFile_lines = logFile.readlines()

        # We have to read conversation lines end exclude others
        # Conversation lines have a <!----> before to recognize them
        # We read from bottom to up and stop when we got enough lines
        i = 1
        conversation_lines_to_print = []
        while (len(conversation_lines_to_print) < self.lines) \
            and (i < (len(logFile_lines)-6)):
            if logFile_lines[-i].startswith('<!---->'):
                conversation_lines_to_print.append(logFile_lines[-i])
            i += 1
        
        conversation_lines_to_print.reverse()
        for line in conversation_lines_to_print:
            if self.grey_text:
                line = greify(line) # The line is now grey
            conversation.ui.textview.display_html(line)
        
        conversation.ui.textview.scrollLater()
        logFile.close()


################################################################################
    def start(self):
        self.check() # To build the available plugins list 
        self.enabled = True
                
        if len(self.available_log_plugins) == 1: 
            # only 1 plugin available, so we automatically set this option
            self.used_plugin = self.available_log_plugins[0]
            self.config.setPluginValue(self.name, 'used_plugin', \
                self.used_plugin)
        else:
             self.used_plugin = self.config.getPluginValue(self.name, \
                'used_plugin', self.available_log_plugins[0])
        
        self.lines = int(self.config.getPluginValue(self.name, \
            'lines', DEFAULT_LINES))
        self.timestyle = self.config.getPluginValue(self.name, \
            'timestyle', DEFAULT_TS)
        self.separatorstyle = self.config.getPluginValue(self.name, \
            'separatorstyle', DEFAULT_SS)
        self.grey_text = bool(int(self.config.getPluginValue(self.name, \
            'grey_text', DEFAULT_GT)))     

        self.time_template = Template(TIMESTYLES[self.timestyle])       

        self.logger = self.controller.pluginManager.getPlugin("Logger")

        self.convmanagerId = self.controller.conversationManager.connect(\
            'new-conversation-ui', self.printLast)

    def stop(self):
        self.enabled = False
        if self.convmanagerId:
            self.controller.conversationManager.disconnect(self.convmanagerId)
            self.convmanagerId = 0

    def check(self):
        '''Logger plugin OR LogConversation plugins needed'''
        self.available_log_plugins = []
        log_plugins = { 
            "Logger" : self.controller.pluginManager.getPlugin("Logger"), 
            "LogConversation" : self.controller.pluginManager.getPlugin(\
                "LogConversation")
            }
        # Check which plugins are available
        for plugin in log_plugins:
            if log_plugins[plugin] is None or not log_plugins[plugin].enabled:
                print "[LastSaid] Logging plugin '" + plugin + "' NOT available."
            else:
                self.available_log_plugins.append(plugin)
                print "[LastSaid] Logging plugin '" + plugin + "' available."
     
        if len(self.available_log_plugins) == 0:
            return (False, _('''No logging plugin found. Enable Logger plugin \
            or LogConversation plugin'''))

        return (True, 'Ok')

    def configure(self):
        self.check() # To build the available plugins list 
        
        if self.available_log_plugins:
            self.used_plugin = self.config.getPluginValue(self.name, \
                'used_plugin', self.available_log_plugins[0])
        self.lines = int(self.config.getPluginValue(self.name, \
            'lines', DEFAULT_LINES))
        self.timestyle = self.config.getPluginValue(self.name, \
            'timestyle', DEFAULT_TS)
        self.separatorstyle = self.config.getPluginValue(self.name, \
            'separatorstyle', DEFAULT_SS)
        self.grey_text = bool(int(self.config.getPluginValue(self.name, \
            'grey_text', DEFAULT_GT)))

        opt = []
        if len(self.available_log_plugins) > 1:
            opt.append(Option('used_plugin', list, _('Logging plugin to use:'), \
                _('Logging plugin used to retrieve old conversations'), \
                self.used_plugin, self.available_log_plugins))
        elif len(self.available_log_plugins) == 1: 
            # only 1 plugin available, so we automatically set this option
            self.used_plugin = self.available_log_plugins[0]
            self.config.setPluginValue(self.name, 'used_plugin', \
                self.used_plugin)
            
        opt.append(Option('lines', str, _('Lines to print:'), \
            _('Number of conversation lines to print'), \
            self.lines))
            
        if "Logger" in self.available_log_plugins:
            opt.append(Option('timestyle', list, _('Time display style:'), \
                _('Style of time displayed next to messages'), \
                self.timestyle, TIMESTYLES.keys()))

        opt.append(Option('separatorstyle', list, _('Separator display style:'), \
            _('Style of separator displayed next to message histories'), \
            self.separatorstyle, SEPARATORSTYLES.keys()))
            
        opt.append(Option('grey_text', bool, _('Grey text (experimental)'), \
            _('Write message history in grey'), self.grey_text))

        result = ConfigWindow(_('Last Said configuration'), opt ).run()
        if result:
        
            if result.has_key('used_plugin'):
                self.used_plugin = result['used_plugin'].value
                self.config.setPluginValue(self.name, 'used_plugin', \
                    self.used_plugin)
                    
            if result.has_key('lines'):
                try:
                    self.lines = int(result['lines'].value)
                except ValueError: # only numbers here
                    self.lines = DEFAULT_LINES
                self.config.setPluginValue(self.name, 'lines', self.lines)

            if result.has_key('timestyle'):
                self.timestyle = result['timestyle'].value
                self.config.setPluginValue(self.name, 'timestyle', \
                    self.timestyle)
                # Update time template
                self.time_template = Template(TIMESTYLES[self.timestyle])

            if result.has_key('separatorstyle'):
                self.separatorstyle = result['separatorstyle'].value
                self.config.setPluginValue(self.name, 'separatorstyle', \
                    self.separatorstyle)

            if result.has_key('grey_text'):
                self.grey_text = result['grey_text'].value
                self.config.setPluginValue(self.name, 'grey_text', \
                    str(int(self.grey_text)))


################################################################################
def greify(s):
    ''' Makes the s string grey '''
    ends = []
    while s.find("color:") != -1:
        beginning = s.find("color:")
        
        end1 = s.find(' ', beginning+7)
        if  end1 != -1: 
            ends.append(end1)
        
        end2 = s.find(';', beginning+7)
        if  end2 != -1: 
            ends.append(end2)
        
        end3 = s.find('"', beginning+7)
        if  end3 != -1: 
            ends.append(end3)

        if len(ends) == 0:
            break
        else:
            end = min(ends)
            ends = []
            s = s[:beginning] + s[end:]
        
    return '<span style="color:' + GREY + '">' + s + '</span>'

