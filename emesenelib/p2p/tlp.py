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

import base64
import gobject
import struct

# flag 0x10 set, file storage
import tempfile

# flag 0x10 not set, memory storage
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import emesenelib.common as common
import emesenelib.p2p.transfers as msn_p2p # TODO
import emesenelib.p2p.slp as msn_slp # TODO


# a better name?
class P2PUser(gobject.GObject):
    '''this class manages the creation of objects to handle the p2p
    messages and connect the necessary signals'''

    __gsignals__ = {
        # BinHeader, SLPMessage, message
        'invite-message-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # BinHeader, SLPMessage, message
        'msnp2p-message-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # BinHeader, file
        'msnp2p-file-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),

        # when a receiver/sender/whatever is created
        'new-p2p-session': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, )),
        
        # this signal is emited when the actual image is received
        # msnobj, str, sender
        'custom-emoticon-data-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # msnobj, str, sender
        'display-picture-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),

        # msnobj, str, sender
        'wink-data-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # session, context, sender 
        'file-transfer-invite': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # session, context, sender 
        'file-transfer-accepted': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),

        # session, context, sender 
        'file-transfer-canceled': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),

        # session, context, rc, sender
        'file-transfer-complete': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, ) * 4),
        
        # session, reason
        'transfer-failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, ) * 2),

        # session, offset
        'transfer-progress': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # session, sender, producer
        'webcam-invite': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_BOOLEAN,
          gobject.TYPE_PYOBJECT)),

        # This signal is sent when the other user accepts webcam
        'webcam-ack': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
        (gobject.TYPE_PYOBJECT,)),
         
        # session, sender 
        'webcam-accepted': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # session, sender 
        'webcam-canceled': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT,)),
        
        # session, reason
        'webcam-failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        
        # session, sender, frame
        'webcam-frame-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),

        # session, frame
        'webcam-frame-ready': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
         (gobject.TYPE_INT, gobject.TYPE_PYOBJECT, gobject.TYPE_INT, gobject.TYPE_INT)),
    }

    def __init__(self, manager, mail):

        gobject.GObject.__init__( self )

        self.manager = manager
        self.mail = str(mail)
        self.object_manager = manager.msn.msnObjectsManager
        self.last_requested_msnobj = None  # to avoid duplicates

        self.transports = []
        self._output_connected = False
        
        self.dchandler = None

        self.connect('display-picture-received', \
            self.manager.msn.on_display_picture_received)
        self.connect('custom-emoticon-data-received', \
            self.manager.msn.on_custom_emoticon_received)
        self.connect('wink-data-received', \
            self.manager.msn.on_wink_received)
        
        # multipart messages that haven't been received/sent completely yet
        # file object could be a file or a StringIO
        self.incoming_pending_messages = {} # {identifier: file object}
        self.outgoing_pending_messages = {} # [identifier: {dict}]
        self.outgoing_identifier_list = [] # this will evolve to priorities
        
        # per-user identifiers, let's see if this works
        self.my_identifier = msn_p2p.random_number(50000)
        #self.remote_identifier = 0  # i think we can avoid this better

    def __repr__(self):
        return "<P2P User: " + self.mail + ">"

    def _get_output_connected(self):
        return self._output_connected

    def _set_output_connected(self, value):
        '''Notifies all registered transports of the value change'''
        transports = self.transports
        if not transports:
            transports = [self.manager.msn.getSwitchboard(self.mail)]

        for transport in transports:
            transport.p2p_set_output_connected(value)

        self._output_connected = value

    output_connected = property(fget=_get_output_connected,
                                fset=_set_output_connected)
    
    #
    # transport layer stuff
    #

    def receive_message(self, body):
        '''called from the transport itself, body is the raw chunk,
        including headers, SLP, data, footer, etc'''

        bin_header = get_bin_header(body)

        if bin_header.flag == BinHeader.ACK_FLAG:
            return

        rc = None # if it's in a file

        if bin_header.total_data_size > bin_header.message_length and \
           bin_header.flag != BinHeader.RAK_FLAG: # don't parse these
            #partial message
            common.debug("partial message", "p2p")

            identifier = bin_header.identifier
            
            if bin_header.flag & BinHeader.EACH_FLAG:
                self.emit('transfer-progress', bin_header.session_id,
                    bin_header.data_offset)

            if identifier in self.incoming_pending_messages:
                fileobj = self.incoming_pending_messages[identifier]
                common.debug("follow up", "p2p")
                # follow-up message
                chunk = get_data_chunk(body, bin_header)
                fileobj.write(chunk)
                
                size = bin_header.data_offset + bin_header.message_length

                if size < bin_header.total_data_size:
                    # don't process, it's not ready yet
                    return

                common.debug("its complete!", "p2p")
                # it's complete!
                if bin_header.flag & BinHeader.STORAGE_FLAG:
                    rc = fileobj
                    body = None
                else:
                    # build a looong message. this is a bit ugly
                    bin_header.data_offset = 0
                    bin_header.message_length = bin_header.total_data_size
                    body = str(bin_header) + fileobj.getvalue() + '\x00' * 4
                
                del self.incoming_pending_messages[identifier]
            else:
                common.debug("first message", "p2p")
                # first message
                chunk = get_data_chunk(body, bin_header)
                if bin_header.flag & BinHeader.STORAGE_FLAG:
                    newfile = tempfile.TemporaryFile()
                else:
                    newfile = StringIO()
                newfile.write(chunk)

                self.incoming_pending_messages[identifier] = newfile
                return
        
        if bin_header.flag & BinHeader.STORAGE_FLAG and rc is None:
            # if the header says it's a file, it must be a file, even if
            # it is a single chunk. ok, yes, i know it's a hint, but
            # files and long invites can't be handled the same way
            rc = tempfile.TemporaryFile()
            rc.write(get_data_chunk(body, bin_header))

        if bin_header.flag != BinHeader.ACK_FLAG:
            common.debug("acking", 'p2p')
            self.send_acknowledge(bin_header)
        
        # session and flag 0 means slp
        if body and bin_header.session_id == 0 and (bin_header.flag & 0xff) == 0:
            try:
                slp = msn_slp.SLPMessage(body[48:-4])
            except msn_slp.SLPError:
                # since we are not 100% sure the condition is right
                # but we should reply with 500 internal server error
                slp = msn_slp.SLPMessage()
            #assert str(slp) == body[48:-4]
        else:
            slp = msn_slp.SLPMessage()

        if bin_header.flag & BinHeader.STORAGE_FLAG:
            common.debug(" ** FILE RECEIVED", 'p2p')

            # send the last progress
            if bin_header.flag & BinHeader.EACH_FLAG:
                self.emit('transfer-progress', bin_header.session_id,
                    bin_header.data_offset)

            # handle it
            self.emit('msnp2p-file-received', bin_header, rc)
        elif slp and slp.method.startswith('INVITE'):
            common.debug(" ** INVITE", 'p2p')
            self.emit('invite-message-received', bin_header, slp, body)
        else:
            common.debug("** MESSAGE", 'p2p')
            self.emit('msnp2p-message-received', bin_header, slp, body)

    def send_acknowledge(self, bin):
        '''Builds an acknowledge message'''
        ack = BinHeader()
        ack.session_id = bin.session_id
        ack.identifier = self.next_id()
        ack.total_data_size = bin.total_data_size
        ack.flag = BinHeader.ACK_FLAG
        ack.acknowledged_identifier = bin.identifier
        ack.acknowledged_unique_id = bin.acknowledged_identifier
        ack.acknowledged_data_size = bin.total_data_size
        self.send_message(self, str(ack) + msn_p2p.Base.FOOTER)
        
    def next_id(self):
        self.my_identifier += 1
        return self.my_identifier
    
    def do_invite_message_received(self, bin_header, slp, message):
        '''method called when an invite message is received
        in the switchboard'''

        if slp.content_type == msn_slp.SLPMessage.CONTENT_SESSION_REQ:
            if 'Context' not in slp.body:
                common.debug('no context in p2p invite', 'p2p')
                return
                
            if slp.body['EUF-GUID'] == msn_slp.SLPMessage.EUFGUID_FILE:
                # is a file
                rawcontext = slp.body['Context']
                context = msn_p2p.FTContext(base64.b64decode(rawcontext))
                # create a ft receiver here
                msn_p2p.FTReceiver(self, context, slp, bin_header)
                return
            elif slp.body['EUF-GUID'] == msn_slp.SLPMessage.EUFGUID_WEBCAM:
                # webcam invite
                rawcontext = slp.body['Context']
                msn_p2p.WebcamHandler(False, False, self, slp)
                return
            elif slp.body['EUF-GUID'] == msn_slp.SLPMessage.EUFGUID_WEBCAM_ASK:
                # webcam invite
                rawcontext = slp.body['Context']
                msn_p2p.WebcamHandler(False, True, self, slp)
                return
            else:
                data = self.get_data_by_context(slp.body['Context'])
                if data is not None:
                    msn_p2p.Sender(self, bin_header, slp, data)
                    return

        elif slp.content_type in (msn_slp.SLPMessage.CONTENT_TRANS_REQ,
                                  msn_slp.SLPMessage.CONTENT_TRANS_RESP):
            # its a direct connect invite
            if not self.dchandler:
                self.dchandler = msn_p2p.DCHandler(self, bin_header, slp)
            else:
                self.dchandler.handle_invite(bin_header, slp)
            return

        common.debug('invalid invite message', 'p2p')

    def get_data_by_context(self, context):
        '''receive a base64 encoded msnobj and try to
        return a Buffer instace with the data, if
        the msnobj doesnt exist, return None'''
        
        try:
            msnobj = self.object_manager.getByContext(context)
            try:
                return open(msnobj.filename, 'rb')
            except IOError:
                return None
        except (TypeError, AttributeError):
            common.debug('invalid msnobj in get_data_by_context', 'p2p')
            return None
        
    def send_message(self, obj, message):
        '''method called when a p2p message is ready to be sent
        it will choose between switchboard or direct connection,
        and start those connections if needed'''
        
        transport = self.get_transport()
        
        if len(message) > transport.MESSAGE_LIMIT + 52:
            # message too big
            bin_header = get_bin_header(message)
            rc = StringIO(message[48:-4])
            footer = message[-4:]
            return self.on_msnp2p_file_ready(obj, None,
                rc, footer, None, bin_header)
        
        transport.p2p_send(message, self.mail)
    
    def on_msnp2p_message_ready(self, obj, slp_message, session_id):#XXX footer
        '''called when a p2p/slp message is ready to be sent'''
        
        body = str(slp_message)
        
        header = BinHeader()
        header.session_id = int(session_id)
        header.identifier = self.next_id()
        header.acknowledged_identifier = msn_p2p.random_number(50000)
        header.total_data_size = len(body)
        header.message_length = len(body)
        self.send_message(obj, \
            str(header) + body + msn_p2p.Base.FOOTER)

    def on_msnp2p_file_ready(self, obj, flags, data, footer, callback,
                             baseheader=None):
        '''this method starts sending a file via p2p, abstracting most stuff
        like offsets, select() on sockets, etc'''
        
        # go to the end, get the size, go back to the start
        # i tested it in a 134mb file after flushing disk cache, it's fast
        data.seek(0, 2)
        data_size = data.tell()
        data.seek(0, 0)

        identifier = self.next_id()
        if baseheader is None:
            header = BinHeader()
            header.session_id = int(obj.session_id)
            header.identifier = identifier
            header.flag = flags
            header.acknowledged_identifier = msn_p2p.random_number(50000)
        else:
            header = baseheader
        
        header.identifier = identifier
        header.total_data_size = data_size
        
        if obj:
            obj.current_transfer = int(identifier)
        
        self.outgoing_pending_messages[identifier] = \
            (header, data, footer, callback)
        self.outgoing_identifier_list.append(identifier)
        
        # this allows the mainloop work while sending data
        self.output_connected = True

    def output_ready(self, transport):
        '''BITSHUFFLE FTW'''
        if not self.outgoing_identifier_list:
            self.output_connected = False
            return
        identifier = self.outgoing_identifier_list.pop(0)
        self.outgoing_identifier_list.append(identifier)
        if not self.send_chunk(identifier):
            self.outgoing_identifier_list.remove(identifier)
            if not self.outgoing_identifier_list:
                self.output_connected = False

    def send_chunk(self, identifier):
        '''Send the next chunk of a pending message'''
        if identifier not in self.outgoing_pending_messages:
            return False

        transport = self.get_transport()

        header, data, footer, callback = \
            self.outgoing_pending_messages[identifier]

        header.data_offset = data.tell()
        chunk = data.read(transport.MESSAGE_LIMIT)
        header.message_length = len(chunk)
        #header.print_fields()
        self.emit("transfer-progress", header.session_id, header.data_offset)
        
        if chunk:
            self.send_message(None, str(header) + chunk + footer)
            return True
        else:
            # TODO: handle when we receive a NAK after this
            #       ...and handle naks
            if callback:
                callback(self)

            if identifier in self.outgoing_pending_messages:
                del self.outgoing_pending_messages[identifier]
            return False
    
    #
    # transports management stuff
    #

    def get_transport(self):
        '''Returns an usable transport from the list.
        That list rotates by default.
        If it's empty, a (new) switchboard is returned (which is added
        to the transport list when it's ready'''

        if self.transports:
            transport = self.transports.pop(0)
            self.transports.append(transport)
            return transport
        return self.manager.msn.getSwitchboard(self.mail)
    
    def register(self, transport):
        '''Adds a working transport to the list'''
        transport.p2p_set_output_connected(self.output_connected)
        self.transports.append(transport)

    def unregister(self, transport):
        '''Removes a transport from the list'''
        transport.p2p_set_output_connected(False)
        if transport in self.transports:
            self.transports.remove(transport)

    def start_new_conv(self):
        '''Tells the GUI that a new conv started
        A bit unstable, may open more than one window''' #FIXME, h4x
        switchboard = self.manager.msn.getSwitchboard(self.mail)
        self.manager.msn.emit('new-conversation', self.mail, switchboard)

