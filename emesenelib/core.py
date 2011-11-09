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
import sys
import hashlib
import time
import socket
import urllib
import gobject
import httplib
import urlparse
import traceback

HAVE_PY25 = 0
if sys.version_info[1] > 5:
    import ssl
else:
    HAVE_PY25 = 1

import mbi
import Socket
import MsnOIM
import Msnobj
import ContactData
import Switchboard
import SignalHandler
import ProfileManager
from XmlParser import SSoParser
from UbxParser import UbxParser

import p2p.tlp
import soap.manager
import soap.templates

import common
import string
import base64
# gzipped requests ftw!
import StringIO, gzip

class Msnp(ProfileManager.ProfileManager):
    '''This class give support to the MSNP15 protocol to use the MSN Messenger network'''

    __gsignals__ = {
        'user-list-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        # when an error happen this signal is emitted with the error name
        # and the description
        'error' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        # an exception in msn.process, the arg is an exception object
        'exception' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        # when we receive a message, the parameter is the user mail
        'message-received' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connection-problem' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        # disconnected happen when someone login in the same account
        'disconnected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        # disconnect is when a socket error happens
        'connection-closed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'challenge' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'initial-status-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),

        # XXX there is no emit for this signal, wtf?
        # command, tid, params
        'status-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        # command, tid, params
        'status-online' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        # command, tid, params
        'status-offline' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'switchboard-invitation' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        # command, tid, params, email, nick
        'add-notification' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING,
             gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'remove-notification' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, \
             gobject.TYPE_STRING)),
        'personal-message-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'server-message' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'user-disconnected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'logout' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'account-unconfirmed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        # signal emited when we change our nick, the parameters are the old and
        # the new nickname
        'self-nick-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'self-status-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        'self-personal-message-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'self-current-media-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)),
        # the filename of the new avatar and a boolean indication if it's changed
        # after retrieving it from Msn's server (True) or set by the user (False)
        'self-dp-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_BOOLEAN)),

        'new-conversation' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)),
        'new-switchboard' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        'nudge-received' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),

        'initial-mail-notification' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),
        # From, FromAddr, Subject, MessageURL , PostURL, id
        'new-mail-notification' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'mail-movement-notification' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),

        'nick-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        # email, status
        'contact-status-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
         # the bolean value on msnobj-changed indicate if he was offline
         # to not request all the avatars when we come online
        'msnobj-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_BOOLEAN)),
        'user-online' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING)),
        'user-offline' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)),
        'send-message-error' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)),

        'offline-message-waiting' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        'offline-message-received' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),

        # switchboard, msnobj, email
        'display-picture-changed' : (gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)),
        'custom-emoticon-transfered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)),

        # switchboard, msnobj, email, directory
        'wink-transferred' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)),
        # contact object, switchboard (it can be None, check it)
        'hidden-contact' : (gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),

        # login
        'login-error': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, )),
        'login-successful': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),

        # this (detailed) signal is useful to monitor switchboards. params:
        #  switchboard, signal, args (tuple)
        # "signal" may be redundant, but for non-detailed monitoring is useful
        'switchboard' : (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_DETAILED, \
          gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, ) * 3),

        # used for sounds and notifications, bad hack
        'new-file-transfer' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,)),
        'finished-file-transfer' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # used to prevent notifications at login
        'enable-notifications' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    ## constants (ftw!)

    # don't change this unless you know what you are doing
    CVR_STRING = "0x0c0a winnt 5.1 i386 MSNMSGR 8.1.0178 msmsgs %s"

    # p2p features support number
    CLIENT_ID = 0x50000000 | 0x2  # msnc5 + reset capabilities
    CLIENT_ID |= 0x4     # ink
    CLIENT_ID |= 0x20    # multi-packet MIME messages
    CLIENT_ID |= 0x8000  # winks
    CLIENT_ID |= 0x40000 # voice clips
    # TODO: ADD WEBCAM IF USER PREFERENCE TELL TO SHOW AND IMPORT WEBCAMDEVICE DOESN'T GIVE ERRORS

    def __init__(self, host, port, user, password, \
        userConfigDir, proxy = None, canUseP4=False, config=None):
        '''Constructor, intialize variables.'''
        #gobject.GObject.__init__(self)
        ProfileManager.ProfileManager.__init__(self, config)
 
        if proxy == None:
            self.socket = Socket.Socket(host, port)
        else:
            self.socket = Socket.HTTPSocket(host, port, proxy)

        self.user = user.lower()
        self.password = password
        self.MSPAuth = ''
        self.tokens = {}

        self.cacheDir = userConfigDir + os.sep + 'cache'

        self.userConfigDir = userConfigDir

        self.proxy = proxy
        self.callbacks = None
        self.connected = False
        self.nick = ''

        self.status = 'FLN'
        
        self.canNotify = False

        self.switchboards = [] # the switchboards to process
        self.switchboardsByTid = {}
        self.demographics = {}
        self.signals = [] # gobject signals to disconnect on logout
        self.selfSignals = [] # msnp signals

        # try creating a profile only once, if it doesn't exist
        self.triedCreatingProfile = False
        # don't try to update the profile if there's no cache
        self.affinityCache = ''
        # don't loop setting dp
        self.firstSetDpFail = False
        # id of stored dp
        self.dpid = ''

        self.contactManager = ContactData.ContactList({})
        self.msnObjectsManager = Msnobj.MsnObjectsManager(user)
        self.msnOIM = MsnOIM.MsnOIM(self)
        self.p2p = common.DynamicDict(p2p.tlp.P2PUser, True)
        self.p2p.msn = self

        self.currentMedia = ''
        self.personalMessage = ''

        self.msnobj = None # the msnobj for the display picture
        self.picture = None

        self.inboxMessages = 0
        self.inboxUnreadMessages = 0
        self.otherMessages = 0
        self.otherMessagesUnreaded = 0

        self.initialBLPTid = 0
        self.accountConfirmed = False

        self._expecting = ''
        self._allowedRedirects = 5
        self._onLogin = False
        self.canUseP4 = canUseP4
    # login() calls _redirect(), which calls loginInputHandler on socket input,
    # which calls loginProcess

    def login(self):
        '''login to the server, after succesfully login you have to change your
            status to appear online'''
        self._allowedRedirects = 5
        self._onLogin = True
        self._redirect()

    def _redirect(self, host='', port=0):
        '''NS server redirect'''
        if host and port:
            try:
                self.socket.disconnectAll()
                self.socket.close()
            except:
                pass

            if self.proxy is None:
                self.socket = Socket.Socket(host, port)
            else:
                self.socket = Socket.HTTPSocket(host, port, self.proxy)

        self.socket.connect('input', self._loginInputHandler)
        self.socket.connect('hangup', self._loginHangupHandler)

        try:
            self.socket.sendCommand('VER', 'MSNP15 CVR0')
        except:
            self.emit('login-error', 'Connection problem')
            return

        self._expecting = 'VER'

    def _loginHangupHandler(self, socket):
        if self.socket.error:
            self.emit('login-error', 'Connection problem: ' + self.socket.error)
        else:
            self.emit('login-error', 'Connection problem: hangup')
        self.socket.disconnectAll()

    def _loginInputHandler(self, socket):
        retval = False
        if self._onLogin:
            try:
                retval = self._loginProcess(socket)
            except Socket.socket.error, desc:
                self.emit('login-error', 'Connection problem: ' + str(desc))
            except Exception, desc:
                exception = sys.exc_info()
                traceback.print_exception(*exception)
                self.emit('login-error', 'Login error: ' + str(desc))

        if retval == False:
            self.socket.disconnectAll()

    def _loginProcess(self, socket):
        '''Called when a message is received on the login phase'''

        (command, tid, params) = self.socket.receiveCommand()

        # messages that may be received at any time
        # including XFR, GCF, MSG
        if command == 'XFR' and params[ :2 ] == 'NS':
            # XFR 3 NS 207.46.24.39:1863 U D

            try:
                ns = params.split()[1].split(":") # 207.46.24.39:1863
                host = ns[0]                      # 207.46.24.39
                port = int(ns[1])                 # int(1863)
            except:
                self.emit('login-error', 'Incorrect parameters: ' + params)
                return

            if (self._allowedRedirects - 1) <= 0:
                self.emit('login-error', 'Too many redirects')
                return
            self._allowedRedirects -= 1
            self._redirect(host, port)
            return
        elif command == 'MSG':
            data = self.socket.receivePayload(int(params.split()[-1]))
            if self.parse_demographics(data):
                self._retriveLists()
                return
        elif command == 'GCF':
            data = self.socket.receivePayload(int(params))
            # this data contains base64 encoded regexps that are used 
            # by microsoft for censoring unwanted text, say malware links, etc. 
        elif command == 'SBS':
            pass
        elif self._expecting and self._expecting != command:
            # if we can convert the command to int, it's an error
            try:
                self.emit('login-error', 'Server error ' + str(command))
            except ValueError:
                self.emit('login-error', 'Unexpected message (%s)' % command)
            return False
        else:
            if command == 'VER':
                # if he doesnt want to speak version 15 we raise an exception
                if not params.startswith('MSNP15'):
                    self.emit('login-error', 'Protocol not supported by server')
                    return False

                self.socket.sendCommand("CVR", Msnp.CVR_STRING % self.user)
                self._expecting = 'CVR'
            elif command == 'CVR':
                self.socket.sendCommand("USR", "SSO I " + self.user)
                self._expecting = 'USR'
            elif command == 'USR' and params.startswith("SSO S "):
                # we get the hash
                hash = params.split()[-1]

                # start the passport authentication
                self.hash = hash
                self.passportid = self.passportAuth(hash)
                try:
                    self.t = self.passportid.split('&p=')[0][2:]
                    self.MSPProf = self.passportid.split('&p=')[1]
                except:
                    self.emit('login-error', 'Incorrect passportid ' + \
                        self.passportid)
                    return False

                # we introduce ourselves again
                self.socket.sendCommand("USR" , "SSO S " + self.passportid + \
                    " " + self.mbiblob)
                self._expecting = 'USR' # but not this one
            elif command == 'USR' and params.startswith("OK"):
                # yay, we are in
                common.debug('We are in', 'core')
            elif command == 'USR':
                # other USR, maybe fail
                self.emit('login-error', 'Authentication error')
                return False

        return True

    def do_login_error(self, message):
        common.debug("login error ;_;", 'core')
        common.debug(message, 'core')
        try:
            self.socket.hangup()
        except:
            pass
        self._onLogin = False

    def _retriveLists(self):
        '''logged in :D'''

        common.debug("logged in", 'core')
        self.connected = True

        self.soapManager = soap.manager.SoapManager(self)
        self.soapManager.start()

        # disable login process
        self.socket.disconnectAll()

        # get sockets working
        self.socket.connect('input', self.process)
        self.socket.connect('hangup', self.socketHangup)

        # aarrrrghhhh
        self.signals.append(gobject.timeout_add(500, self.soapManager.process))
        self.signals.append(gobject.timeout_add(5000, self.checkPing))

        # Get the lists
        mlCache = None #self.getCacheFileData(self.user + "_ml.xml")
        diCache = None #self.getCacheFileData(self.user + "_di.xml")
        
        if mlCache and diCache:
            common.debug("parsing membership list", 'core')
            start = time.time()
            try:
                self.setMembershipListXml(mlCache)
                common.debug("done:" + str(time.time() - start), 'core')

                common.debug("parsing dynamic items", 'core')
                start = time.time()
                self.setDynamicItemsXml(diCache)
                self.changeNick(ProfileManager.getNickFromDynamicItems(diCache),
                    initial=True)
                common.debug("done:" + str(time.time() - start), 'core')
            except Exception, e: #TODO: pylint
                print "error parsing lists", e

        # connect some callbacks
        self.callbacks = SignalHandler.SignalHandler(self)
        self.selfSignals = []
        self.selfSignals.append(self.connect('status-change', \
            self.callbacks.statusChange))
        self.selfSignals.append(self.connect('switchboard-invitation', \
            self.callbacks.switchboardInvitation))
        self.selfSignals.append(self.connect('server-message', \
            self.callbacks.serverMessage))

        soap.requests.membership(self.proxy, self.onGetMembershipList)
        soap.requests.address_book(self.proxy, self.onGetAddressBook)

    def do_login_successful(self):
        # send privacy status
        self.initialBLPTid = self.socket.sendCommand("BLP" , "BL")
        # if it gets a 209 reply, the account is unconfirmed
        
        # send our contacts
        # TODO: flooding with this killed someones router
        for i in self.contactManager.getADL():
            self.socket.sendPayloadCommand("ADL", '', i)

        # change the nickname
        self.changeNick(self.nick, initial=True)
        gobject.timeout_add(10000, self.enable_notifications)
        soap.requests.get_profile(self.proxy, self.cid, self.onGetProfile)

    # a delay in case the UUX command doesn't enable notifications
    # see "processCommand()" method
    def enable_notifications(self):
        if not self.canNotify:
            self.emit('enable-notifications')
            self.canNotify = True
        return False

    def passportReAuth(self, hash=None):
        if hash == None:
            hash = self.hash
        
        self.passportid = self.passportAuth(hash)
        self.MSPAuth = self.passportid.split('&p')[0][2:]
        self.MSPProf = self.passportid.split('&p')[1]

    def passportAuth(self, nonce, policy="MBI"):
        '''do the passport authenticaton, this is done connecting
        to loginnet.passport.com:443 and sending a XML message described
        on soap.templates.passport'''

        common.debug('PASSPORT begin', 'core')

        # replace the %s in the string
        body = soap.templates.passport % (self.user,
            common.escape(self.password))
        # http://forum.emesene.org/index.php/topic,1946.msg12943.html#msg12943
        #if '@msn.com' not in self.user:
        _server = "login.live.com"
        _url = "/RST.srf"
        #else:
        #    _server = "msnia.login.live.com"
        #    _url = "/pp550/RST.srf"

        #create the headers
        headers = {
            "Accept":  "text/*",
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
            "Host": _server,
            "Content-Length": str(len(body)),
            "Connection": "Keep-Alive",
            "Cache-Control": "no-cache",
            "Accept-encoding": "gzip", # highly improves bandwidth usage
        }

        succeeded = False
        for i in range(5):
            response = None
            lastError = None
            # send the SOAP request
            for i in range(3):
                try:
                    if self.proxy and self.proxy.host:
                        proxy_connect = 'CONNECT %s:%s HTTP/1.0\r\n'%(_server,'443')
                        user_agent = 'User-Agent: python\r\n'
                        if self.proxy.user:
                            # setup basic authentication
                            user_pass = base64.encodestring(self.proxy.user+':'+self.proxy.password).replace('\n','')
                            proxy_authorization = 'Proxy-authorization: Basic '+user_pass+'\r\n'
                            proxy_pieces = proxy_connect+proxy_authorization+user_agent+'\r\n'
                        else:
                            proxy_pieces = proxy_connect+user_agent+'\r\n'
                        # now connect, very simple recv and error checking
                        proxy = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        proxy.connect((self.proxy.host,int(self.proxy.port)))
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
                        conn = httplib.HTTPSConnection(_server,443)
                    conn.request("POST", _url, body, headers)
                    response = conn.getresponse()
                    common.debug('%s %s'%(response.status, response.reason), \
                        'core')
                    break
                except Exception, e:
                    lastError = e

            if response:
                data = response.read()
                isGzipd = response.getheader('Content-Encoding', '')
                if isGzipd == 'gzip':
                    # data is gzipped, unzipit!
                    cstream = StringIO.StringIO(data)
                    gzpr = gzip.GzipFile(fileobj=cstream)
                    data = gzpr.read()
            else:
                raise common.AuthError, "Can't connect to HTTPS server: " + \
                    str(e)

            if data.find('<faultcode>psf:Redirect</faultcode>') > 0:
                _url = urlparse.urlparse(data.split('<psf:redirectUrl>')\
                    [ 1 ].split('</psf:redirectUrl>')[ 0 ])

                # fixed according to
                #  http://docs.python.org/lib/module-urlparse.html
                _server=_url[ 1 ]
                _url=_url[ 2 ]
                common.debug('Redirect to: %s %s' % (_server, _url), 'core')
            else:
                succeeded = True
                break

        if not succeeded:
            raise common.AuthError, 'Too many redirections'

        # try to get the ticket from the received data
        try:
            self.tokens = SSoParser(data).tokens
            if 'messengerclear.live.com' not in self.tokens:
                raise common.AuthError, 'Auth Failed'
        except Exception, e:
            common.debug(e, 'core')
            common.debug(data, 'core')
            # try to get the faultstring
            try:
                faultstring = data.split("<faultstring>")\
                    [ 1 ].split("</faultstring>")[ 0 ]
            except:
                faultstring = ''
            raise common.AuthError, faultstring
        self.mbiblob = mbi.encrypt(
                self.tokens['messengerclear.live.com']['secret'], nonce)
        return self.tokens['messengerclear.live.com']['security']\
                .replace("&amp;" , "&")

    def ping(self):
        '''send a ping to the server and register the timestamp of the command'''
        try:
            self.socket.ping()
        except (IOError, socket.error):
            self.emit('connection-closed')

    def checkConnection(self):
        '''return true if the time between the last ping and the response is
        lower than max_ping_delay'''

        if self.socket.ping_enabled and \
           (self.socket.lastqng < self.socket.lastpng) and \
           (time.time() - self.socket.lastpng) > self.socket.max_ping_delay:
            return False

        return True

    def checkPing(self):
        '''check connection and ping if needed
        A return value False doesn't mean broken connection,
        it means "disconnect this timeout"'''

        if not self.connected:
            return False
        elif not self.socket.ping_enabled:
            return False
        elif self.socket.lastpng == 0:
            self.ping()
        elif not self.checkConnection():
            self.emit('connection-problem')
            print 'connection problem'
            return False
        elif (int(time.time()) - self.socket.lastpng) > \
             self.socket.secs_between_pings:
            self.ping()

        return True

    def socketHangup(self, socket):
        '''The socket got into IO_HUP or IO_ERR status'''
        common.debug("Socket hangup/error", 'core')
        self.emit('connection-closed')
        return False

    def process(self, obj=None):
        '''read a command from the server and process it'''

        (command, tid, params) = self.socket.receiveCommand()
        try:
            self.processCommand(command, tid, params)
        except:
            print 'FATAL ERROR on msn.process(): '
            self.emit('exception', sys.exc_info())
            return False
        return True

    def processCommand(self, command, tid, params):
        if command == 'CHL':
            self.callbacks.challenge(self, command, tid, params)
            self.socket.do_not_ping = False
            #self.emit('challenge', command, tid, params)
        elif command == 'ILN':
            self.callbacks.statusChange(self, command, tid, params)
            gobject.idle_add(self.emit, 'initial-status-change', command, tid, params)
        elif command == 'NLN':
            # kids, we emit the status-online signal in SignalHandler            
            self.callbacks.statusOnline(self, command, tid, params)
        elif command == 'FLN':
            self.callbacks.statusOffline(self, command, tid, params)
            self.emit('status-offline', command, tid, params)
        elif command == 'RNG':
            self.emit('switchboard-invitation', command, tid, params)
        elif command == 'ADL':
            if params != 'OK':
                payload = self.socket.receivePayload(int(params))
                # this looks like when someone adds you
                # <ml><d n="gmail.com"><c n="luismarianoguerra" t="1" l="8" \
                # f="[Mariano%20Guerra]%20(IRC%20is%20just%20multiplayer%20 \
                # notepad.)" /></d></ml>

                email = payload.split('<c n="')[1].split('"')[0] + '@' + \
                    payload.split('<ml><d n="')[1].split('"')[0]
                nick = ''

                type = payload.split(' t="')[1].split('"')[0]
                if int(type) == 32:
                    print payload
                    return

                try:
                    nick = payload.split(' f="')[1].split('"')[0]
                    nick = urllib.unquote(nick)
                except:
                    pass

                lists = self.contactManager.lists
                if email not in lists['Block'] and email not in lists['Allow']:
                    self.emit('add-notification', command, tid, params, \
                        email, nick)

        elif command == 'RML':
            if params != 'OK':
                payload = self.socket.receivePayload(int(params))
                # this looks like when someone removes you:
                # <ml><d n="gmail.com"><c n="luismarianoguerra" t="1" \
                # l="8" /></d></ml>

                email = payload.split('<c n="')[1].split('"')[0] + '@' + \
                    payload.split('<ml><d n="')[1].split('"')[0]
                self.emit('remove-notification', command, tid, params, email)

        elif command == 'UBX':
            size = int(params.split()[-1])
            payload = self.socket.receivePayload(size)
            payload = payload.decode('utf-8', 'replace').encode('utf-8')

            common.debug('<<< ' + payload, 'core')
            if size > 0:
                try:
                    self.parseUBX(command, tid, params, payload)
                except Exception, e:
                    common.debug('Unable to handle UBX: ' + str(e))

        elif command == 'XFR':
            #XFR 32 SB 65.54.171.31:1863 CKI 1743299383.52212212.219110167 U messenger.msn.com\r\n
            connstring = ' '.join([command, tid, params])
            self.switchboardsByTid[int(tid)].setConnectionString(connstring)
        elif command == 'MSG':
            try:
                payload = self.socket.receivePayload(int(params.split()[1]))
                self.emit('server-message', command, tid, params, payload)
            except Exception, e:
                common.debug('Exception in msnp.process, continuing', 'core')
                common.debug('(EE) ' + str(e), 'core')
        elif command == 'NOT':
            # TODO: parse these messages
            payload = self.socket.receivePayload(int(tid))
        elif command == 'OUT':
            self.emit('user-disconnected', tid, params)
        elif command == 'QNG':
            self.socket.onQng(tid)
        elif command == '209' and self.initialBLPTid == tid:
            # i think flags 1024 or 1 on the initial hotmail MSG
            # have something to do with this, but this seems safer
            self.accountConfirmed = False
            self.emit('account-unconfirmed')
        elif command == "UUX" and params == "0" and self.profile_retrieved:
            self.enable_notifications()

    def parseUBX(self, command, tid, params, payload):
        '''this function parses the UBX payload, and sets the personal
        message or current media'''
        parsed = UbxParser(payload)

        if parsed.current_media:
            media = '\xe2\x99\xab ' + parsed.current_media
            self.contactManager.setContactPersonalMessage(tid, media)
        else:
            self.contactManager.setContactPersonalMessage(tid, parsed.psm)

        #TODO: is this signal needed?
        self.emit('personal-message-changed', tid, parsed.psm)

        contact = self.contactManager.getContact(tid)
        self.emit('user-attr-changed', contact)

    def changeStatus(self , status):
        '''change the current status'''

        if status == 'FLN' or status == 'offline':
            return

        msnobj = ''

        if self.msnobj:
            msnobj = ' ' + self.msnobj.quote()
        else:
            msnobj = ' 0'
        #print msnobj
        clientid = ' ' + str(self.CLIENT_ID)

        if common.status_table.has_key(status):
            self.socket.sendCommand("CHG" , common.status_table[ status ] + clientid + msnobj)
            self.status = common.status_table[ status ]
            self.emit('self-status-changed', self.status)
        elif common.reverse_status.has_key(status):
            self.socket.sendCommand("CHG" , status + clientid + msnobj)
            self.status = status
            self.emit('self-status-changed', self.status)

    def sendDL(self, command, email, type):
        '''send ADL or RML on a single contact'''
        self.sendDLs(command, {email: type})

    def sendDLs(self, command, usersdict):
        '''send ADL or RML
        userslist is a dict {email: type}

        allowed values for type:
        #1 = Forward List
        #2 = Allow List
        #4 = Block List
        #8 = Reverse List (not to be tampered with)
        #16 = Pending list

        FL Forward List Users who were added to your contact list
        RL Reverse List Users who added you to their contact list
        AL Allow List Users who are able to see your status
        BL Block List Users who are blocked from seeing your status'''

        payloads = self.contactManager.buildDL(usersdict, initial=False)

        # TODO: flooding with this killed someones router
        for payload in payloads:
            self.socket.sendPayloadCommand(command, '', payload)

    def logout(self):
        '''disconnect from the server'''
        self.emit('logout')
        self.socket.disconnectAll()
        try:
            self.socket.send('OUT\r\n')
        except:
            pass
        self.socket.hangup()

        if not self.connected:
            return
        self.connected = False


        # cleanup references
        for signal in self.signals:
            gobject.source_remove(signal)
        self.signals = []

        for signal in self.selfSignals:
            self.disconnect(signal)
        self.selfSignals = []

        self.contactManager = ContactData.ContactList({})
        self.msnOIM.destroy()
        self.msnOIM = None
        self.callbacks = None

        # Send the soapmanager a stop signal
        try:
            self.soapManager.destroy()
            self.soapManager.join() # thread
            self.soapManager = None
        except:
            pass

        # cleanup switchboards
        for sb in self.switchboards:
            try:
                sb.leaveChat()
                sb.msn = None
            except:
                pass
        self.switchboards = []
        self.switchboardsByTid = {}

    def newSwitchboard(self):
        '''create a new Switchboard and return it'''
        tid = self.socket.tid
        new = Switchboard.Switchboard(tid, self, 'requested')
        self.on_new_switchboard(new)
        self.switchboardsByTid[tid] = new
        self.socket.sendCommand('XFR', 'SB')

        return new

    def removeClosedSwitchboards(self):
        closed = []
        for sb in self.switchboards:
            if sb.status in ('closed', 'error'):
                closed.append(sb)
        for sb in closed:
            self.switchboards.remove(sb)
        del closed

    def on_display_picture_received(self, switchboard, msnobj, data, email):
        '''called when a display picture has been received'''
        contact = self.contactManager.getContact(email)
        filename = contact.displayPicturePath
        try:
            open(os.path.join(self.cacheDir, filename), 'wb').write(data)
        except IOError:
            print "can't save display picture"
        else:
            self.emit('display-picture-changed', switchboard, msnobj, email)

    def on_custom_emoticon_received(self, switchboard, msnobj, data, email):
        '''called when a custom emoticon has been received'''
        open(msnobj.filename,'wb').write(data)
        self.emit('custom-emoticon-transfered', email, msnobj, msnobj.filename)

    def on_wink_received(self, switchboard, msnobj, data, email):
        '''called when a wink has been received'''
        try:
            # save wink to cache/wink_sha1d/wink.cab
            sha1d = hashlib.sha1(msnobj.sha1d).hexdigest()
            dir = os.path.join(self.cacheDir, 'wink_' + sha1d)
            if not os.path.exists(dir):
                os.mkdir(dir)

            path = os.path.join(dir, 'wink.cab')
            open(path, 'wb').write(data)
        except IOError:
            print "can't save wink"
        else:
            self.emit('wink-transferred', email, msnobj, dir)

    def on_new_switchboard(self, switchboard):
        '''called when a new switchboad is created, its not a callback
        from a signal'''
        self.switchboards.append(switchboard)
        self.emit('new-switchboard', switchboard)

    def getSwitchboard(self, email):
        '''try to retrieve an existing switchboard that has email as the first
        user and its not a group chat. Clean up closed switchboards and create
        a new switchboard if no existing switchboard matches.'''

        self.removeClosedSwitchboards()
        switchboard = None
        for sb in self.switchboards:
            if not sb.isGroupChat() and sb.firstUser == email:
                switchboard = sb

        if not switchboard:
            switchboard = self.newSwitchboard()
            switchboard.invite(email)
        return switchboard

    def getGroups(self):
        '''return the groups in the userlist'''

        return self.contactManager.groups

    def getGroupNames(self):
        '''Returns a list with the group names in the user list'''
        groups = self.contactManager.getGroupNames()
        groups.sort( key= lambda x: x.lower() )

        return groups

    def checkPending(self):
        '''Return all the pending users'''

        l = []
        lists = self.contactManager.lists
        for email in lists[ 'Pending' ]:
            if email not in lists[ 'Block' ] and email not in lists[ 'Allow' ]:
                l.append(email)

        return l

    def cacheFileExist(self, fileName):
        '''return true if the file exist in the cache directory'''

        return os.path.isfile(self.cacheDir + os.sep + fileName)

    def newCacheFile(self, fileName, data):
        '''create the file and put data on it'''

        f = open(self.cacheDir + os.sep + fileName, 'w')
        f.write(data)
        f.close()

    def getCacheFileData(self, fileName):
        '''get the data in filename, return None otherwise'''

        if self.cacheFileExist(fileName):
            f = open(self.cacheDir + os.sep + fileName, 'r')
            data = f.read()
            f.close()
            return data
        else:
            return None

    def setDisplayPicture(self, filename):
        '''try to open the picture and set the msnobj'''
        if filename == '':
            self.msnobj = None
        else:
            self.msnobj = self.msnObjectsManager.create('', filename, \
                type=Msnobj.Msnobj.DISPLAY_PICTURE)

            myself = self.contactManager.getContact(self.user)
            if myself != None:
                myself.displayPicturePath = filename

            self.updateDisplayPicture()

        if self.status != 'FLN':
            self.changeStatus(self.status)

    def createCustomEmoticon(self, shortcut, filename):
        self.msnObjectsManager.create(shortcut, filename, type=Msnobj.Msnobj.CUSTOM_EMOTICON)

    def getMsnObjectsManager(self):
        return self.msnObjectsManager

    def getUser(self):
        return self.user

    def getNick(self):
        return self.nick

    def setDebug(self, debug, binary):
        common.debugFlag = debug
        common.binaryFlag = binary

    def parse_demographics(self, payload):
        '''parse the demographic data and add it ot the demographics dict'''
        # true means "login successful"
        mspauth = False
        for line in payload.split("\r\n"):
            try:
                key, value = line.split(":")
                self.demographics.update({key.strip(): value.strip()})
            except:
                pass
            if line.startswith("MSPAuth: "):
                self.MSPAuth = line.split("MSPAuth: ")[ 1 ]
                mspauth = True
        return mspauth

gobject.type_register(Msnp)

