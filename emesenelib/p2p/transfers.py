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

'''module to handle p2p sessions on msn protocol'''

import os
import time
import random
import base64
import struct
import gobject

import socket, asyncore
from threading import Thread

import emesenelib.common as common
import emesenelib.Msnobj as Msnobj
import emesenelib.p2p.slp as msn_slp # TODO

common.debugFlag = True

def contains(string, substring):
    '''return True if string contains substring'''
    return (string.find(substring) != -1)
    
# we use the max from sys.maxint in a 32 bit machine because
# in a 64 bit machine it is bigger and can give some troubles
def random_number(minimum = 0, maximum = 2147483647):
    '''return a random number between minimum and maximum'''
    return random.randint(minimum, maximum)
 
class Base(gobject.GObject):
    '''a base class for P2P handlers
    this class has all the methods to create the different
    messages and to check if a message belong to a handler'''

    __gsignals__ = { 
        # message, footer, session_id
        'msnp2p-message-ready':
        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
            (gobject.TYPE_PYOBJECT, ) * 2),
        
        # flags, file, footer, bye (bool)
        'msnp2p-file-ready':
        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, ) * 4),

        # message
        'debug':
        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, ))
    }

    # workarounds for pylint lack of support of builtin subclassing
    # just to get cleaner output
    emit = gobject.GObject.emit
    connect = gobject.GObject.connect
    disconnect = gobject.GObject.disconnect
    
    # seconds alive until disconnecting automatically
    MAX_TIME_ALIVE = 60*3

    FOOTER = '\0\0\0\0'
    DP_FOOTER = '\0\0\0\1'
    FILE_FOOTER = '\0\0\0\2'
    INK_FOOTER = '\0\0\0\3'
    WEBCAM_FOOTER = '\0\0\0\4'
    CE_FOOTER = '\0\0\0\x0c'

    # these must be replaced on subclassing
    temporary_session = None
    signals_p2p = [] # ['msnp2p-message-received']
    signals_self = [] # ['msnp2p-message-ready']
    
    def __init__(self, p2p):
        '''from_ is the sender and to the receiver email'''
        gobject.GObject.__init__(self)

        # the moment when its created
        self.time_stamp = time.time()
        
        # list of identifiers of connected signals
        self.signal_ids = []

        self.from_ = p2p.manager.msn.user
        self.to_ = p2p.mail
        
        # this values are just the most common ones
        self.via = msn_slp.random_id()
        self.cseq = '0'
        self.call_id = msn_slp.random_id()
        self.max_forwards = '0'
        self.content_type = ''
        self.content_length = ''
        self.euf_guid = ''
        self.session_id = str(random_number(50000))
        self.app_id = ''
        self.context = ''

        self.data = None

        p2p.emit('new-p2p-session', self)

    def check_time_limit(self):
        '''check if the time alive is greater than MAX_TIME_ALIVE
        if it is, return True to let the gc destroy the object'''

        if self.temporary_session and \
            time.time() > self.time_stamp + Base.MAX_TIME_ALIVE:

            self.debug('max time alive exceeded', 'p2p')
            return True

    def debug(self, message, _channel=''):
        '''Emits the debug signal and displays the message in the terminal'''
        self.emit('debug', message)
        common.debug(message, 'p2p')
        
    def is_data(self, bin):
        '''return True if the header is from a data message of
        this p2p session'''

        if bin.flag != bin.ACK_FLAG and \
           bin.session_id == int(self.session_id):
            return True

        return False

    def is_last_data(self, bin):
        '''return True if it is the last data message'''

        if self.is_data(bin) and \
            bin.data_offset + bin.message_length == bin.total_data_size:
            return True

    def connect_handler(self, p2p):
        '''connects signals, yay'''

        # the following may be confusing, but who cares? just don't touch
        # i use strings here to avoid saving a reference
        targets = ('p2p', self.signals_p2p), ('self', self.signals_self)

        for owner, signals in targets:
            if owner == 'p2p':
                src, dest = p2p, self
            else:
                src, dest = self, p2p

            for signal in signals:
                funcname = 'on_' + signal.replace("-", "_")
                identifier = src.connect(signal, getattr(dest, funcname))
                self.signal_ids.append((owner, identifier))

    def disconnect_handler(self, p2p):
        '''disconnects itself allowing garbage collection'''
        self.debug('disconnecting p2p handler', 'p2p')

        for owner, identifier in self.signal_ids:
            if owner == 'p2p':
                src = p2p
            else:
                src = self
            src.disconnect(identifier)


