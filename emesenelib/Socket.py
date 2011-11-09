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

'''This module provides "interfaces to connect to external hosts",
including only MSNP sockets by now. (future: http[s], DC)
'''

import sys
import time
import Queue
import socket
import select
import gobject
import httplib
import threading
import traceback
import base64
import string

# faster than concatenation
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import common

# oh shi-
PAYLOAD_COMMANDS = ['UBX', 'GCF', 'MSG', 'NOT', 'ADL', 'RML']
IGNORE_COMMANDS = ['SBS']

class BaseConnection(gobject.GObject):
    '''This is the base class to all sockets (including http method ones),
    and higher-level connections (http or https)
    The signals below behave similar to io_add_watch in a normal socket, but
    exposing a simple, unified interface for all different socket types'''
    # Prototype weak gobject implementation included.
    
    __gsignals__ = {
        'input': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'hangup': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'output': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self._hung = False
        self._signals = {'input': [], 'hangup': [], 'output': []}

    def connect(self, name, *args):
        '''Connects a signal and stores the identifier'''
        retval = gobject.GObject.connect(self, name, *args)
        self._signals[name].append(retval)
        return retval

    def disconnect(self, identifier):
        if identifier:
            gobject.GObject.disconnect(self, identifier)
        for signal in self._signals:
            if identifier in self._signals[signal]:
                self._signals[signal].remove(identifier)

    def disconnectAll(self):
        '''Disconnects all the signal ids stored'''
        for identifiers in self._signals.values():
            for identifier in identifiers:
                self.disconnect(identifier)
    
    def hangup(self):
        if not self._hung:
            self._hung = True
            self.emit('hangup')
            self.close()
            self.disconnectAll()


class BaseSocket(BaseConnection):
    '''This is the base class to Socket and HTTPSocket
    Some high-level methods are implemented here too'''
    
    # override me
    ping_enabled = None

    def __init__(self, host, port):
        BaseConnection.__init__(self)

        self.error = ''
        # the buffer to store the received data
        self._buffer = ''
        self._host = host
        self._port = port
        
        # transaction ID
        self.tid = 1

        # ping times
        self.lastsent = int(time.time())
        self.lastpng = 0
        self.lastqng = 0

        # max time in seconds between PNG and QNG
        self.max_ping_delay = 10
        self.secs_between_pings = 20

        self.do_not_ping = True
    
    def sendCommand(self, command, params=''):
        '''send a command through the socket and increment the tid'''
        
        if params != "":
            text = "%s %s %s\r\n" % (command, self.tid, params)
        else:
            text = "%s %s\r\n" % (command, self.tid)
            
        self.tid += 1
        self.send(text)
        return self.tid
        
    def sendPayloadCommand(self, command, params, payload):
        '''send a command that has an indicator of the body length'''
            
        if type(payload) == unicode:
            payload = str(payload.encode('utf-8'))
        
        text = command + " " + str(self.tid) + " "
        if params != '':
            text += params + " "
        text += str(len(payload)) + '\r\n' + payload
        
        self.tid += 1
        self.send(text)
        return self.tid
        
    def send(self, text):
        pass

    def receiveCommand(self):
        return ('', 0, '')
        
    def receivePayload(self):
        return ''

    def close(self):
        pass

    def ping(self):
        pass

    def onQng(self, tid):
        pass


class Socket(BaseSocket):
    '''This represents a MSNP protocol socket over plain TCP'''
    
    ping_enabled = True

    def __init__(self, host, port):
        BaseSocket.__init__(self, host, port)
        
        self.inQueue = Queue.Queue(0)
        self.outQueue = Queue.Queue(0)
        
        self.thread = SocketThread(self, host, port)
        self.thread.start()
        
    def send(self, text):
        '''Sends raw bytes'''
        common.debug(">>> " + text, 'socket')
        self.lastcmd = int(time.time())
        self.thread.send(text)

    def receiveCommand(self):
        '''Parses the receive() return value
        in a (command, tid, params) tuple'''
        list = self.thread.get().split(' ', 2)
        
        command, tid, params = ('', '0', '')
        
        if len(list) >= 1: command = list[0]
        if len(list) >= 2: tid = list[1]
        if len(list) >= 3: params = list[2]
        
        return (command, tid, params)
        
    def receivePayload(self, length):
        '''Yay, cheap!'''
        return self.thread.get()

    def ping(self):
        '''ping the server if idle, errors are handled by core.py'''
        if not self.do_not_ping and \
           (int(time.time()) - self.lastcmd) > self.secs_between_pings:
            self.send('PNG\r\n')
            self.lastpng = int(time.time())

    def onQng(self, tid):
        '''called by core.process()'''
        self.lastqng = int(time.time())
        self.max_ping_delay = int(int(tid) * 85 / 100)
        self.secs_between_pings = int(int(tid) * 9 / 10)
        
    def close(self):
        self.thread.quit()
        self.disconnectAll()
        self.thread.join()
        self.thread = None


class BaseThread(threading.Thread):
    def __init__(self, parent):
        '''class constructor'''
        threading.Thread.__init__(self)
        
        self.parent = parent

        self.input = parent.inQueue
        self.output = parent.outQueue

        self.open = True

        self.setDaemon(True)

    def send(self, data):
        '''add data to the input queue'''
        self.input.put(data)

    def get(self):
        '''return data from the output queue (received data)'''
        return self.output.get()

    def quit(self):
        try:
            while True:
                self.input.get(True, 0.01)
        except Queue.Empty:
            pass
        self.input.put('quit')
        self.open = False
        self.signal('hangup')
        common.debug(self.getName() + ' quit')

    def signal(self, name):
        '''sends a signal to the parent object safely
        (i hope)'''
        def emit():
            self.parent.emit(name)
            return False
        gobject.idle_add(emit, priority=gobject.PRIORITY_DEFAULT)


class SocketThread(BaseThread):
    '''a socket that runs on a thread, it reads the data and put it on the 
    output queue, the data to be sent is added to the input queue'''

    def __init__(self, parent, host, port):
        BaseThread.__init__(self, parent)

        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def run(self):
        '''error handler for the real do_run function
        a decorator is fine too'''

        common.debug(self.getName() + ' start')
        try:
            self.do_run()
        except Exception, e:
            traceback.print_exception(*sys.exc_info())
            self.parent.error = str(e)
            self.signal('hangup')
        common.debug(self.getName() + ' end')

    def do_run(self):
        '''the main method of the socket, wait until there is something to 
        send or there is something to read, if there is something to send, get 
        it from the input Queue, wait until we can send it and send it, if 
        there is something to read, read it and put it on the output queue'''
        self.socket.connect((self.host, self.port))

        while True:
            # see if we can send or read something
            (iwtd, owtd) = select.select([self], [self], [])[:2]
            
            # if we can read, we try to read
            if iwtd:
                if not self._receive():
                    return
            
            if owtd:
                try:
                    input_ = self.input.get(True, 0.05)
                except Queue.Empty:
                    continue

                if input_ == 'quit':
                    return
                else:
                    try:
                        sent = self.socket.send(input_)
                        if sent == 0:
                            self.signal('hangup')
                    except socket.error:
                        self.signal('hangup')
                        return

    def _receive(self):
        '''receive data from the socket'''
        data = self._readline()
        # if we got something add it to the output queue
        if data:
            #print 'received', data
            self.output.put(data)
            common.debug("<<< " + data, 'socket')

            if data.split()[0] in PAYLOAD_COMMANDS:
                # this is supposed to block
                try:
                    payload = self.receive_fixed_size(int(data.split()[-1]))
                    self.output.put(payload)
                except ValueError:
                    pass   # not a payload command (like some ADL)
            self.signal('input')
            return True
        else:
            return False

    def _readline(self):
        '''read until new line'''
        output = StringIO()

        try:
            chunk = self.socket.recv(1)
        except socket.error:
            self.signal('hangup')
            return None

        while chunk != '\n' and chunk != '':
            output.write(chunk) 
            try:
                chunk = self.socket.recv(1)
            except socket.error:
                self.signal('hangup')
        
        if chunk == '\n':
            output.write(chunk)
        if chunk == '':
            self.signal('hangup')

        output.seek(0)
        return output.read()[:-2]

    def receive_fixed_size(self, size):
        '''receive a fixed size of bytes, return it as string'''
        output = StringIO()
        outputlen = 0

        while outputlen < size:
            try:
                data = self.socket.recv(size - outputlen)
                outputlen += len(data)
                output.write(data)
            except socket.error:
                self.signal('hangup')

        output.seek(0)

        return output.read()

    def fileno(self):
        '''method that is used by select'''
        return self.socket.fileno()


class Proxy:
    '''Just a class to hold the proxy data'''
    
    def __init__(self, host='', port='80', user='', password=''):
        '''constructor of the class, just set the class attributes'''
        self.host = host
        self.port = str(port)
        self.user = user
        self.password = password

class HTTPSocket(BaseSocket):
    '''This class represent an abstraction of HTTPMethod that has the
    same methods that the Socket class to make easy the use of this
    on core class, it behaves the same way'''
    
    ping_enabled = False

    def __init__(self, host, port, proxy=None, serverType='NS'):
        BaseSocket.__init__(self, host, port)
        
        self.inQueue = Queue.Queue(0)
        self.outQueue = Queue.Queue(0)
        
        self.responseBuffer = ''
        self.thread = HttpRequestManager(self, host, port, proxy, serverType)
        self.thread.start()
        
        self.hasReceived = False
        
    def send(self, text):
        '''send text with no format, this is usefull for commands like OUT\r\n
        also its used internally'''
        
        common.debug(">>> " + text, 'socket')
        self.inQueue.put(text)
    
    def _getBuffer(self, wait=False):
        if self.responseBuffer == '':
            try:
                newbuffer = self.outQueue.get(True, 0.01)
            except Queue.Empty:
                return ''
            self.responseBuffer = newbuffer
        
    def receiveCommand(self):
        '''Parses the receive() return value
        in a (command, tid, params) tuple'''
        
        self._getBuffer()
        if self.responseBuffer.find('\r\n') != -1:
            received, self.responseBuffer = \
                self.responseBuffer.split('\r\n', 1)
        else:
            received = self.responseBuffer
            self.responseBuffer = ''

        common.debug("<<< " + received, 'socket')
        self.lastcmd = int(time.time())
        
        list = received.split(' ', 2)

        command, tid, params = ('', '0', '')
        if len(list) >= 1: command = list[0]
        if len(list) >= 2: tid = list[1]
        if len(list) >= 3: params = list[2]
        
        return (command, tid, params)
        
    def receivePayload(self, length):
        '''receive a number of characters from an earlier command'''
        length = int(length) 
        received = 0
        buffer = []
        
        while received < length:
            self._getBuffer(True)
            bytes = length - received
            chunk, self.responseBuffer = self.responseBuffer[:bytes], \
                                         self.responseBuffer[bytes:]
            received += len(chunk) + 4  # not concatenation
            buffer.append(chunk)
        
        return ''.join(buffer)

    def close(self, *args):
        '''called on logout'''
        self.thread.quit()
        self.disconnectAll()
        

class HttpRequestManager(BaseThread):
    '''This class make the request via Http method in a thread'''
    
    def __init__(self, parent, destip, port, proxy, desttype):
        '''Contructor'''
        BaseThread.__init__(self, parent)

        self.host = 'gateway.messenger.hotmail.com'
        self.port = port
        self.proxy = proxy
        self.type = desttype
        self.path = '/gateway/gateway.dll?Action=open&Server=' + desttype + \
            '&IP=' + destip
        
        self.connection = None
        self.data = ''
        self.sessionID = ''

        self.dataWaiting = False # indicate if some data is waiting
                                 # if false and receive is called, we call poll
        
        if self.proxy.host:
            addr = self.proxy.host + ':' + self.proxy.port
        elif desttype == 'NS':
            addr = 'gateway.messenger.hotmail.com:80'
        else:
            addr = destip + ':80'
        self.addr = addr
        self.connection = None
    
    def run(self):
        '''the thread main loop'''

        self.connection = httplib.HTTPConnection(self.addr)

        while self.open:
            try:
                req = self.input.get(True, 3)
            except Queue.Empty:
                req = 'poll'

            common.debug(self.getName() + ' doing ' + \
                str(req)[:40].strip() + '...', 'psocket')

            if req == 'poll':
                data = self.poll()
                if not self.output.empty():
                    self.signal('input')
            elif req == 'quit':
                return
            else:
                data = self.request(payload=req)

            while len(data) > 0:
                tmp = data.split('\r\n', 1)
                if len(tmp) == 1:
                    tmp = [tmp[0], '']
                line, data = tmp
                linesplit = line.split()
                if linesplit[0] not in IGNORE_COMMANDS:
                    self.output.put(line)
                if linesplit[0] in PAYLOAD_COMMANDS:
                    try:
                        size = int(linesplit[-1])
                        payload, data = data[:size], data[size:]
                        self.output.put(payload)
                    except ValueError:
                        pass  # not a payload command

                self.signal('input')
    
    def poll(self):
        return self.request(path='/gateway/gateway.dll?'
            'Action=poll&SessionID=' + self.sessionID)
    
    def request(self, method='POST', path=None, payload=''):

        if path is None:
            path = self.path

        url = 'http://' + self.host + path

        def dorequest():
            common.debug('>>> '+url)
            self.connection.putrequest(method, url,
                                       skip_accept_encoding=True,
                                       skip_host=True)
            
            if self.proxy.user:
               userauth = "%s:%s" % (self.proxy.user, self.proxy.password)
               enc_userauth = string.replace(base64.encodestring(userauth),"\n","")
               self.connection.putheader("Proxy-Authorization", "Basic %s" % enc_userauth)
            self.connection.putheader("Accept", "*/*")
            self.connection.putheader("Accept-Language", "en-us")
            self.connection.putheader("User-Agent", "MSMSGS")
            self.connection.putheader("Host", self.host)
            self.connection.putheader("Proxy-Connection", "Keep-Alive")
            self.connection.putheader("Connection", "Keep-Alive")
            self.connection.putheader("Pragma", "no-cache")
            self.connection.putheader("Content-Type",
                "application/x-msn-messenger")
            self.connection.putheader("Content-Length", str(len(payload)))
            self.connection.endheaders()
            self.connection.send(payload)
            return self.getHttpResponse()
        
        for i in range(5):
            # try up to 5 times. if it keeps failing, close
            try:
                return dorequest()
            except Exception, e:
                traceback.print_exception(*sys.exc_info())
            self.connection.close()
            time.sleep(2)
            self.connection.connect()

        self.quit()
        return 'OUT'
        
    def getHttpResponse(self):
        response = self.connection.getresponse()
        
        text = response.read().strip()
        if response.status == 500:
            common.debug("500 internal server error", "psocket")
            self.quit()
            return 'OUT'
        elif response.status != 200:
            raise httplib.HTTPException("Server not available")
        try:
            # this header contains important information
            # such as the IP of the next server we should connect
            # and the session id assigned
            data = response.getheader('x-msn-messenger', '')
            if data.count("Session=close"):
                common.debug("Session closed", "socket")
                self.quit()
                return 'OUT'

            # parse the field
            self.sessionID = data.split("; GW-IP=")[0].replace("SessionID=", "")
            self.gatewayIP = data.split("; ")[1].replace("GW-IP=", "")
            self.host = self.gatewayIP
            self.path = "/gateway/gateway.dll?SessionID=" + self.sessionID
        except Exception,e:
            common.debug('In getHttpResponse: ' + str(e), 'socket')
            common.debug('Data: "%s"' % data, 'socket')
        return text
        
