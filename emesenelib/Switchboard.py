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
import time
import urllib
import gobject

import Msnobj
import Socket # emesenelib
import p2p.transfers

import common

EMESENE_ACK_CHECK_MSECS = 30000

class Switchboard(gobject.GObject):
    '''This class represents a switchboard connection and provides methods
    and signals to interact with it'''
    
    __gsignals__ = {
        'typing' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        # body, format, charset
        'message-sent' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, 
                gobject.TYPE_PYOBJECT)),
        # message
        'non-sent-message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        'nudge-sent' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),
        'ink-sent' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),
        # data
        'action-sent' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        'user-join' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        'user-leave' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        
        'message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            #tid, nick, body, format, charset, hasP4context
            (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, 
             gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)),
        'action-message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_STRING)),
            #tid, data
        'ink-message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_STRING)),
            #tid, filename

        'nudge': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        'status-change': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            
        # this signal is emited when a message
        # with a custom emoticon is received
        'custom-emoticon-received': \
            (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT,)),
        
        # tid, msnobj
        'wink': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT,)),
    } 
    
    MESSAGE_LIMIT = 1202

    def __init__(self, id, msn, type, status = 'pending'):
        '''class contructor
        type can be 'requested' or 'invited', its 'requested' if we request the
        switchboard and guess what invited means? :P.
        status is pending initialy, then when we process the connection string is
        connected and is stablished when someone join the conversation, 
        if something goes wrong the status is closed'''

        gobject.GObject.__init__(self)
        self.id = id
        
        self.status = status
        self.validStatus = ['pending', 'connected', 'established',
                            'closed', 'error']
        self.invalidTransitions = {
            'connected': ['pending'],
            'established': ['pending', 'connected']
        }
        self.connectionString = ''
        
        self.msn = msn

        self.user = self.msn.user.lower()
        self.proxy = self.msn.proxy
        
        self.host = ''
        self.port = 0
        self.authenticationType = ''
        self.authenticationString = ''
        self.sessionID = ''
        self.command = ''
        self.socket = None

        self.members = {}
        self.outDict = {}   
        self.msg_count = 0
        # messageQueue: a list that holds the messages sent when 
        # the status was 'pending'. It's a list of dicts like this
        # {'msg': msg, 'header': header, 'acknowledgeType': type}'
        self.messageQueue = [] 

        # invitationQueue: a list of mails to invite when we go
        # to established status
        self.invitationQueue = []
        # inkSessions: {session: dict{'file','total','actual'}}
        self.inkSessions = {}
        # pendingCEs {mail: [(creator, msnobj, name), ...]}
        # these are params to getCustomEmoticon()
        self.pendingCEs = {}

        # { Message-ID: MultiPacketBuffer }
        self.packet_buffer = {}

        self.p2p_output_id = 0
        self.p2p_output_interval = 100
        
        self.firstMessage = False
        self.firstUser = ''

        self.error = 0
        # needed for logger
        self.started = time.time()
        
        # if True, conversation will overwrite sender's nicks 
        # with p4 context, if available
        self.canUseP4 = msn.canUseP4
        
    def __repr__(self):
        return '<Switchboard users: ' + str(self.members.keys()) + '>' 

    def emit(self, signal, *args):
        gobject.GObject.emit(self, signal, *args)
        if self.msn:
            self.msn.emit('switchboard::' + signal, self, signal, args)
   
    def parse(self):
        '''parse the connection string to fill the attributes'''
    
        if self.connectionString == '':
            return        

        if self.connectionString.split()[0] == 'XFR':
            # example
            # XFR 15 SB 207.46.108.37:1863 CKI 17262740.1050826919.32308\r\n
            (command, tid, sb, host,
             authenticationType,
             authenticationString,
             u, server) = self.connectionString.split()[:8]
        else:
            # example
            # RNG 11752013 207.46.108.38:1863 CKI 849102291.520491113 \
            # example@passport.com Example%20Name
            (command, sessionID, host,
             authenticationType,
             authenticationString,
             user, userName, u, server) = self.connectionString.split()[:9]

            self.sessionID = sessionID
             
            self.addMember(user, userName, initial=True)

        self.command = command
        self.host = host.split(':')[0]
        self.port = int(host.split(':')[1])
        self.authenticationType = authenticationType
        self.authenticationString = authenticationString
        
    def leaveChat(self):
        '''leave the conversation'''
        self.setStatus('closed')
        try:
            self.socket.send('OUT\r\n')
        except Exception, e:
            pass

    def socketHangup(self, obj=None):
        '''The socket got into IO_HUP or IO_ERR status'''
        common.debug(str(self) + ' hangup/error', 'switchboard')
        if self.status != 'error':
            self.setStatus('closed')
        return False
        
    def process(self, obj=None):
        '''read the info from Socket and process the info'''
        if self.socket == None:
            return False
        
        def close(message, status='closed'):
            common.debug(message, 'switchboard')
            self.setStatus(status)
            
        try:
            (command, tid, params) = self.socket.receiveCommand()
        except Exception, e:
            close(str(self) + ' error, closing (receive)\n' + str(e))
            return False
        
        if command == '':
            # empty command means some socket borkedness
            close('received empty command, the socket is broken')
            return False
        elif command == 'MSG':
            try:
                message = self.socket.receivePayload(int(params.split()[1]))
            except Exception, e:
                close(str(self) + ' error, closing (payload)\n' + str(e))
                return False
                
            common.debug(message, 'switchboard')
            try:
                header, body = splitMsg(message)
            except IndexError:
                common.debug("malformed message", "switchboard")

            # handle multi-part message
            if 'Message-ID' in header:
                message_id = header['Message-ID']
                
                if not self.packet_buffer.has_key(message_id):
                    self.packet_buffer[message_id] = MultiPacketBuffer()
                
                buf = self.packet_buffer[message_id]
                buf.append_chunk(header, body)
                
                if buf.is_complete():
                    header, body = buf.get_message()
                    del self.packet_buffer[message_id]
                else:
                    return # message not complete yet
                
            Type = ''
            
            if "P4-Context" in header and self.canUseP4:
                nick = header['P4-Context']
                hasP4 = True
            else:
                nick = params.split()[0]
                hasP4 = False
                
            if "Content-Type" in header:
                Type = header["Content-Type"]

            if Type.startswith('text/plain'):
                # MSG god@gmail.com God%20http://www.400monkeys.com/God/ 111\r\n
                # MIME-Version: 1.0
                # Content-Type: text/plain; charset=UTF-8
                # X-MMS-IM-Format: FN=Sans; EF=; CO=000000; PF=0
                # 
                # a
                
                if not self.firstMessage:
                    self.firstMessage = True
                    self.msn.emit('new-conversation', self.firstUser, self)
                
                format = ''
                if 'X-MMS-IM-Format' in header:
                    format = header['X-MMS-IM-Format']
                
                try:
                    charset = Type.split('text/plain; charset=')[1]
                except IndexError:
                    charset = ''
                
                self.emit('message', tid, nick, body, format, charset, hasP4)
                self.msn.emit('message-received', tid)

                # WLM doesn't reply invites before the actual MSG
                if tid in self.pendingCEs:
                    for mail, msnobj, name in self.pendingCEs[tid]:
                        self.getCustomEmoticon(mail, msnobj, name)
                    del self.pendingCEs[tid]
                
            elif Type == 'text/x-msnmsgr-datacast':
                # datacasts: nudges, winks and actions
                if body.find('ID: 1') != -1:
                    # nudges
                    if not self.firstMessage:
                        self.firstMessage = True
                        self.msn.emit('new-conversation', self.firstUser, self)
                    
                    self.msn.emit('nudge-received', tid)
                    self.emit('nudge', tid)
                
                elif body.find('ID: 2') != -1:
                    # winks
                    data = body.split("Data: ")[1]
                    if not self.firstMessage:
                        self.firstMessage = True
                        self.msn.emit('new-conversation', self.firstUser, self)
                    msnobj = Msnobj.createFromString(data, False)
                    self.get_wink(tid, msnobj)
                    
                    self.emit('wink', tid, msnobj)
                    
                elif body.find('ID: 4') != -1:
                    # actions
                    if not self.firstMessage:
                        self.firstMessage = True
                        self.msn.emit('new-conversation', self.firstUser, self)
                    data = body.split("Data: ")[1] 
                    self.emit('action-message', tid, data)
                    self.msn.emit('message-received', tid)
                    
            
            elif Type == 'text/x-msmsgscontrol':
                self.emit('typing', tid)

            elif Type == 'text/x-mms-emoticon' or \
                 Type == 'text/x-mms-animemoticon':
                if not self.firstMessage:
                    self.firstMessage = True
                    self.msn.emit('new-conversation', self.firstUser, self)
                self.parseCustomEmoticon(message)

            elif Type == 'application/x-msnmsgrp2p' and \
                 'P2P-Dest' in header and \
                 header['P2P-Dest'].lower() == self.user.lower():
                
                self.msn.p2p[tid].receive_message(body)

            else:
                common.debug("Unhandled content type: " + str(header),
                    'switchboard')
                
        elif command == 'USR':
            if params.split(' ')[0] == 'OK':
                self.setStatus('connected')
            else:
                close('can\'t connect to switchboard: USR ' + str(params))

        elif command == 'IRO':
            #IRO 1 1 1 god@gmail.com urlencoded%20nick 1615642660\r\n
            (currentNumber, totalNumber, mail, nick, clientID) = \
                params.split(' ')
            self.addMember(mail.lower(), nick)
            
            self.emit('user-join', mail.lower())
                
            self.setStatus('established') 
            
        elif command == 'JOI':
            # JOI god@gmail.com urlencoded%20nick 1615642660\r\n
            (nick, clientID) = params.split()[:2] # likely to break..
            self.addMember(tid, nick)
            
            self.emit('user-join', tid)
                
            self.setStatus('established') 
                
        elif command == 'ANS':
            if params == 'OK':
                self.setStatus('connected')
            else:
                close('can\'t connect to switchboard: ANS ' + str(params))
        elif command == 'BYE':
            wasGroupChat = self.isGroupChat()
            self.leave(tid)
            # TODO, check when a bye means an OUT
            # from the other side.
            if params == '1' or wasGroupChat:
                self.emit('user-leave', tid)
                
        elif command == 'ACK':
            self.msg_count -= 1
            if int(tid) in self.outDict:
                del self.outDict[int(tid)]
                #print "deleted ", tid, " have left:", self.outDict 
            return False
        elif command == 'NAK': #untested, never had any of this.
            self.msg_count -= 1
            if int(tid) in self.outDict:
                msg = self.outDict[int(tid)]
                self.check_outDict(tid)   
            return False 
        try:
            self.error = int(command)
            if len(self.members) == 0:
                close('server error %d, closing switchboard' % self.error, \
                    'error')
                self.setStatus('error')
                # flush message in queue as oims
                for mess in self.messageQueue:
                    self.msn.msnOIM.send(self.firstUser, mess['msg'])
                return False
        except ValueError:
            pass

        return True
        
    def add_to_outdict(self, ctype, tid, msg):
        '''this method adds your outgoing text message to a dict, and checks
           back in TIMEOUT milliseconds if the message has been delivered 
           correctly'''
        if ctype == 'text/plain; charset=UTF-8' or ctype == 'text/x-msnmsgr-datacast':
            # crappy sendPayloadCommand returns ++tid so...
            self.outDict[int(tid) - 1] = msg
            gobject.timeout_add(EMESENE_ACK_CHECK_MSECS, self.check_outDict, int(tid) - 1)
            #print "added number", tid - 1
    
    def check_outDict(self, tid, dontClose=0):
        '''hy, i check for acks otherwise i kill me (switchboard)'''
        if int(tid) in self.outDict:
            # we haven't received the ack in the specified timeout.
            # a good thing is recreate the switchboard, so we set our status
            # to closed and spit out to the conversation the non-sent message
            # wdyt of this? --c10ud
            self.emit('non-sent-message', self.outDict[int(tid)])
            del self.outDict[int(tid)]
            common.debug('Timeout on ACKing in switchboard because of ' + str(tid) + \
                    ' closing switchboard', 'switchboard')
            self.setStatus('closed') 
            
        return False
    
    def getStyle(self, message=''): #borrowed from Conversation.py
        '''return the style string to use in the sendMessage method'''

        effectValue = ''

        if self.config.user['fontBold']:
            effectValue += 'B'

        if self.config.user['fontItalic']:
            effectValue += 'I'

        if self.config.user['fontUnderline']:
            effectValue += 'U'

        if self.config.user['fontStrike']:
            effectValue += 'S'

        color = self.config.user['fontColor'].replace('#', '')
        color = color[ 4:6 ] + color[ 2:4 ] + color[ :2 ]

        face = self.config.user['fontFace'].replace(' ', '%20')

        return "X-MMS-IM-Format: FN=" + face + \
            "; EF=" + effectValue + "; CO=" + color + \
            "; PF=0 ;RL=" + self.getRTL(message)
    
    def parseCustomEmoticon(self, message):
        body = message.split('\r\n\r\n')[1]
        l = body.split('\t')
        d = {}
      
        while len(l) > 0:
            if len(l) < 2:
                break
            shortcut = l.pop(0)
            msnobjString = l.pop(0)
            msnobj = Msnobj.createFromString(msnobjString, False)
           
            if msnobj != None:
                self.emit('custom-emoticon-received', shortcut, msnobj)
                filename = shortcut + '_' + msnobj.sha1d + '.tmp'
                filename = urllib.quote(filename).replace('/', '_')
                completeFileName = self.msn.cacheDir + os.sep + filename
                
                if not os.path.isfile(completeFileName):
                    # WLM doesn't reply invites before the actual MSG
                    mail = msnobj.getCreator()
                    if mail not in self.pendingCEs:
                        self.pendingCEs[mail] = []
                    self.pendingCEs[mail].append((mail, msnobj, \
                        completeFileName))
                else:
                    self.msn.emit('custom-emoticon-transfered', None, \
                        msnobj, completeFileName)

    def _output_ready(self):
        '''This function sucks. Ya, rly (c10ud)'''
        self.p2p_set_output_connected(True)

        if self.msg_count < 5:
            self.msn.p2p[self.firstUser].output_ready(self)

            if self.msg_count < 2 and self.p2p_output_interval > 50:
                self.p2p_output_interval -= 10

        elif self.p2p_output_interval < 300:
            self.p2p_output_interval += 10

        return True

    def p2p_set_output_connected(self, value):
        '''(dis)connects socket output_ready "signal"'''
        if self.socket:
            if self.p2p_output_id:
                gobject.source_remove(self.p2p_output_id)
                self.p2p_output_id = 0
            
            if value:
                self.p2p_output_id = gobject.timeout_add(
                    self.p2p_output_interval, self._output_ready)

    def p2p_send(self, message, mail):
        '''Sends a p2p message, called by P2PManager'''
        self.sendMessage(str(message), '', 'application/x-msnmsgrp2p',
            'D', 'P2P-Dest: ' + str(mail))

    def sendMessage(self, msg='', format='', \
                     contentType='text/plain; charset=UTF-8', \
                     acknowledgeType='A', extraHeader=''):
        
        header = "MIME-Version: 1.0\r\n"
        
        if contentType != "":
            header += "Content-Type: " + contentType + "\r\n"

        if extraHeader != "":
            header += extraHeader + '\r\n'
            
        if contentType == 'text/plain; charset=UTF-8':
            msg = msg[:1100] #TODO: use something like MAX_MESSAGE_LENGTH
            self.emit('message-sent', msg, format, 
                contentType.split('charset=')[1])
        
        if format != "":
            header += format + "\r\n\r\n"
        else:
            header += "\r\n"
        
        if self.status != 'established':
            self.messageQueue.append({
                'msg': msg, \
                'header': header, \
                'acknowledgeType': acknowledgeType, \
                'contentType': contentType \
            })

        elif self.status == 'established':
            try:
                tid = self.socket.sendPayloadCommand('MSG', acknowledgeType, \
                    header + msg)
                # append to out queue, only if this is a message
                self.add_to_outdict(contentType, tid, msg)
                self.msg_count += 1
            except Exception, e:
                #raise e
                common.debug('socket error on switchboard, closing',
                    'switchboard')
                common.debug(str(e), 'switchboard')
                self.setStatus('closed')
        
    def sendKeepAlive(self):
        ''' sends a keepalive to current switchboard '''
        self.sendMessage('', '', 'text/x-keep-alive', 'A')            

    def flushMessageQueue(self):
        '''send all the unsended messages'''
        
        if self.status != 'established' or len(self.messageQueue) == 0:
            return
        
        for i in self.messageQueue:
            try:
                tid = self.socket.sendPayloadCommand('MSG', \
                    i['acknowledgeType'], i['header'] + i['msg'])
                self.add_to_outdict(i['contentType'], tid, i['msg'])
                self.msg_count += 1
            except Exception, e:
                common.debug('socket error on switchboard, ' + \
                    'closing switchboard', 'switchboard')
                common.debug(str(e), 'switchboard')
                self.setStatus('closed')
        # flushed
        self.messageQueue = []
        common.debug('message queue flushed', 'switchboard')

    def sendNudge(self):
        '''a easy method to send a nudge'''

        self.sendMessage('ID: 1\r\n\r\n', '', 'text/x-msnmsgr-datacast')
        self.emit('nudge-sent')

    def sendAction(self, data):
        '''a easy method to send an action message - this works with MSNC6+'''

        self.sendMessage('ID: 4\r\nData: %s\r\n' % data, '',
            'text/x-msnmsgr-datacast')
        self.emit('action-sent', data)

    def sendIsTyping(self):
        '''a easy method to send the is typing message'''

        self.sendMessage('\r\n', '', 'text/x-msmsgscontrol\r\nTypingUser: ' + 
            self.user)

    def invite(self, mail):
        '''invite somebody to the switchboard conversation'''

        mail = mail.lower()
        if self.firstUser == '':
            self.firstUser = mail

        if self.status in ('connected', 'established') and \
           not mail in self.members.keys():
            try:
                self.socket.sendCommand('CAL', mail)
            except Exception, e:
                #raise e
                common.debug('socket error on switchboard, ' +
                    'closing switchboard', 'switchboard')
                common.debug(str(e), 'switchboard')
                self.setStatus('closed')
                return
            
            if mail in self.invitationQueue:
                self.invitationQueue.pop(self.invitationQueue.index(mail))
        elif not mail in self.invitationQueue:
            self.invitationQueue.append(mail.lower())

    def leave(self, mail):
        '''remove the mail from the members list'''
        
        if mail.lower() in self.members.keys():
            if len(self.members) == 1:
                self.setStatus('closed')
            else:
                del self.members[mail.lower()]
    
    def setConnectionString(self, connectionString):
        '''we received the conecction string (the first response of a XFR
        or the RNG) and here we process it'''
        
        self.connectionString = connectionString        
        self.parse()
        self.connectSocket()
        
    def connectSocket(self):
        '''connect the socket'''

        if self.proxy != None:
            self.socket = Socket.HTTPSocket(self.host, self.port, \
                self.proxy, 'SB')
        else:
            self.socket = Socket.Socket(self.host, self.port)
            
        self.socket.connect('input', self.process)
        self.socket.connect('hangup', self.socketHangup)
        
        if self.command == 'XFR':
            try:
                self.socket.sendCommand("USR", self.user + " " + \
                    self.authenticationString)
            except Exception, e:
                #raise e
                common.debug('socket error on switchboard, ' + \
                    'closing switchboard', 'switchboard')
                common.debug(str(e), 'switchboard')
                self.setStatus('closed')
            
        else: #RNG
            # ANS 1 alice@passport.com 1056411141.26158 17342299\r\n
            try:
                self.socket.sendCommand("ANS", self.user + " " + \
                    self.authenticationString + " " + self.sessionID)
                # forcing some stuff here
                self.setStatus('connected')
                self.setStatus('established')                
            except Exception, e:
                #raise e
                common.debug('socket error on switchboard, ' + \
                    'closing switchboard', 'switchboard')
                common.debug(str(e), 'switchboard')
                self.setStatus('closed')

        if len(self.members) == 1:
            self.msn.p2p[self.firstUser].register(self)
        else:
            self.msn.p2p[self.firstUser].unregister(self)
        
    def addMember(self, mail, nick, initial=False):
        '''add a member to the members dict'''
        
        mail = mail.lower()
        self.members[mail] = nick.replace('%20', ' ')
        
        if not initial:
            if len(self.members) == 1:
                self.firstUser = mail
                self.msn.p2p[mail].register(self)
            else:
                self.msn.p2p[mail].unregister(self)

    def setStatus(self, status):
        '''set the status, the status can be 'pending', 'stablished' or 'closed'
        PLEASE change the status here and not directly because we may want
        to do thing when a status is changed
        XXX-DX: i think we need a property here, we can't ask "PLEASE" that
        way...'''
        
        if status in self.validStatus and self.status != status:
            if self.invalidTransitions.has_key(self.status) and \
               status in self.invalidTransitions[self.status]:
                return

            self.status = status

            if status in ('closed', 'error'):
                self.msn.p2p[self.firstUser].unregister(self)
                if self.socket:
                    self.socket.hangup()
            if status == 'error':
                try:
                    self.socket.send('OUT\r\n')
                except Exception, e:
                    pass
                self.socket = None
            if status == 'connected':
                for i in self.invitationQueue:
                    self.invite(i)
                    
                self.invitationQueue = []
            elif self.status == 'established':
                self.flushMessageQueue()
            
            self.emit('status-change')
        
    def getId(self): #FIXME: getter
        '''return the id of the switchboard, this is a unique identification
        of the switchboards. The value is the value of the Trid of the
        command that created the switchboard or the sessionid if the other
        user started the conversation, the value doesnt matter, what
        matters is that its unique.'''
        
        return self.id
    
    def getOnlineUsers(self):
        '''This method returns a list ol mails of the contacts who are
        not offline'''
        
        return self.msn.contactManager.getOnlineUsers()
    
    def getMembers(self):
        '''return a list of the members in the switchboard'''
        
        return self.members.keys()

    def isGroupChat(self):
        return (len(self.members) > 1)
        
    def getInvitedMembers(self):
        '''return a list of the members invited but not joined'''
        
        return self.invitationQueue
        
    def getDisplayPicture(self, email):
        '''start a P2P session to get the display picture'''
        if self.msn is None:
            return

        email = email.lower()
        contact = self.msn.contactManager.getContact(email)
        
        if contact == None:
            common.debug('contact (' + email + ') not found in ' + \
                'getDisplayPicture', 'switchboard')
            return
        
        msnobj = contact.msnobj
        
        if msnobj == None:
            common.debug(email + ' has no msnobj in getDisplayPicture', \
                'switchboard')
            return

        #print "Switchboard.getDisplayPicture(email=%s)" % email

        filename = os.path.join(self.msn.cacheDir, contact.displayPicturePath)
        if not os.path.exists(filename):
            #print "Requesting avatar for ", email
            p2p.transfers.Receiver(self.msn.p2p[email], msnobj)
        else:
            #print "Avatar cached at %s - updating path" % filename
            self.msn.emit("display-picture-changed", self, msnobj, email)
            
    def getCustomEmoticon(self, email, msnobj, filename):
        email = email.lower()
        msnobj.filename = filename
        p2p.transfers.Receiver(self.msn.p2p[email], msnobj)
        
    def sendCustomEmoticons(self, message):
        msnObjs = []
        msnObj = ''
        i = 0
        msnOM = self.msn.getMsnObjectsManager()
        for CE in msnOM.getIds():
            if i == 4:
                i = 0
                msnObjs.append(msnObj)
                msnObj = ''
            if message.find(CE) != -1:
                msnObj += CE + '\t' + str(msnOM.getById(CE)) + '\t'
                i += 1
        if msnObj != '':
            msnObjs.append(msnObj)
        for msnObj in msnObjs:
            self.sendMessage(msnObj, contentType='text/x-mms-animemoticon')
            
    def get_wink(self, email, msnobj):
        p2p.transfers.Receiver(self.msn.p2p[email], msnobj)

class MultiPacketBuffer:
    '''this class represents the buffer for a multichunk MIME-message'''
    
    def __init__(self):
        '''initialize the buffer'''
        self.chunks_total = 0
        self.chunks_received = 0
        self.body = []
        self.header = {}
        
    def append_chunk(self, header, body):
        '''appends a new chunk to the buffer'''
        
        if 'Chunks' in header:
            self.chunks_total = int(header['Chunks'])
        
        for key, val in header.iteritems():
            if key not in ['Chunks', 'Chunk', 'Message-ID']:
                self.header[key] = val
        
        self.chunks_received += 1
        self.body.append(body)
        
    def get_message(self):
        '''returns a (header, body) tuple.
        header is a dict, body is a string'''
        return (self.header, ''.join(self.body))
    
    def is_complete(self):
        '''returns True if we have all chunks, False otherwise'''
        return (self.chunks_received == self.chunks_total)
        
def splitMsg(message):
    '''return header(dict), body(str)'''
    part = message.split('\r\n\r\n')
    def htuple(x):
        parts = x.split(': ')
        return (parts[0], ': '.join(parts[1:]))
    header = dict([htuple(i) for i in part[0].split('\r\n')])
    body = '\r\n\r\n'.join(part[1:])
    return header, body