class Sender(Base):
    '''A class that sends p2p content based on msnobjs (with dpm)
    This is unbeliabely short, heh.'''

    temporary_session = True
    
    signals_p2p = []
    signals_self = ['msnp2p-message-ready', 'msnp2p-file-ready']

    def __init__(self, p2p, bin_header, slp, data):
        Base.__init__(self, p2p)

        self.data = data
        self.via = slp.via
        self.call_id = slp.call_id
        self.session_id = slp.body['SessionID']
        
        self.connect_handler(p2p)
        self.emit('msnp2p-message-ready', msn_slp.ok(self), 0)
        self.emit('msnp2p-message-ready', '\0\0\0\0', self.session_id) #dpm
        self.emit('msnp2p-file-ready', bin_header.EACH_FLAG, self.data,
            Base.DP_FOOTER, self.on_transfer_complete)

    def on_transfer_complete(self, p2p):
        self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
        self.disconnect_handler(p2p)


class Receiver(Base):
    '''a class that request data to other client and receive it'''

    temporary_session = True

    signals_p2p = ['msnp2p-message-received']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, p2p, msnobj):
        '''p2p is a P2PUser, msnobj is a Msnobj'''

        if p2p.last_requested_msnobj == msnobj:
            return
        
        Base.__init__(self, p2p)
        
        p2p.last_requested_msnobj = msnobj
        self.msnobj = msnobj

        if self.msnobj.type == Msnobj.Msnobj.DISPLAY_PICTURE:
            self.app_id = '1' 
        elif self.msnobj.type == Msnobj.Msnobj.CUSTOM_EMOTICON:
            self.app_id = '12' 

        self.connect_handler(p2p)

        context = base64.b64encode(str(msnobj) + '\0')
        self.emit('msnp2p-message-ready', msn_slp.invite(self, context), 0)
    
    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        if self.check_time_limit():
            self.disconnect_handler(p2p)
        else:
            self.debug('receiver checking', 'p2p')
            if int(self.session_id) == int(bin.session_id):
                body = message[48:-4]

                if body == '\0\0\0\0':   # ignore dpm
                    return
                
                if len(body) != bin.total_data_size:
                    self.debug('corrupt data, not all pieces received')
                elif self.msnobj.type == Msnobj.Msnobj.CUSTOM_EMOTICON:
                    self.debug('custom-emoticon-data-received', 'p2p')
                    p2p.emit('custom-emoticon-data-received', 
                        self.msnobj, body, self.to_)
                elif self.msnobj.type == Msnobj.Msnobj.DISPLAY_PICTURE:
                    self.debug('display-picture-received', 'p2p')
                    p2p.emit('display-picture-received', 
                        self.msnobj, body, self.to_)
                elif self.msnobj.type == Msnobj.Msnobj.WINK:
                    self.debug('wink-data-received', 'p2p')
                    p2p.emit('wink-data-received', self.msnobj, body, self.to_)
                else:
                    self.debug('no CE, DP or wink? %s' % self.msnobj.type, 'p2p')

                self.disconnect_handler(p2p)


class DCHandler(Base):
    '''A class that handles direct connect invites
    After the automatic ack massacre, most code here was removed,
    so handling ACK MSNSLP messages'''

    temporary_session = False

    signals_p2p = ['msnp2p-message-received']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, p2p, bin_header, slp):
        '''this processes the first invite, subsequent invites should '''
        Base.__init__(self, p2p)

        self.via = slp.via
        self.call_id = slp.call_id
        if 'SessionID' in slp.body:
            self.session_id = slp.body['SessionID']
        else:
            self.session_id = 0
        
        self.connect_handler(p2p)
        self.tempp2p = p2p
        
        self.handle_invite(bin_header, slp)
            
    def handle_invite(self, bin_header, slp):
        '''Handles a invite message'''

        if slp.content_type == msn_slp.SLPMessage.CONTENT_TRANS_REQ:
            # params after \r\n\r\n:
            #Bridges: TRUDPv1 TCPv1 SBBridge TURNv1
            #NetID: -1689699384
            #Conn-Type: Port-Restrict-NAT
            #TCP-Conn-Type: Port-Restrict-NAT
            #UPnPNat: false
            #ICF: false
            #Hashed-Nonce: {44C4DB18-98AC-2025-1404-1998BEE1C437}
            #SessionID: 10958830
            #SChannelState: 0
            #Capabilities-Flags: 1

            message = msn_slp.ok(self)
            message.content_type = msn_slp.SLPMessage.CONTENT_TRANS_RESP
            message.body = {
                'Bridge': 'TCPv1',
                'Listening': 'false',
                'Nonce': '{00000000-0000-0000-0000-000000000000}',
            }
            self.emit('msnp2p-message-ready', message, 0)

        elif slp.content_type == msn_slp.SLPMessage.CONTENT_TRANS_RESP:
            # the second invite is a TRANSRESP. body:
            # 
            # Bridge: TCPv1
            # Listening: true
            # Conn-Type: Direct-Connect
            # TCP-Conn-Type: Direct-Connect
            # Nonce: {A10AE850-D3DD-4A4A-A69D-C41F01D41F94}
            # IPv4Internal-Addrs: 5.127.##.## 169.254.##.### 201.255.###.##
            # IPv4Internal-Port: 3660
            #  <alt>
            # IPv4Internal-Addrs: 190.183.##.##
            # IPv4Internal-Port: 1434
            # SessionID: 278241011
            # SChannelState: 0
            # Capabilities-Flags: 1

            # this is auto acked
            pass

    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        self.debug('DC Handler checking')
        if 'SessionID' in slp.body:
            session_id = slp.body['SessionID']
        else:
            session_id = bin.session_id

        if session_id == self.session_id or slp.call_id == self.call_id:
            if slp.method.startswith('ACK'):

                addrs = []
                for field in ('External', 'Internal'):
                    fieldname = 'IPv4' + field + 'AddrsAndPorts'
                    if fieldname in slp.body:
                        addrs.extend(slp.body[fieldname].strip().split())
                
                self.debug("Got ACK, i'll connect to " + repr(addrs))
                
                #p2p.get_switchboard()
                #p2p.switchboard.emit('message', 'p2p', '',
                #    'Received address list ' + repr(addrs), '', '')
                #time.sleep(10)
                
            elif slp.method.startswith('BYE'):
                self.disconnect_handler(p2p)


