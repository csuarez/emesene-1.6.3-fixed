#   This file is part of emesene.
#
#    Eval plugin is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Eval plugin is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

#Changelog:
#0.5.1:
#-Don't log "conversation started/closed" if just open an close conversation
#-Fix a bug at stop of the plugin

#0.5:
#-Log all offline messages
#-Fixed user menu for the new logs directories structure (dates)
#-A lot of refactor

#0.4.8:
#-Fix Back consinstency for PyGtk in setting tooltips of a ToolItem

#0.4.7.1:
#-Try to solve ('Exception importing LogConversation\nNo module named paths', 'PluginManager') in Opensuse 10.3 64 bit
# with paths importing code from aaPluginDownloader

#0.4.7:
#-Fix bug: Controller has not attribute debug.

#0.4.6:
#-Received custom emoticons are logged with the string in fields data in
# the tag <object type="application/x-emesene-emoticon" class="%s" data="%s"></object>
#-With group conversation logger change automatically in the right file
# where to log: emailRemote1-emailRemote2... .html

#0.1 -> 0.4.5:
#-Store in file paths.CONFIG_DIR join controller.config.getCurrentUser() join html_logs join emailRemote
#-utf-8 coding of html logs
#-Added a button to conversation toolbar to view logs in current browser
#Logging Capability:
#-Send/received messages
#-OfflineReceived messages
#-File Transfers acceptation

VERSION = '0.4.8'
import Plugin
import os
import time
import emesenelib
import desktop
import gtk
import gobject

#From aaPluginDownloader
try:
    import paths
    CONFIG_PATH = paths.CONFIG_DIR
except:
    import emesenelib.common
    from emesenecommon import PATH
    CONFIG_PATH = PATH.CONFIG_DIR

