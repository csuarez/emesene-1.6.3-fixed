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

import emesenelib.common as common

import sys
import Queue
import threading
import httplib
import string
import base64
import socket
import os

# gzipped requests ftw!
import StringIO, gzip

HAVE_PY25 = 0
if sys.version_info[1] > 5:
    import ssl
else:
    HAVE_PY25 = 1
    
requestQueue = Queue.Queue( 0 )
responseQueue = Queue.Queue( 0 )

def put(request):
    global requestQueue
    if isinstance(request, SoapRequest):
        common.debug("soap.manager.put(%s)" % request, "soap")
    requestQueue.put(request)
    
def get():
    global responseQueue
    retval = responseQueue.get()
    if isinstance(retval, SoapRequest):
        common.debug("soap.manager.get() --> %s" % retval, "soap")
    return retval

def getNoBlock():
    global responseQueue
    
    return responseQueue.get(True, 0.01)

def process():
    '''run the callbacks if some response is in responseQueue'''
    global responseQueue
    
    while True:
        try:
            response = getNoBlock()
        except Queue.Empty:
            break

        common.debug("soap.manager.process(): %s" % response, "soap")
                    
        if response.callback:
            if hasattr(response.callback, '__name__'):
                common.debug("soap.manager.process(): Calling %s()" % \
                    response.callback.__name__, "soap")
            response.callback(response, *response.args)

    return True

def do_request(proxy, action, host, port, path, body, callback=None, args=(),
               sync=False):
    '''Adds a new request to the queue and optionally waits for response'''
    put(SoapRequest(proxy, action, host, port, path, body,
        callback=callback, args=args))

    if sync:
        response = get()

        # since i don't rely on get(), i'll just use the attributes in the
        # response object, and not the parameters
        if response and response.callback:
            response.callback(response, *response.args)

def repeat_request(request, body):
    '''Repeats a request with a different body'''
    put(SoapRequest(request.proxy, request.action, request.host, request.port, request.path,
        body, request.callback))

class SoapException(Exception):
    pass

class SoapRequest(object):
    '''This class represents a soapRequest'''
    
    def __init__(self, proxy, action, host, port, path, body, callback=None, args=()):
        '''Constructor'''
        
        self.proxy = proxy
        self.action = action
        self.host = host
        self.port = port
        self.path = path
        self.body = body
        self.callback = callback
        self.args = args
        self.extraCookie = ''
        self.errorCount = 0
        self.status = (0, '')

    def __repr__(self):
        action = self.action.split("/")[-1]
        if self.status != (0, ''):
            return '<SoapRequest %s %s>' % (action, self.status)
        else:
            return '<SoapRequest %s>' % action