class FTSender(Base):
    '''a class that request data to other client and receive it'''
    
    temporary_session = False
    
    signals_p2p = ['msnp2p-message-received', 'file-transfer-canceled']
    signals_self = ['msnp2p-message-ready', 'msnp2p-file-ready']

    def __init__(self, p2p, filename):
        Base.__init__(self, p2p)
        
        self.app_id = '2' 
        
        self.context = FTContext()
        if os.name == "nt":
            filename = unicode(filename)
        self.context.filename = filename
        #self.context.preview = base64.b64encode( self.data )
        self.context.file_size = os.stat(filename).st_size
        self.data = open(filename, "rb")

        self.connect_handler(p2p)
        self.current_transfer = 0

        message = msn_slp.invite(self, base64.b64encode(str(self.context)),
            msn_slp.SLPMessage.EUFGUID_FILE)

        self.emit('msnp2p-message-ready', message, 0)
        
    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        
        if 'SessionID' in slp.body:
            session_id = int(slp.body['SessionID'])
        else:
            session_id = int(bin.session_id)

        self.debug("FTSender checking")

        if session_id == int(self.session_id):
            self.debug("Mine!")
            if slp.method == msn_slp.SLPMessage.OK_STATUS:
                self.debug("Accepted")
                common.debug('sending data', 'p2p')
                p2p.emit('file-transfer-accepted', int(self.session_id),
                    self.context, 'Me')
                self.emit('msnp2p-file-ready', bin.FILE_FLAG | \
                    bin.EACH_FLAG | bin.STORAGE_FLAG, self.data,
                    Base.FILE_FOOTER, self.on_transfer_complete)
                
            elif slp.method == msn_slp.SLPMessage.DECLINE_STATUS or \
                 slp.method.startswith('BYE'):
                
                self.debug("Cancelled")
                # notify the user
                p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
                self.disconnect_handler(p2p)
            else:
                self.debug("wtf is " + str(slp.method))
        elif slp.call_id == self.call_id and slp.method.startswith("BYE"):
            self.debug("file transfer canceled", 'p2p')
            p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
            self.disconnect_handler(p2p)
            
    def on_transfer_complete(self, p2p):
        p2p.emit('file-transfer-complete', int(self.session_id),
            self.context, None, 'Me')
        self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
        self.disconnect_handler(p2p)

    def on_file_transfer_canceled(self, p2p, session, context, sender):
        '''callback for P2PUser file-transfer-canceled, sends a decline
        message canceling the transfer'''
        if int(session) == int(self.session_id):
            self.debug('canceling FT')
            self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
            self.disconnect_handler(p2p)
    
    def disconnect_handler(self, p2p):
        Base.disconnect_handler(self, p2p)
        if self.current_transfer and \
           self.current_transfer in p2p.outgoing_pending_messages:
            # this stops the send data callback
            del p2p.outgoing_pending_messages[self.current_transfer]
            self.current_transfer = 0