class BinHeader(object):
    '''This class represents the bin header'''
 
    FORMAT = '<LLQQLLLLQ'
 
    NO_FLAG = 0x0           # no flags specified
    NAK_FLAG = 0x1          # negative acknowledge
    ACK_FLAG = 0x2          # acknowledge
    RAK_FLAG = 0x4          # request acknowledge
    BINERROR_FLAG = 0x8     # error on the binary level
    STORAGE_FLAG = 0x10     # if set it should be saved in a file
    EACH_FLAG = 0x20        # if we should emit a progress signal
    CANCEL_FLAG = 0x40      # cancel
    ERROR_FLAG = 0x80       # error
    FILE_FLAG = 0x1000000  # data of a file 

    def __init__(self, data=None):
        '''Constructor'''
        self.session_id = 0               # dw
        self.identifier = 0               # dw
        self.data_offset = 0              # qw
        self.total_data_size = 0          # qw
        self.message_length = 0           # dw
        self.flag = 0                     # dw
        self.acknowledged_identifier = 0  # dw1
        self.acknowledged_unique_id = 0   # dw2
        self.acknowledged_data_size = 0   # qw1

        if data != None:
            self.fill(data)
    
    def print_fields(self):
        '''print the binary fields'''
        print
        print 'SessionID:               ' + str(self.session_id)
        print 'Identifier:              ' + str(self.identifier)
        print 'Data offset:             ' + str(self.data_offset)
        print 'Total data size:         ' + str(self.total_data_size)
        print 'Message length:          ' + str(self.message_length)
        print 'Flag:                    ' + str(self.flag)
        print 'Acknowledged identifier: ' + str(self.acknowledged_identifier)
        print 'Acknowledged unique ID:  ' + str(self.acknowledged_unique_id)
        print 'Acknowledged data size:  ' + str(self.acknowledged_data_size)
        print
        
    def fill(self, data):
        '''Parse and save in attributes the contents of data'''
        
        # from __future__ import braces
        (
            self.session_id,
            self.identifier,
            self.data_offset,
            self.total_data_size,
            self.message_length,
            self.flag,
            self.acknowledged_identifier,
            self.acknowledged_unique_id,
            self.acknowledged_data_size
        ) = struct.unpack(BinHeader.FORMAT, data[:48])

    def __str__(self):
        '''return the representation of this object'''
        
        return struct.pack(BinHeader.FORMAT,
            self.session_id,
            self.identifier,
            self.data_offset,
            self.total_data_size,
            self.message_length,
            self.flag,
            self.acknowledged_identifier,
            self.acknowledged_unique_id,
            self.acknowledged_data_size)	
        
def get_bin_header(message):
    '''receive a msnp2p message and return a BinHeader
    instance with the bin header of the message
    if you send crap, you will get a nice BinHeader full
    of crap! ;).'''

    return BinHeader(message[:48])

def get_data_chunk(message, bin):
    '''return the data chunk in message, an empty string if
    something went bad'''

    try:
        return message[48:48 + bin.message_length]
    except IndexError:
        return ''
    
def compare_binheaders(b1, b2):
    '''print the binary fields'''
    def compare_field(name, attr):
        print '%-17s %10s %10s' % (name, getattr(b1, attr), getattr(b2, attr))

    print '-------------------------------------------\n'
    compare_field('SessionID:', 'session_id')
    compare_field('Identifier:', 'identifier')
    compare_field('Data offset:', 'data_offset')
    compare_field('Total data size:', 'total_data_size')
    compare_field('Message length:', 'message_length')
    compare_field('Flag:', 'flag')
    compare_field('Ackd identifier:', 'acknowledged_identifier')
    compare_field('Ackd unique ID:', 'acknowledged_unique_id')
    compare_field('Ackd data size:', 'acknowledged_data_size')
    print '-------------------------------------------\n'