class SoapManager( threading.Thread ):
    '''This class is a thread that wait for soapRequest in the requestQueue
    and make the request, then add the response to the responseQueue'''
       
    def __init__( self, msn ):
        threading.Thread.__init__( self )

        # this is wrong
        self.msn = msn

    def process( self ):
        try:
            return process()
        except:
            self.msn.emit('exception', sys.exc_info())

    def destroy( self ):
        global requestQueue, responseQueue
        try:
            while True:
                tmp = responseQueue.get(True, 0.01)
                for i in dir(tmp):
                    if not i.startswith('_'):
                        setattr(tmp, i, None)
        except Queue.Empty:
            pass

        try:
            while True:
                tmp = requestQueue.get(True, 0.01)
                for i in dir(tmp):
                    if not i.startswith('_'):
                        setattr(tmp, i, None)
        except Queue.Empty:
            pass
        
        put('quit')
        self.msn = None

    def run( self ):
        global requestQueue, responseQueue

        req = None

        while True:
            if not req:
                req = requestQueue.get()
            
            if req == 'quit' or self.msn == None:
                break
            else:
                try:
                    responseQueue.put(self.makeSoapRequest(req))
                except Exception, e:
                    common.debug('soap.manager run() Error: ' + str(e), 'soap')
                    if req.errorCount < 2:
                        req.errorCount += 1
                        continue # retry
            req = None

        return False
        
    def makeSoapRequest(self, soapRequest, retry=True):
        common.debug('soap.manager makeSoapRequest(): %s' % soapRequest, 'soap')
        if soapRequest.host in self.msn.tokens:
            soapRequest.body = soapRequest.body.replace("&tickettoken;",
                                  self.msn.tokens[soapRequest.host]['security']\
                                  .replace('&', '&amp;'))
        # TODO: change to putheader
        headers = {
            "SOAPAction": soapRequest.action,
            "Content-Type": "text/xml; charset=utf-8",
#            "Cookie": "MSPAuth=" + self.msn.MSPAuth + ";MSPProf=" +
#                self.msn.MSPProf + soapRequest.extraCookie,
            "Host": soapRequest.host,
            "Content-Length": str(len(soapRequest.body)),
            "User-Agent": "MSN Explorer/9.0 (MSN 8.0; TmstmpExt)",
            "Connection": "Keep-Alive",
            "Cache-Control": "no-cache",
            "Accept-encoding": "gzip", # highly improves bandwidth usage
        }
        

        conn = None
        response = None
        
        if soapRequest.proxy and soapRequest.proxy.host:
            common.debug('>>> using proxy host: '+soapRequest.proxy.host)
            proxy_connect = 'CONNECT %s:%s HTTP/1.0\r\n'%(soapRequest.host, str(soapRequest.port))
            user_agent = 'User-Agent: python\r\n'
            if soapRequest.proxy.user:
                common.debug('>>> using proxy auth user: '+soapRequest.proxy.user)
                # setup basic authentication
                user_pass = base64.encodestring(soapRequest.proxy.user+':'+soapRequest.proxy.password).replace('\n','')
                proxy_authorization = 'Proxy-authorization: Basic '+user_pass+'\r\n'
                proxy_pieces = proxy_connect+proxy_authorization+user_agent+'\r\n'
            else:
                proxy_pieces = proxy_connect+user_agent+'\r\n'
            # now connect, very simple recv and error checking
            proxy = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            proxy.connect((soapRequest.proxy.host,int(soapRequest.proxy.port)))
            proxy.sendall(proxy_pieces)
            response = proxy.recv(8192) 
            status=response.split()[1]
            if status!=str(200):  raise ValueError,'Error status=%s' % str(status)
            # trivial setup for ssl socket
            if HAVE_PY25:
                sslconn = socket.ssl(proxy, None, None)
                sock = httplib.FakeSocket(proxy, sslconn)
            else:
                sock = ssl.wrap_socket(proxy, None, None)
            conn = httplib.HTTPConnection('localhost')
            conn.sock = sock
        else:
            if soapRequest.port == 443:
                conn = httplib.HTTPSConnection(soapRequest.host, soapRequest.port)  
            else:
                conn = httplib.HTTPConnection(soapRequest.host, soapRequest.port)
            
        if soapRequest.action == 'http://www.msn.com/webservices/storage/w10/CreateDocument' or \
            soapRequest.action == 'http://www.msn.com/webservices/storage/w10/DeleteRelationships':
            #print soapRequest.path, soapRequest.body, headers
            if os.name == "nt":
                tempfile = os.environ['TEMP'] + os.sep + "createdocumentsoap.txt"
                tempfile = unicode(tempfile)
            else:
                tempfile = '/tmp/createdocumentsoap.txt'
            f = open(tempfile, 'w')
            f.write(soapRequest.body)
            f.close()
        conn.request("POST", soapRequest.path, soapRequest.body, headers)
        response = conn.getresponse()
            
        data = response.read()
        isGzipd = response.getheader('Content-Encoding', '')
        if isGzipd == 'gzip':
            # data is gzipped, unzipit!
            cstream = StringIO.StringIO(data)
            gzpr = gzip.GzipFile(fileobj=cstream)
            data = gzpr.read()
            
        soapResponse = SoapRequest(soapRequest.proxy, soapRequest.action,
            soapRequest.host, soapRequest.port, soapRequest.path,
            data, soapRequest.callback, soapRequest.args)
    
        soapResponse.status = (response.status, response.reason)
        if soapResponse.body.count('TweenerChallenge') or \
           soapResponse.body.count('LockKeyChallenge'):
            retry = False

        if retry and soapResponse.body.count('AuthenticationFailure') or \
                     soapResponse.body.count('PassportAuthFail'):
            self.msn.passportReAuth()
            soapResponse = self.makeSoapRequest(soapRequest, False)
        return soapResponse