class FTReceiver(Base):
    '''a class to accept and handle an incoming file transfer'''

    temporary_session = False

    signals_p2p = ['msnp2p-message-received', 'msnp2p-file-received',
        'file-transfer-accepted', 'file-transfer-canceled']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, p2p, context, slp, bin_header):
        '''context, slp and bin_header are from the INVITE message'''
        Base.__init__(self, p2p)

        self.context = context

        self.via = slp.via
        self.call_id = slp.call_id
        self.session_id = int(slp.body['SessionID'])
        
        self.connect_handler(p2p)

        p2p.start_new_conv()
        p2p.emit('file-transfer-invite', int(self.session_id), \
            self.context, self.from_)
        # ugly, but effective
        p2p.manager.msn.emit('new-file-transfer',self.to_, self.context.filename)
        
    def on_file_transfer_accepted(self, p2p, session, context, sender):
        '''callback for P2PUser file-transfer-accepted, sends a 200ok
        message starting the transfer'''
        if int(session) == int(self.session_id) and \
           context == self.context and \
           sender == self.from_:

            # accept the file
            self.debug('accepting FT')
            self.emit('msnp2p-message-ready', msn_slp.ok(self), 0)

    def on_file_transfer_canceled(self, p2p, session, context, sender):
        '''callback for P2PUser file-transfer-canceled, sends a decline
        message canceling the transfer'''
        if int(session) == int(self.session_id):
            self.debug('canceling FT')
            self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
            self.disconnect_handler(p2p)

    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        
        self.debug('FT Receiver checking', 'p2p')
        if 'SessionID' in slp.body:
            session_id = int(slp.body['SessionID'])
        else:
            session_id = int(bin.session_id)

        if session_id == int(self.session_id):
            if slp.method == msn_slp.SLPMessage.DECLINE_STATUS or \
               slp.method.startswith('BYE'):
                
                self.debug("file transfer canceled", 'p2p')
                p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
                self.disconnect_handler(p2p)

            if bin.flag == bin.CANCEL_FLAG:
                self.debug('cancelled on TLP')
                p2p.emit('transfer-failed', int(self.session_id), 'error')
                self.disconnect_handler(p2p)

        elif slp.call_id == self.call_id and slp.method.startswith("BYE"):
            self.debug("file transfer canceled", 'p2p')
            p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
            self.disconnect_handler(p2p)
            
    def on_msnp2p_file_received(self, p2p, bin, rc):
        '''Method called when the file is received succesfully'''
        self.debug('FTReceiver checking file')
        if self.is_data(bin) and bin.flag & bin.FILE_FLAG:
            self.debug('file received')
            
            # file received successfully
            self.debug('file-transfer-complete')
            p2p.emit('file-transfer-complete', int(self.session_id),
                self.context, rc, self.from_)
            # ugly, but effective
            p2p.manager.msn.emit('finished-file-transfer',self.to_,self.context.filename)
            self.disconnect_handler(p2p)



class FTContext(object):
    '''this class represents a File Transfer Context'''

    #FORMAT = '<LLQL520s30sL64s'  # perl?
    FORMAT = '<LLQL520s30sL'
    PORTABLE_FORMAT = '<LQL520s'  # note: without header
    HEADER_FORMAT = '<L'

    UNKNOWN_FT = 0xffffffff
    UNKNOWN_BG = 0xfffffffe
    RUBBISH = base64.b64encode("rubbish")

    TYPE_NO_PREVIEW = 0
    TYPE_PREVIEW = 1
    TYPE_BACKGROUND = 4
    
    def __init__(self, data=None):
        '''Constructor'''
        
        self.header_length = struct.calcsize(FTContext.FORMAT)
                                     # ..dw
        self.msnc = 2                # dw (3 == msn7)
        self.file_size = 0           # qw
        self.__data_type = 0         # dw
        self.__filename = ''         # 520 byte string, utf-16-le
        self.rubbish = ''            # 30 byte string, optional base64
        self.unknown1 = 0            # dw (see UNKNOWN_(BG|FT))

        # set properties
        self.data_type = FTContext.TYPE_NO_PREVIEW
        self.filename = ''

        self.preview = ''

        if data != None:
            self.fill(data)
            
    def __str__(self):
        '''return the representation of this object'''

        return struct.pack(FTContext.FORMAT,
            self.header_length,
            self.msnc,
            self.file_size,
            self.data_type,
            self.__filename,
            self.rubbish,
            self.unknown1) + self.preview
    
    def set_data_type(self, dword):
        '''property setter for data_type
        when it's set as background, the rubbish and unknown1 fields
        are set to the corresponding values'''

        self.__data_type = dword
        if dword == FTContext.TYPE_BACKGROUND:
            self.rubbish = FTContext.RUBBISH
            self.unknown1 = FTContext.UNKNOWN_BG
        else:
            self.rubbish = ''
            self.unknown1 = FTContext.UNKNOWN_FT

    def get_data_type(self):
        '''property getter for data_type'''
        return self.__data_type

    data_type = property(fset=set_data_type, fget=get_data_type)

    def set_filename(self, data):
        '''set the value of filename'''
        data = os.path.basename(data)
        self.__filename = data.encode('utf-16-le', 'replace').ljust(520, '\0')
        
    def get_filename(self):
        '''get the value of filename'''
        return self.__filename.decode('utf-16-le', 'replace').replace('\0', '')

    filename = property(fset=set_filename, fget=get_filename)
    
    def print_fields(self):
        '''print the binary fields'''
        print
        print 'Header length:   ' + str(self.header_length)
        print 'msnc:            ' + str(self.msnc)
        print 'File size:       ' + str(self.file_size)
        print 'Type:            ' + str(self.data_type)
        print 'Filename:        ' + str(self.filename)
        print
        
    def fill(self, data):
        '''fill the object with the data provided'''
        self.header_length = struct.unpack(FTContext.HEADER_FORMAT, data[:4])[0]
        portable_size = struct.calcsize(FTContext.PORTABLE_FORMAT)
        header = data[4:portable_size + 4]
        
        # from __future__ import braces
        (   
            self.msnc,
            self.file_size,
            self.data_type,
            self.__filename,
        ) = struct.unpack(FTContext.PORTABLE_FORMAT, header)

        self.preview = data[self.header_length:]