class MyLogger():
    '''Logger able to log in a file the specific conversation'''

    def __init__(self,controller,conversation,MainClass,addButton = True):
        '''Save the identifier of this conversation and begin to log message'''
        self.controller = controller
        self.mainClass = MainClass
        self.stopped = False

        #This identifier enable the check of members change!
        self.members = conversation.getMembers()
        self.idMyLog = self.members[0]
        for mem in self.members[1:len(self.members)]:
            self.idMyLog = self.idMyLog + '-' + mem
        self.lastUserName = ''

        #The identifier of this conversation is the id of conversation
        self.idConv = id(conversation)
        self.conversation = conversation

        #We would save logs in :
        self.logDir = os.path.join(self.mainClass.logsDir, \
			time.strftime('%B_%Y', time.localtime(time.time()))) #This is created at the first run

        #If the log dir not exist create it
        if not os.path.exists(self.logDir):
            try:
                os.mkdir(self.logDir)
            except: #in case we can't create the dir with the date
                self.logDir = self.mainClass.logsDir 

        #Create the log FileName
        self.logFileName = os.path.join(self.logDir, \
            self.idMyLog + '.html')

        #Exist already?
        if os.path.exists(self.logFileName):
            self.logFile = open(self.logFileName,'r+')
            #Ok we have to delete the last string if it is a </body></html>
            self.logFile.seek(-15,2)
            lastLine = self.logFile.readline()
            if lastLine.find('</html>') != -1:
                #Ok, last time we closed the file in the right way
                #let seek  at the beginning of the line to overwrite
                #(15 chars with the new line).
                self.logFile.seek(-15,2)
            else:
                #Last time we have not closed the file in the right way
                #We put a br..
                self.logFile.seek(0,2)
                self.logFile.write('\n<span><br/></span>\n')
        else:
            self.logFile = open(self.logFileName,'w')
            #Head of the document
            self.logFile.write('<html>\n')
            self.logFile.write('<head>\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />\n')
            convwith = _('Conversation with %s') % self.idMyLog
            self.logFile.write('<title>'+ convwith +'</title>\n</head>\n<body>\n')

        self.modified = False

        #For file send and receive logging
        self.p2p = controller.msn.p2p[conversation.switchboard.firstUser]

        #Connect the sending and receiving logger
        self.sendmessageId = self.controller.conversationManager.connect( \
                                    'send-message', self.logSendMessage)
        self.receivemessageId = self.controller.conversationManager.connect( \
                             'receive-message', self.logReceivedMessage)
        self.fileTransferId = self.p2p.connect('file-transfer-accepted',\
                                                   self.logFileTransfer)
        #Every time the conversationManager send a close-conversation-ui
        #execute stop
        self.closeUIId = self.controller.conversationManager.connect(\
                                     'close-conversation-ui', self.stop)

        if addButton:
            #Add a button to the toolbar of this conversation:
            self.logButton = gtk.ToolButton(label=_('Logs'))
            self.logButton.set_stock_id(gtk.STOCK_DND)
            if self.controller.theme.getImage('log'):
                imagelog = gtk.Image()
                imagelog.set_from_pixbuf(self.controller.theme.getImage('log'))
                imagelog.show()
                self.logButton.set_icon_widget(imagelog)
            self.logButton.connect('clicked', self.mainClass.viewLog, self.logFileName)

            self.logButton.set_tooltip_text(_('View the logs of this conversation'))

            conversation.ui.input.toolbar.insert(gtk.SeparatorToolItem(), -1)
            conversation.ui.input.toolbar.insert(self.logButton, -1)
            conversation.ui.input.toolbar.show_all()
            
    def start_conv_log(self):
        #First string
        started = _('Started at: ') 
        self.logFile.write('<hr align=\"left\" />\n')
        self.logFile.write('\n<span><span style=\"font-size: 10pt;font-weight: bold;\"> ' + started)
        self.logFile.write(time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(time.time())))
        self.logFile.write('.<br/></span></span>\n')
        self.logFile.flush()
        self.modified = True

    def logSendMessage(self, obj, conversation, message):
        '''message is a list of string'''
        idThisLog = id(conversation)

        #Log this message if the id match
        if idThisLog == self.idConv:
            if not self.modified:
                self.start_conv_log()
            #Members have changed??
            members = conversation.getMembers()
            mbThisLog = members[0]
            for mem in members[1:len(members)]:
                mbThisLog = mbThisLog + '-' + mem

            if mbThisLog != self.idMyLog:
                self.stop()
                self.__init__(self.controller,self.conversation,self.mainClass,False)
                self.mainClass.activeLoggers.append(self)

            self.appendOutputText(conversation.getUser(), message, 'outgoing')

    def logReceivedMessage(self, cm, conversation, mail, nick, message, format, charset, p4c):
        idThisLog = id(conversation)

        #Log this message if the id match
        if idThisLog == self.idConv:
            if not self.modified:
                self.start_conv_log()
            #Members have changed??
            members = conversation.getMembers()
            mbThisLog = members[0]
            for mem in members[1:len(members)]:
                mbThisLog = mbThisLog + '-' + mem

            if mbThisLog != self.idMyLog:
                self.stop()
                self.__init__(self.controller,self.conversation,self.mainClass,False)
                self.mainClass.activeLoggers.append(self)

            self.appendOutputText(mail, message, 'incoming', \
                conversation.parseFormat(mail, format))

    def logFileTransfer(self, p2p, session, context, sender):

        mail = sender
        #self.mainClass.debug( '[LogConv] Sender of file: %s' % sender)

        self.members = self.conversation.getMembers()
        for mem in self.members:
            if (mail == mem) or (mail == 'Me'):
                if not self.modified:
                    self.start_conv_log()
                self.appendOutputText(None, \
                        _('Starting transfer of %s') % context.filename, \
                        'information')
                break

    #From in Conversation.py with another end
    def appendOutputText(self, username, text, type, style = None, timestamp = None):
        '''append the given text to the outputFile type is in[incoming:outgoing]'''
        if not self.modified:
            self.start_conv_log()
        if type.startswith('ink_'):
            type = type[4:]
            ink = True
        else:
            ink = False

        if username == self.conversation.switchboard.user:
            nick = emesenelib.common.escape(self.controller.msn.nick)
        elif username != None:
            nick = emesenelib.common.escape( \
                self.controller.msn.getUserDisplayName(username))
        else:
            nick = ''

        if timestamp is None:
            timestamp = time.time()

        if self.lastUserName == username:
            if type != "offline_incoming":
                type = "consecutive_"+type
            displayedText = self.controller.conversationLayoutManager.layout(\
                username, text, style, self.conversation, type, timestamp, ink)
        else:
            self.lastUserName = username
            displayedText = self.controller.conversationLayoutManager.layout(\
                username, text, style, self.conversation, type, timestamp, ink)

        #erase custom emoticons
        displayedText = self.fromCustomEmoticonsToText(displayedText)
        self.logFile.write('<!---->' + displayedText)
        self.logFile.write('\n')
        self.logFile.flush()

    def stop(self, conversationManager = None, conversation = None, window = None):
        '''Close this logger if the id of the conversation closed match with self.idMyLog'''
        if self.stopped:
            return

        if(conversationManager != None):
            idThisLog = id(conversation)
        else:
            idThisLog = self.idConv

        #Close this logger if the id match
        if idThisLog == self.idConv:
            #Last String
            if self.modified:
                closed = _('Closed at: ')
                self.logFile.write('\n<span><span style=\"font-size: 10pt;font-weight: bold;\">'+ closed)
                self.logFile.write(time.strftime('%a, %d %b %Y %H:%M:%S',time.localtime(time.time())))
                self.logFile.write('.<br/></span></span>\n')
                #Tail of the document
                self.logFile.write('\n</body></html>\n')

            self.logFile.close()

            self.controller.conversationManager.disconnect(self.sendmessageId)
            self.controller.conversationManager.disconnect(self.receivemessageId)
            self.controller.conversationManager.disconnect(self.closeUIId)
            self.p2p.disconnect(self.fileTransferId)
            self.stopped = True
            self.mainClass.activeLoggers.remove(self)

    def fromCustomEmoticonsToText(self,message):

        #This is the string to find and to substitute with the field data
        #'<object type="application/x-emesene-emoticon" class="%s" data="%s"></object>'
        modified = False

        firstInstance = message.find('<object')
        #First part of the string where we don't want to see (there are
        # object tags not custom emoticons)
        offset = 0

        if firstInstance < 0:
            #No objects in here.
            return message

        while firstInstance >= 0:
            firstInstance += offset
            #find the end of the tag..
            endTag = message[offset:].find('/object>')
            if endTag < 0:
                #Error parsing.. leve what there is
                return message

            endTag = offset + endTag + len('/object>')

            objectTag = message[firstInstance:endTag]
            fields = objectTag.split('"')

            #is a type application/x-emesene-emoticon??
            foundEmoticon = False
            nextIsData = False
            dataField = ''
            for field in fields:
                if nextIsData:
                    dataField = field
                    nextIsData = False
                if field == 'application/x-emesene-emoticon':
                    foundEmoticon = True
                if field.find('data=') >= 0:
                    nextIsData = True

            if foundEmoticon:
                message1 = message[:firstInstance]
                message2 = message[endTag:]
                message = message1 + dataField + message2
            else:
                offset = endTag

            firstInstance = message[offset:].find('<object')

        return message