def between(s, start, stop):
    '''return the part between start and stop from s'''
    try:
        return s.split(start)[1].split(stop)[0]
    except:
        return ''

class WebcamHandler(Base):
    '''a class to accept and handle an incoming file transfer'''

    temporary_session = False

    signals_p2p = ['msnp2p-message-received', 'webcam-accepted', 
        'webcam-canceled', 'webcam-frame-ready']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, we_initiate, request, p2p, slp=None):
        '''context, slp and bin_header are from the INVITE message'''
        Base.__init__(self, p2p)

        if slp:
            self.via = slp.via
            self.call_id = slp.call_id
            self.session_id = int(slp.body['SessionID'])
        
        self.p2p = p2p
        self.we_initiate = we_initiate
        self.producer = request
        
        self.connect_handler(p2p)

        self.app_id  = '4'
        self.context = 'ewBCADgAQgBFADcAMABEAEUALQBFADIAQwBBAC0ANAA0ADA' + \
                        'AMAAtAEEARQAwADMALQA4ADgARgBGADgANQBCADkARgA0AEUAOAB9AA=='
        
        p2p.start_new_conv()
        self.received_producer_xml = False
        self.received_viewer_xml = False
        self.webcam_thread = None
        
        msn = self.p2p.manager.msn
        self.external_ip = msn.demographics['ClientIP']
        
        if we_initiate:
            if self.producer:
                self.debug('Sending invite to send webcam')
                message = msn_slp.invite(self, self.context, msn_slp.SLPMessage.EUFGUID_WEBCAM)
                self.emit('msnp2p-message-ready', message, 0)
            else:
                # ask to receive webcam
                self.debug('Sending invite to receive webcam')
                message = msn_slp.invite(self, self.context, msn_slp.SLPMessage.EUFGUID_WEBCAM_ASK)
                self.emit('msnp2p-message-ready', message, 0)
        else:
            if self.producer:
                self.debug("We received a request to send out webcam")
                p2p.emit('webcam-invite', int(self.session_id), self.to_, True, None)
            else:
                self.debug('Received webcam invite')
                p2p.emit('webcam-invite', int(self.session_id), self.from_, False, self.to_)
        
    def receive_frame(self, frame):
        self.p2p.emit('webcam-frame-received', int(self.session_id), self.from_, frame)

    def on_webcam_frame_ready(self, p2p, session, frame, width, height):
        if int(session) == int(self.session_id) and self.webcam_thread is not None:
            sock = self.webcam_thread.get_main_sock()
            if sock is not None:
                try:
                    sock.send(self.add_frame_header(frame, width, height))
                except:
                    print "Error sending webcam frame..."

    def add_frame_header(self, frame, width, height):
        timestamp = time.time()
        uid = [random.randint(1,255), random.randint(1,255), random.randint(1,255), random.randint(1,255)]
        #FIXME: I'm not sure this actually works, should be checked...
        dump, key = struct.unpack('8sh', frame[:10])
        header = struct.pack('<2chhhi4s4ci', chr(24), chr(0), width, height, key, len(frame), "ML20", chr(uid[0]), chr(uid[1]), chr(uid[2]), chr(uid[3]), timestamp)
        return header + frame
        
    def on_webcam_accepted(self, p2p, session, sender):
        '''callback for P2PUser file-transfer-accepted, sends a 200ok
        message starting the transfer'''
        if int(session) == int(self.session_id) and \
           sender == self.from_:
            
            # accept it
            self.debug('Accepting webcam invitation')
            self.emit('msnp2p-message-ready', msn_slp.ok(self), 0)
            self.emit('msnp2p-message-ready', msn_slp.webcam_invite(self), 0)

    def on_webcam_canceled(self, p2p, session):
        '''callback for P2PUser webcam-canceled, sends a decline
        message canceling the webcam session'''
        
        if int(session) == int(self.session_id):
            print('canceling webcam')
            # TODO: possible unsafe without locking
            if self.webcam_thread:
                self.webcam_thread.close_other_sockets(None)
            self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
            self.disconnect_handler(p2p)

    def parse_producer_xml(self, msg):
        self.debug("Parsing producer XML")
        IPs = []
        ports = []
            
        # collect all IPs
        i = 1
        while True:
            start = '<tcpipaddress%d>' % i
            stop = '</tcpipaddress%d>' % i
            if msg.find(start) > 0:
                IPs.append(between(msg, start, stop))
                i += 1
            else:
                break
            
        ports.append(between(msg, '<tcpport>', '</tcpport>'))
        ports.append(between(msg, '<tcplocalport>', '</tcplocalport>'))
        ports.append(between(msg, '<tcpexternalport>', '</tcpexternalport>'))
            
        rid = int(between(msg, '<rid>', '</rid>'))
        session = between(msg, '<session>', '</session>')
            
        # convert to integers, remove duplicates
        ports = list(set(map(int, ports)))
        
        return (IPs, ports, rid, session)

    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        
        def format_message(message):
            message = message.encode('utf16')[2:] # skip byte order mark
            msg  = '\x80\xea\x00\x00\x08\x00' # \x00\x00
            msg += struct.pack("<L", len(message))
            msg += message
            return msg
        
        self.debug('Webcam message received', 'webcam')
        if 'SessionID' in slp.body:
            session_id = int(slp.body['SessionID'])
        else:
            session_id = int(bin.session_id)
        
        if int(session_id) != int(self.session_id):
            print "Not for us", self.session_id, session_id
            return
        
        # TODO: find out what this is exactly
        msg = str(unicode(message[58:], 'utf16', 'ignore'))
        
        if slp.method.startswith('BYE'):
            print "** Webcam canceled?"
            
            # notify the user
            p2p.emit('webcam-failed', int(self.session_id), 'cancelled')
            self.disconnect_handler(p2p)
        
        elif msg.startswith('syn'):
            self.debug('Received SYN', 'webcam')
            reply = format_message('syn\x00')
            self.emit('msnp2p-message-ready', reply, self.session_id)
            
            reply = format_message('ack\x00')
            self.emit('msnp2p-message-ready', reply, self.session_id)
            
        elif msg.startswith('ack'):
            self.debug('Received ACK', 'webcam')
            if self.producer:
                #FIXME: Find out what is rid and what should it be set to
                data = self.get_producer_xml(self.session_id, 342) + '\x00'
                reply = format_message(data)
                self.emit('msnp2p-message-ready', reply, self.session_id)
        
        elif msg.startswith('<producer>'):
            if self.received_producer_xml:
                # this shouldn't happen, but..
                self.debug('Received producer XML twice', 'webcam')
                return
            if self.received_viewer_xml:
                # this shouldn't happen, but..
                self.debug('Already received viewer XML', 'webcam')
                return
            
            self.received_producer_xml = True
            
            IPs, ports, rid, session = self.parse_producer_xml(msg)
            
            self.auth_data = 'recipientid=%d&sessionid=%s\r\n\r\n' % (rid, session)
            self.debug("Authentication data: " + self.auth_data, 'webcam')
            
            # send viewer data
            data = self.get_viewer_xml(session, rid) + '\x00'
            reply = format_message(data)
            self.emit('msnp2p-message-ready', reply, self.session_id)
            
            # exclude our own ip
            IPs = [ip for ip in IPs if ip != self.external_ip]
            
            # remove zeroes
            ports = [p for p in ports if p > 0]
            
            # combine each ip with each port
            hosts = [(ip, port) for ip in IPs for port in ports]
            self.debug('Hosts: ' + str(hosts), 'webcam')
            
            # start webcam thread
            # FIXME: what happens if webcam_thread is already started?
            self.webcam_thread = WebcamSocketHandler(hosts, self)
            self.webcam_thread.start()

        elif msg.startswith('<viewer>'):
            if self.received_viewer_xml:
                # this shouldn't happen, but..
                self.debug('Received viewer XML twice', 'webcam')
                return
            if self.received_producer_xml:
                # this shouldn't happen, but..
                self.debug('Already received producer XML', 'webcam')
                return
            
            self.received_viewer_xml = True

            recv = "receivedViewerData\x00"
            recv = format_message(recv)
            self.emit('msnp2p-message-ready', recv, self.session_id)
            
            IPs, ports, rid, session = self.parse_producer_xml(msg)
            
            self.auth_data = 'recipientid=%d&sessionid=%s\r\n\r\n' % (rid, session)
            self.debug('Received XML:' + msg, 'webcam')
            
            # exclude our own ip
            IPs = [ip for ip in IPs if ip != self.external_ip]
            
            # remove zeroes
            ports = [p for p in ports if p > 0]
            
            # combine each ip with each port
            hosts = [(ip, port) for ip in IPs for port in ports]
            self.debug('Hosts: ' + str(hosts), 'webcam')
            
            # start webcam thread
            # FIXME: what happens if webcam_thread is already started?
            self.webcam_thread = WebcamSocketHandler(hosts, self)
            self.webcam_thread.start()
            p2p.emit('webcam-ack', session)
        elif msg.startswith('receivedViewerData'):
            self.debug('Other client received our <viewer> xml', 'webcam')

        elif msg.startswith('ReflData'):
            print 'Got ReflData, connect to reflector?'
            
    def get_viewer_xml(self, session, rid):
        ip = '<tcpipaddress1>%s</tcpipaddress1>' % self.external_ip
        port = '6891'
        
        xml = '<viewer>'
        xml += '<version>2.0</version>'
        xml += '<rid>' + str(rid) + "</rid><udprid>" + str(int(rid)+1) + '</udprid>'
        xml += "<session>"+str(int(session))+"</session><ctypes>0</ctypes><cpu>2931</cpu>"
        xml += "<tcp>"
        xml += "<tcpport>" + port + "</tcpport><tcplocalport>" + port + "</tcplocalport>"
        xml += "<tcpexternalport>" + port + "</tcpexternalport>" + ip
        xml += "</tcp>"
        xml += "<udp>"
        xml += "<udplocalport>6899</udplocalport><udpexternalport>31863</udpexternalport>"
        xml += "<udpexternalip>" + ip +"</udpexternalip><a1_port>31859</a1_port>"
        xml += "<b1_port>31860</b1_port><b2_port>31861</b2_port>"
        xml += "<b3_port>31862</b3_port><symmetricallocation>1</symmetricallocation>"
        xml += "<symmetricallocationincrement>1</symmetricallocationincrement>"
        xml += "<udpversion>1</udpversion>"
        xml += "<udpinternalipaddress1>127.0.0.1</udpinternalipaddress1>"
        xml += "</udp>"
        xml += "<codec></codec>"
        xml += "<channelmode>1</channelmode>"
        xml += "</viewer>\r\n\r\n"
        
        self.debug('Viewer xml: ' + xml, 'webcam')
        return xml

    def get_producer_xml(self, session, rid):
        ip = '<tcpexternalip>%s</tcpexternalip>' % self.external_ip
        iip = '<tcpipaddress1>%s</tcpipaddress1>' % self.external_ip
        port = '6892'
        
        xml = '<producer>'
        xml += '<version>2.0</version>'
        xml += '<rid>' + str(rid) + "</rid>"
        xml += "<session>"+str(int(session))+"</session><ctypes>0</ctypes><cpu>2931</cpu>"
        xml += "<tcp>"
        xml += "<tcpport>" + port + "</tcpport><tcplocalport>" + port + "</tcplocalport>"
        xml += "<tcpexternalport>" + port + "</tcpexternalport>" + ip + iip
        xml += "</tcp>"
        xml += "<codec></codec>"
        xml += "<channelmode>1</channelmode>"
        xml += "</producer>\r\n\r\n"
        
        self.debug('Producer xml: ' + xml, 'webcam')
        return xml