class MainClass(Plugin.Plugin):
    '''Main plugin class'''

    description = _('Log every session with friendEmail in:\n' + \
      '~/.config/emesene1.0/<address>/html_logs/month_year/friendEmail.html')
    authors = { 'Marramao' : 'maramaopercheseimorto@gmail.com', \
                'arielj' : 'arieljuod@gmail.com' }
    website = 'emesene.org'
    displayName = _('Conversation Logger')
    name = 'LogConversation'

    def __init__(self, controller, msn):
        '''Contructor'''
        Plugin.Plugin.__init__(self, controller, msn)

        self.controller = controller
        self.config = controller.config
        self.config.readPluginConfig(self.name)

        self.activeLoggers = []

    def start(self):
        '''start the plugin'''
        self.convmanagerId = self.controller.conversationManager.connect( \
                'new-conversation-ui', self.connectLogger)
        self.menuItemId = self.controller.connect("usermenu-item-add", \
                                                  self.add_usermenu_item)
        self.offlineMessages = self.connect('offline-message-received', \
                                              self.logOffReceivedMessage)

        self.logsDir = os.path.join(CONFIG_PATH, \
                 self.controller.config.getCurrentUser(), 'html_logs')

        if not os.path.isdir(self.logsDir):
            os.mkdir(self.logsDir)

        self.enabled = True

    def connectLogger (self, conversationManager, conversation, window):
        self.activeLoggers.append(MyLogger(self.controller,conversation,self))

    def logOffReceivedMessage(self, msnp, oim):
        '''used when a new conversation is opened by an offline message'''
        def check(oim):
            user, date, message = oim
            mail = user['addr']
            result = self.controller.conversationManager.getOpenConversation(mail)
            
            if result is not None:
                conversation = result[1]
                for logger in self.activeLoggers:
                    if logger.conversation == conversation:

                        try:
                            logger.appendOutputText(mail, message, 'offline_incoming', \
                                time.mktime(date))
                            return False
                        except:
                            pass
                return True
            return True

        gobject.timeout_add(500, check, oim)

    def add_usermenu_item(self, controller, userMenu):
        dates = os.listdir(self.logsDir)
        logMenuItem = userMenu.newImageMenuItem( _( "Logs of this user" ),
                                                           gtk.STOCK_DND )
        if self.controller.theme.getImage('log'):
            imagelog = gtk.Image()
            imagelog.set_from_pixbuf(self.controller.theme.getImage('log'))
            imagelog.show()
            logMenuItem.set_icon_widget(imagelog)

        submenu = gtk.Menu()
        logsAvailables = False
        for date in dates:
            logFileName = os.path.join(self.logsDir, date, \
                                       userMenu.user.email + '.html')
            if os.path.exists(logFileName):
                newMenuItem = gtk.MenuItem(label=date)
                newMenuItem.connect( 'activate', self.viewLog, logFileName )
                submenu.append(newMenuItem)
                logsAvailables = True

        if logsAvailables:
            logMenuItem.set_submenu(submenu)
            userMenu.viewMenu.add(logMenuItem)
            logMenuItem.show_all()

    def viewLog(self, menuitem, logFileName):
        desktop.open(logFileName)

    def stop(self):
        '''stop the plugin'''
        self.controller.conversationManager.disconnect(self.convmanagerId)
        self.controller.disconnect(self.menuItemId)
        self.disconnect(self.offlineMessages)

        for myLogger in self.activeLoggers:
            myLogger.stop()
        
        self.enabled = False

    def check(self):
        return (True, 'Ok')