class WebcamListenSocket(asyncore.dispatcher):
    '''Webcam server socket'''
    def __init__(self, host, port, receiver, handler):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.set_reuse_addr() 
        retry = 1
        while retry:
            try:
                self.bind((host, port))
                retry = 0
            except Exception, e:
                port += 1
                retry += 1
                print "Could not bind to port", port
                print "Exception:", type(e)
                print "Error -", e
                if retry > 50:
                    raise Exception("Could bind to port")
        self.host = host
        self.port = port
        self.listen(1)
        
        self.receiver = receiver
        self.handler = handler
    
    def handle_connect(self):
        pass
    
    def handle_error(self):
        tb = asyncore.compact_traceback()
        print "Socket error:", tb
        self.handler.close_socket(self)
    
    def handle_close(self):
        print "Listen socket closed"
        self.handler.close_socket(self)
    
    def handle_accept(self):
        socket, (host, port) = self.accept()

        print "Accepted webcam connection from: %s:%d" % (host, port)
        sock = WebcamSocket(host, port, self.receiver, self.handler, \
                WebcamSocket.AUTHENTICATING, socket)
        
        self.handler.add_socket(sock)
        self.handler.close_other_sockets(sock)
        
class WebcamSocket(asyncore.dispatcher):
    
    RECEIVING = 0
    CONNECTING = 1
    AUTHENTICATING = 2
    CONNECTED = 3
    
    def __init__(self, host, port, receiver, handler, state, sock=None):
        if sock:
            asyncore.dispatcher.__init__(self, sock)
        else:
            asyncore.dispatcher.__init__(self)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.host = host
        self.port = port
        self.receiver = receiver
        self.handler = handler
        self.state = state
        
        print "Connecting to %s:%d" % (self.host, self.port)
        self.connect((host, port))

        self.buffer = ''
        if state == self.CONNECTING:
            self.buffer += self.receiver.auth_data
        
        self.recv_buffer = ''
        self.tstart = 0

    def handle_connect(self):
        pass
    
    def handle_error(self):
        tb = asyncore.compact_traceback()
        print "Socket error, closing this socket"
        print tb
        self.handler.close_socket(self)
    
    def handle_close(self):
        print "Webcam socket closed"
        self.handler.close_socket(self)
    
    def read_buffer(self, bytes, peek=False):
        if len(self.recv_buffer) < bytes:
            return None
        
        data = self.recv_buffer[:bytes]
        if not peek:
            self.recv_buffer = self.recv_buffer[bytes:]
        
        return data

    def handle_read(self):
        self.recv_buffer += self.recv(16384)
       
        if self.state == self.RECEIVING:
            while True:
                header = self.read_buffer(24, peek=True)
                if header is None: return
            
                bytes = header[8:12]
                size, = struct.unpack("<L", bytes)
            
                frame = self.read_buffer(24 + size)
                if frame is None:
                    return
                    
                self.receiver.receive_frame(frame)
            
        elif self.state in (self.CONNECTING, self.CONNECTED):
            conn = "connected\r\n\r\n"
            
            buf = self.read_buffer(len(conn))
            if buf is None:
                return
                
            if buf == conn:
                if self.state == self.CONNECTING:
                    self.handler.close_other_sockets(self)
                    self.buffer += conn
                self.state = self.RECEIVING
            else:
                print "Expected 'connected' but got something else"
                self.close()
        
        elif self.state == self.AUTHENTICATING:
            buf = self.read_buffer(len(self.receiver.auth_data))
            if buf is None: return
            
            if buf == self.receiver.auth_data:
                print "Authentication OK"
                self.handler.close_other_sockets(self)
                self.buffer += "connected\r\n\r\n"
                
                self.state = self.CONNECTED
            else:
                print "Authentication FAILED! Got: %s, but need: %s!" % (buf, \
                    self.receiver.auth_data)
                self.close()

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        print self.buffer[:sent]
        self.buffer = self.buffer[sent:]
        
        print "Sent %d bytes to %s:%d" % (sent, self.host, self.port)
        self.handler.close_other_sockets(self)

class WebcamSocketHandler(Thread):
    def __init__(self, hosts, receiver):
        Thread.__init__(self)
        
        self.hosts = hosts
        self.receiver = receiver
        self.socket_map = {}
        self.listener = None
        self.connected = False
        self.main_sock = None
        
        print "Starting SocketHandler thread"
    
    def add_socket(self, sock):
        self.socket_map[sock] = sock
    
    def close_socket(self, sock):
        '''close socket and remove it from the socket map'''
        sock.close()
        if sock in self.socket_map:
            del self.socket_map[sock]
        if sock == self.main_sock:
            self.main_sock = None
            self.connected = False
        
    def close_other_sockets(self, sock):
        '''Connected, close the listening socket and all sockets except sock.
        sock can be None to close all sockets.'''
        
        if sock:
            print "Closing sockets except to %s:%d" % (sock.host, sock.port)
        else:
            print "Closing all webcam sockets..."

        if self.listener:
            self.close_socket(self.listener)

        map(self.close_socket, [s for s in self.socket_map.keys() if s != sock])
        self.main_sock = sock
        self.connected = True
    
    def run(self):
        self.listener = WebcamListenSocket('', 6891, self.receiver, self)
        self.add_socket(self.listener)
        
        for host, port in self.hosts:
            if self.connected:
                break
            
            sock = WebcamSocket(host, port, self.receiver, self, WebcamSocket.CONNECTING)
            self.add_socket(sock)
        
        asyncore.loop(map=self.socket_map)
        
        print "SocketHandler thread quit"
    
    def is_connected(self):
        return self.connected

    def get_main_sock(self):
        return self.main_sock
