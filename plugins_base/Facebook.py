#Changelog :
#   -- 0.7.16 | 03/11/2009 : Better login experience
#   -- 0.7.15 | 09/05/2009 : Added suffix option | Updated strings
#   -- 0.7.12 | 09/02/2009 : Various configuration bugfixes | Updated some strings
#   -- 0.7.10 | 09/02/2009 : Some translations updates | The two status option have merged into a "synchronization" option. Seeparing them is kind of unusual now. | Comments are downloaded in a new thread if there is a new comment | Fixed a bug with commentscount displaying | Various comments bugfixes
#   -- 0.7.5 | 09/01/2009 : Plugin ready for translations | Updated some strings
#   -- 0.7 | 09/01/2009 : Now when the status is cleared from facebook, the commentsbox disappears. Bugfix w/ commentsactive. Now comments are grabbed in a new thread if commentscount changes. Configuration box rewritten. Optimized threads. Some cleaning.
#   -- 0.6.11 | 08/30/2009 : Solved a bug w/ commentscount and comments displaying ? | Added a silhouette logo if the user doesn't have a profilepic
#   -- 0.6.9 | 08/28/2009 : Removed pango from the importations | Changed a sentence in confirmation box
#   -- 0.6.7 | 08/28/2009 : Comments button is destroyed when changing or clearing status | Now 'confirmation' is saved | Disable comments if 1st option disabled. Silent now.
#   -- 0.6.4 | 08/28/2009 : Bugfixes
#   -- 0.6.2 | 08/27/2009 : Trying to solve a bug that makes the user authenticate every time | Trying to handle silently facebook errors and urllib errors
#   -- 0.6 | 08/27/2009 : This version implements threads. No need to import gobject now
#   -- 0.5.14 | 08/24/2009 : Fixed a nasty bug on startup.
#   -- 0.5.13 | 08/08/2009 : Created a facebook directory where is put facebook stuff | bugfix, faster | Now comments activated by default
#   -- 0.5.12 | 08/08/2009 : This should reduce gui locks a lot
#   -- 0.5.11 | 08/08/2009 : As fast as before, but no need to have read_stream
#   -- 0.5.10 | 08/08/2009 : Comments request improved. It downloads pictures once.
#   -- 0.5.9 | 08/07/2009 : Added read_stream. It prevents gui_locks but you'll have to delete Facebook.conf
#   -- 0.5.8 | 08/07/2009 : Comments are saved and retrieved if commentscount didn't change (still WIP though) | it stops checking after the plugin to stop
#   -- 0.5.6 | 08/07/2009 : Bugfix
#   -- 0.5.5 | 08/07/2009 : Nicolaide's comments box integrated, w/ picture retrieving | New pyfacebook version | Some workarounds
#   -- 0.5.2 | 08/05/2009 : Initial logged release
#
#       mehd36 at gmail . com
#
#       This plugin is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This plugin is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import Plugin
import paths
import gtk
import os
import gc
import base64
import desktop
from threading import Event, Thread

#
# pyfacebook - Python bindings for the Facebook API
#

import sys
import time
import struct
import urllib
import urllib2
import httplib
try:
    import hashlib
except ImportError:
    import md5 as hashlib
import binascii
import urlparse
import mimetypes

# try to use simplejson first, otherwise fallback to XML
RESPONSE_FORMAT = 'JSON'
try:
    import json as simplejson
except ImportError:
    try:
        import simplejson
    except ImportError:
        try:
            from django.utils import simplejson
        except ImportError:
            try:
                import jsonlib as simplejson
                simplejson.loads
            except (ImportError, AttributeError):
                from xml.dom import minidom
                RESPONSE_FORMAT = 'XML'

# support Google App Engine.  GAE does not have a working urllib.urlopen.
try:
    from google.appengine.api import urlfetch

    def urlread(url, data=None, headers=None):
        if data is not None:
            if headers is None:
                headers = {"Content-type": "application/x-www-form-urlencoded"}
            method = urlfetch.POST
        else:
            if headers is None:
                headers = {}
            method = urlfetch.GET

        result = urlfetch.fetch(url, method=method,
                                payload=data, headers=headers)

        if result.status_code == 200:
            return result.content
        else:
            raise urllib2.URLError("fetch error url=%s, code=%d" % (url, result.status_code))

except ImportError:
    def urlread(url, data=None):
        try:
            res = urllib2.urlopen(url, data=data)
            return res.read()
        except:
            res = urllib2.urlopen(url, data=data)
            return res.read()

__all__ = ['Facebook']

VERSION = '0.1'

FACEBOOK_URL = 'http://api.facebook.com/restserver.php'
FACEBOOK_SECURE_URL = 'https://api.facebook.com/restserver.php'

class json(object): pass

# simple IDL for the Facebook API
METHODS = {
    'notifications': {
        'get': []
    },

    # users methods
    'users': {
        'getInfo': [
            ('uids', list, []),
            ('fields', list, [('default', ['name'])]),
        ],

        'getStandardInfo': [
            ('uids', list, []),
            ('fields', list, [('default', ['uid'])]),
        ],

        'getLoggedInUser': [],

        'isAppAdded': [],

        'hasAppPermission': [
            ('ext_perm', str, []),
            ('uid', int, ['optional']),
        ],

        'setStatus': [
            ('status', str, []),
            ('clear', bool, []),
            ('status_includes_verb', bool, ['optional']),
            ('uid', int, ['optional']),
        ]
    },

    # auth methods
    'auth': {
        'revokeAuthorization': [
            ('uid', int, ['optional']),
        ],
    },
    'fql': {
        'query': [
            ('query', str, []),
        ],
    },

    #stream methods (beta)
    'stream' : {
        'getComments' : [
            ('post_id', int, []),
        ]
    }
}

class Proxy(object):
    """Represents a "namespace" of Facebook API calls."""

    def __init__(self, client, name):
        self._client = client
        self._name = name

    def __call__(self, method=None, args=None, add_session_args=True):
        # for Django templates
        if method is None:
            return self

        if add_session_args:
            self._client._add_session_args(args)

        return self._client('%s.%s' % (self._name, method), args)


# generate the Facebook proxies
def __generate_proxies():
    for namespace in METHODS:
        methods = {}

        for method in METHODS[namespace]:
            params = ['self']
            body = ['args = {}']

            for param_name, param_type, param_options in METHODS[namespace][method]:
                param = param_name

                for option in param_options:
                    if isinstance(option, tuple) and option[0] == 'default':
                        if param_type == list:
                            param = '%s=None' % param_name
                            body.append('if %s is None: %s = %s' % (param_name, param_name, repr(option[1])))
                        else:
                            param = '%s=%s' % (param_name, repr(option[1]))

                if param_type == json:
                    # we only jsonify the argument if it's a list or a dict, for compatibility
                    body.append('if isinstance(%s, list) or isinstance(%s, dict): %s = simplejson.dumps(%s)' % ((param_name,) * 4))

                if 'optional' in param_options:
                    param = '%s=None' % param_name
                    body.append('if %s is not None: args[\'%s\'] = %s' % (param_name, param_name, param_name))
                else:
                    body.append('args[\'%s\'] = %s' % (param_name, param_name))

                params.append(param)

            # simple docstring to refer them to Facebook API docs
            body.insert(0, '"""Facebook API call. See http://developers.facebook.com/documentation.php?v=1.0&method=%s.%s"""' % (namespace, method))

            body.insert(0, 'def %s(%s):' % (method, ', '.join(params)))

            body.append('return self(\'%s\', args)' % method)

            exec('\n    '.join(body))

            methods[method] = eval(method)

        proxy = type('%sProxy' % namespace.title(), (Proxy, ), methods)

        globals()[proxy.__name__] = proxy


__generate_proxies()


class FacebookError(Exception):
    """Exception class for errors received from Facebook."""

    def __init__(self, code, msg, args=None):
        self.code = code
        self.msg = msg
        self.args = args

    def __str__(self):
        return 'Error %s: %s' % (self.code, self.msg)

class AuthProxy(AuthProxy):
    """Special proxy for facebook.auth."""

    def getSession(self):
        """Facebook API call. See http://developers.facebook.com/documentation.php?v=1.0&method=auth.getSession"""
        args = {}
        try:
            args['auth_token'] = self._client.auth_token
        except AttributeError:
            raise RuntimeError('Client does not have auth_token set.')
        result = self._client('%s.getSession' % self._name, args)
        self._client.session_key = result['session_key']
        self._client.uid = result['uid']
        self._client.secret = result.get('secret')
        self._client.session_key_expires = result['expires']
        return result

    def createToken(self):
        """Facebook API call. See http://developers.facebook.com/documentation.php?v=1.0&method=auth.createToken"""
        token = self._client('%s.createToken' % self._name)
        self._client.auth_token = token
        return token

class Facebook(object):

    def __init__(self, api_key, secret_key, auth_token=None, app_name=None, callback_path=None, internal=None, proxy=None, facebook_url=None, facebook_secure_url=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session_key = None
        self.session_key_expires = None
        self.auth_token = auth_token
        self.secret = None
        self.uid = None
        self.page_id = None
        self.in_canvas = False
        self.in_profile_tab = False
        self.added = False
        self.app_name = app_name
        self.callback_path = callback_path
        self.internal = internal
        self._friends = None
        self.locale = 'en_US'
        self.profile_update_time = None
        self.ext_perms = None
        self.proxy = proxy
        if facebook_url is None:
            self.facebook_url = FACEBOOK_URL
        else:
            self.facebook_url = facebook_url
        if facebook_secure_url is None:
            self.facebook_secure_url = FACEBOOK_SECURE_URL
        else:
            self.facebook_secure_url = facebook_secure_url

        for namespace in METHODS:
            self.__dict__[namespace] = eval('%sProxy(self, \'%s\')' % (namespace.title(), 'facebook.%s' % namespace))


    def _hash_args(self, args, secret=None):
        """Hashes arguments by joining key=value pairs, appending a secret, and then taking the MD5 hex digest."""
        # @author: houyr
        # fix for UnicodeEncodeError
        hasher = hashlib.md5(''.join(['%s=%s' % (isinstance(x, unicode) and x.encode("utf-8") or x, isinstance(args[x], unicode) and args[x].encode("utf-8") or args[x]) for x in sorted(args.keys())]))
        if secret:
            hasher.update(secret)
        elif self.secret:
            hasher.update(self.secret)
        else:
            hasher.update(self.secret_key)
        return hasher.hexdigest()


    def _parse_response_item(self, node):
        """Parses an XML response node from Facebook."""
        if node.nodeType == node.DOCUMENT_NODE and \
            node.childNodes[0].hasAttributes() and \
            node.childNodes[0].hasAttribute('list') and \
            node.childNodes[0].getAttribute('list') == "true":
            return {node.childNodes[0].nodeName: self._parse_response_list(node.childNodes[0])}
        elif node.nodeType == node.ELEMENT_NODE and \
            node.hasAttributes() and \
            node.hasAttribute('list') and \
            node.getAttribute('list')=="true":
            return self._parse_response_list(node)
        elif len(filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes)) > 0:
            return self._parse_response_dict(node)
        else:
            return ''.join(node.data for node in node.childNodes if node.nodeType == node.TEXT_NODE)


    def _parse_response_dict(self, node):
        """Parses an XML dictionary response node from Facebook."""
        result = {}
        for item in filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes):
            result[item.nodeName] = self._parse_response_item(item)
        if node.nodeType == node.ELEMENT_NODE and node.hasAttributes():
            if node.hasAttribute('id'):
                result['id'] = node.getAttribute('id')
        return result


    def _parse_response_list(self, node):
        """Parses an XML list response node from Facebook."""
        result = []
        for item in filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes):
            result.append(self._parse_response_item(item))
        return result


    def _check_error(self, response):
        """Checks if the given Facebook response is an error, and then raises the appropriate exception."""
        if type(response) is dict and response.has_key('error_code'):
            raise FacebookError(response['error_code'], response['error_msg'], response['request_args'])


    def _build_post_args(self, method, args=None):
        """Adds to args parameters that are necessary for every call to the API."""
        if args is None:
            args = {}

        for arg in args.items():
            if type(arg[1]) == list:
                args[arg[0]] = ','.join(str(a) for a in arg[1])
            elif type(arg[1]) == unicode:
                args[arg[0]] = arg[1].encode("UTF-8")
            elif type(arg[1]) == bool:
                args[arg[0]] = str(arg[1]).lower()

        args['method'] = method
        args['api_key'] = self.api_key
        args['v'] = '1.0'
        args['format'] = RESPONSE_FORMAT
        args['sig'] = self._hash_args(args)

        return args


    def _add_session_args(self, args=None):
        """Adds 'session_key' and 'call_id' to args, which are used for API calls that need sessions."""
        if args is None:
            args = {}

        if not self.session_key:
            return args
            #some calls don't need a session anymore. this might be better done in the markup
            #raise RuntimeError('Session key not set. Make sure auth.getSession has been called.')

        args['session_key'] = self.session_key
        args['call_id'] = str(int(time.time() * 1000))

        return args


    def _parse_response(self, response, method, format=None):
        """Parses the response according to the given (optional) format, which should be either 'JSON' or 'XML'."""
        if not format:
            format = RESPONSE_FORMAT

        if format == 'JSON':
            result = simplejson.loads(response)
            if type(result) is dict and result.has_key('error_code'):
                result = simplejson.loads(response)
            self._check_error(result)
        elif format == 'XML':
            dom = minidom.parseString(response)
            result = self._parse_response_item(dom)
            dom.unlink()

            if 'error_response' in result:
                dom = minidom.parseString(response)
                result = self._parse_response_item(dom)
                dom.unlink()
                
            if 'error_response' in result:    
                self._check_error(result['error_response'])

            result = result[method[9:].replace('.', '_') + '_response']
        else:
            raise RuntimeError('Invalid format specified.')

        return result


    def hash_email(self, email):
        """
        Hash an email address in a format suitable for Facebook Connect.

        """
        email = email.lower().strip()
        return "%s_%s" % (
            struct.unpack("I", struct.pack("i", binascii.crc32(email)))[0],
            hashlib.md5(email).hexdigest(),
        )


    def unicode_urlencode(self, params):
        """
        @author: houyr
        A unicode aware version of urllib.urlencode.
        """
        if isinstance(params, dict):
            params = params.items()
        return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-8') or v)
                          for k, v in params])


    def __call__(self, method=None, args=None, secure=False):
        """Make a call to Facebook's REST server."""
        # for Django templates, if this object is called without any arguments
        # return the object itself
        if method is None:
            return self

        # @author: houyr
        # fix for bug of UnicodeEncodeError
        post_data = self.unicode_urlencode(self._build_post_args(method, args))

        if self.proxy:
            proxy_handler = urllib2.ProxyHandler(self.proxy)
            opener = urllib2.build_opener(proxy_handler)
            if secure:
                response = opener.open(self.facebook_secure_url, post_data).read()
            else:
                response = opener.open(self.facebook_url, post_data).read()
        else:
            if secure:
                response = urlread(self.facebook_secure_url, post_data)
            else:
                response = urlread(self.facebook_url, post_data)

        return self._parse_response(response, method)


    # URL helpers
    def get_url(self, page, **args):
        """
        Returns one of the Facebook URLs (www.facebook.com/SOMEPAGE.php).
        Named arguments are passed as GET query string parameters.

        """
        return 'http://www.facebook.com/%s.php?%s' % (page, urllib.urlencode(args))


    def get_app_url(self, path=''):
        """
        Returns the URL for this app's canvas page, according to app_name.

        """
        return 'http://apps.facebook.com/%s/%s' % (self.app_name, path)


    def get_add_url(self, next=None):
        """
        Returns the URL that the user should be redirected to in order to add the application.

        """
        args = {'api_key': self.api_key, 'v': '1.0'}

        if next is not None:
            args['next'] = next

        return self.get_url('install', **args)


    def get_authorize_url(self, next=None, next_cancel=None):
        args = {'api_key': self.api_key, 'v': '1.0'}

        if next is not None:
            args['next'] = next

        if next_cancel is not None:
            args['next_cancel'] = next_cancel

        return self.get_url('authorize', **args)


    def get_login_url(self, next=None, popup=False, canvas=True):
        args = {'api_key': self.api_key, 'v': '1.0'}

        if next is not None:
            args['next'] = next

        if canvas is True:
            args['canvas'] = 1

        if popup is True:
            args['popup'] = 1

        if self.auth_token is not None:
            args['auth_token'] = self.auth_token

        return self.get_url('login', **args)


    def login(self, popup=False):
        desktop.open(self.get_login_url(popup=popup))


    def get_ext_perm_url(self, ext_perm, next=None, popup=False):
        args = {'ext_perm': ext_perm, 'api_key': self.api_key, 'v': '1.0'}

        if next is not None:
            args['next'] = next

        if popup is True:
            args['popup'] = 1

        return self.get_url('authorize', **args)


    def request_extended_permission(self, ext_perm, popup=False):
        """Open a web browser telling the user to grant an extended permission."""
        desktop.open(self.get_ext_perm_url(ext_perm, popup=popup))


    def check_session(self, request):
        self.in_canvas = (request.POST.get('fb_sig_in_canvas') == '1')

        if self.session_key and (self.uid or self.page_id):
            return True

        if request.method == 'POST':
            params = self.validate_signature(request.POST)
        else:
            if 'installed' in request.GET:
                self.added = True

            if 'fb_page_id' in request.GET:
                self.page_id = request.GET['fb_page_id']

            if 'auth_token' in request.GET:
                self.auth_token = request.GET['auth_token']

                try:
                    self.auth.getSession()
                except FacebookError, e:
                    self.auth_token = None
                    return False

                return True

            params = self.validate_signature(request.GET)

        if not params:
            # first check if we are in django - to check cookies
            if hasattr(request, 'COOKIES'):
                params = self.validate_cookie_signature(request.COOKIES)
            else:
                # if not, then we might be on GoogleAppEngine, check their request object cookies
                if hasattr(request,'cookies'):
                    params = self.validate_cookie_signature(request.cookies)

        if not params:
            return False

        if params.get('in_canvas') == '1':
            self.in_canvas = True

        if params.get('in_profile_tab') == '1':
            self.in_profile_tab = True

        if params.get('added') == '1':
            self.added = True

        if params.get('expires'):
            self.session_key_expires = int(params['expires'])

        if 'locale' in params:
            self.locale = params['locale']

        if 'profile_update_time' in params:
            try:
                self.profile_update_time = int(params['profile_update_time'])
            except ValueError:
                pass

        if 'ext_perms' in params:
            self.ext_perms = params['ext_perms']

        if 'friends' in params:
            if params['friends']:
                self._friends = params['friends'].split(',')
            else:
                self._friends = []

        if 'session_key' in params:
            self.session_key = params['session_key']
            if 'user' in params:
                self.uid = params['user']
            elif 'page_id' in params:
                self.page_id = params['page_id']
            else:
                return False
        elif 'profile_session_key' in params:
            self.session_key = params['profile_session_key']
            if 'profile_user' in params:
                self.uid = params['profile_user']
            else:
                return False
        elif 'canvas_user' in params:
            self.uid = params['canvas_user']
        else:
            return False

        return True


    def validate_signature(self, post, prefix='fb_sig', timeout=None):
        """
        Validate parameters passed to an internal Facebook app from Facebook.

        """
        args = post.copy()

        if prefix not in args:
            return None

        del args[prefix]

        if timeout and '%s_time' % prefix in post and time.time() - float(post['%s_time' % prefix]) > timeout:
            return None

        args = dict([(key[len(prefix + '_'):], value) for key, value in args.items() if key.startswith(prefix)])

        hash = self._hash_args(args)

        if hash == post[prefix]:
            return args
        else:
            return None

    def validate_cookie_signature(self, cookies):
        """
        Validate parameters passed by cookies, namely facebookconnect or js api.
        """
        if not self.api_key in cookies.keys():
            return None

        sigkeys = []
        params = dict()
        for k in sorted(cookies.keys()):
            if k.startswith(self.api_key+"_"):
                sigkeys.append(k)
                params[k.replace(self.api_key+"_","")] = cookies[k]


        vals = ''.join(['%s=%s' % (x.replace(self.api_key+"_",""), cookies[x]) for x in sigkeys])
        hasher = hashlib.md5(vals)

        hasher.update(self.secret_key)
        digest = hasher.hexdigest()
        if digest == cookies[self.api_key]:
            return params
        else:
            return False

class MainClass( Plugin.Plugin ):
    '''Main plugin class
    This plugins synchronizes Emesene with your Facebook life'''
    description = _('Synchronize emesene with your Facebook status, profile picture and more!')
    authors = { 'Mehdi Rejraji' : 'mehd36 at gmail dot com' }
    website = ''
    displayName = 'Facebook'
    name = 'Facebook'

    def __init__( self, controller, msn):
        '''Contructor'''

        Plugin.Plugin.__init__( self, controller, msn)

        self.description = _('Synchronize emesene with your Facebook status, profile picture and more!')
        self.authors = { 'Mehdi Rejraji' : 'mehd36 at gmail dot com' }
        self.website = ''
        self.displayName = 'Facebook'
        self.name = 'Facebook'

        self.controller = controller
        self.config = controller.config
        self.config.readPluginConfig(self.name)

        self.dest_filename = os.path.join(paths.CONFIG_DIR, \
            controller.config.getCurrentUser(), '')
            
        facebookdir = os.path.join(self.dest_filename, \
            'facebook', '') 

        if os.path.exists(facebookdir):
            self.dest_filename = facebookdir
        else:
            os.mkdir(facebookdir)
            if os.path.exists(facebookdir):
                self.dest_filename = facebookdir

        self.status = self.config.getPluginValue \
            (self.name, 'status', '1')
        self.time = (self.config.getPluginValue \
            (self.name, 'time', '0') == '1')
        self.avatar = (self.config.getPluginValue \
            (self.name, 'avatar', '1') == '1')
        self.buttonconv = (self.config.getPluginValue \
            (self.name, 'buttonconv', '0') == '1')
        self.buttonhome = (self.config.getPluginValue \
            (self.name, 'buttonhome', '1') == '1')
        self.unread = (self.config.getPluginValue \
            (self.name, 'unread', '1') == '1')
        self.pokes = (self.config.getPluginValue \
            (self.name, 'pokes', '0') == '1')
        self.comments = (self.config.getPluginValue \
            (self.name, 'comments', '1') == '1')
        self.timechanged = False
        api_key = '92d4a977a81ac68bb53fdb4dac115fd9'
        secret_key = 'd51f6f904f0082684c899d4d511fe99b'
        self.fb = Facebook(api_key, secret_key)
        self.theme = controller.theme
        self.doichangestatus = True
        
        
        
        self.enabled = False

    def start(self):
        if self.enabled == False:
            self.check()
        ## Add a button to the conversation windows if enabled
        ###Creates a new button with an encoded facebook icon
        items = [('facebook-logo', '_Facebook', 0, 0, '')]
        gtk.stock_add(items)
        factory = gtk.IconFactory()
        factory.add_default()
        fbimageencoded = \
        """AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAcRoNUP2qk+Uhy\nqv9MdKv/Tnas/1F3rf9Sea3/VHqu/1V7rv9V
        e67/VXqu/1N6rv9SeK3/T3et/011rP9Kc6v/R3Gq\n/0NuqP87ZqP5HEWDVAAAAA
        AAAAAAAAAAAAAAAAA+aKP5SX/D/z53v/8+d77/Pne+/z52vv89dr7/\nPXa+/z12
        vv89dr7/PXa+/z12vv8+dr7/Pna+/z53vv8+d77/P3e//z93v/9HfsP/OmWh+QAA
        AAAA\nAAAAAAAAAAAAAABGcKj/PXS8/0B2vf9Adr3/QHa9/0B2vf9Adr3/QHa9/0
        B2vf9Adr3/QHa9/z91\nvP9DeL7/g6bU/5u43f+bt9z/jq7Y/1yKx/8+dLz/Qmyn
        /wAAAAAAAAAAAAAAAAAAAABJcaj/PHK4\n/z90uf8/dLn/P3S5/z90uf8/dLn/P3
        S5/z90uf8/dLn/PnO5/3+i0P//////////////////////\n/////6G73f88crj/
        RW6m/wAAAAAAAAAAAAAAAAAAAABKcaj/O3C1/z5ytv8+crb/PnK2/z5ytv8+\ncr
        b/PnK2/z5ytv8+crb/S3u7///////+/v7//v7+/////////////////6G62/87cL
        X/SG+n/wAA\nAAAAAAAAAAAAAAAAAABLcqf/OW2y/z1ws/89cLP/PXCz/z1ws/89
        cLP/PXCz/z1ws/89cLP/j6zT\n/////////////////4Gjzv9AcrT/T326/1eDvf
        85brL/SnGn/wAAAAAAAAAAAAAAAAAAAABMcqf/\nN2uv/ztusP87brD/O26w/ztu
        sP87brD/O26w/zxvsP8uZKv/orrZ//7+/v///////f7+/yJcpv8v\nZav/Mmes/z
        tusP83a6//S3Gn/wAAAAAAAAAAAAAAAAAAAABMcqb/Nmmr/zpsrf86bK3/Omyt/z
        ps\nrf86bK3/Omyt/y5jqP//////////////////////////////////////1N/t
        /zRoq/82aav/TXKm\n/wAAAAAAAAAAAAAAAAAAAABMcaX/NWeo/zlqqv85aqr/OW
        qq/zlqqv85aqr/OWqq/yxhpf//////\n////////////////////////////////
        z9vq/zNmqP80Z6j/TXKm/wAAAAAAAAAAAAAAAAAAAABL\ncKT/NGWl/zhop/84aK
        f/OGin/zhop/84aKf/OGin/zFjpP+iudb/1d/s/////////////////5qy\n0v+e
        ttT/hqPK/zVmpv8zZaX/TnOl/wAAAAAAAAAAAAAAAAAAAABJbqL/MmOi/zZmo/82
        ZqP/Nmaj\n/zZmo/82ZqP/Nmaj/zZmo/80ZaP/qL3X/////////////////yxen/
        82ZqT/Nmak/zZmpP8yY6L/\nTnKl/wAAAAAAAAAAAAAAAAAAAABHbaH/MmGf/zVk
        of81ZKH/NWSh/zVkof81ZKH/NWSh/zVkof80\nY6D/qLzW/////////////////y
        xdnP81ZKD/NWSg/zVkoP8xYZ//TXGj/wAAAAAAAAAAAAAAAAAA\nAABEap//MGCc
        /zRinv80Yp7/NGKe/zRinv80Yp7/NGKe/zRinv8yYZ3/p7zV////////////////
        \n/ypamf80Yp7/NGKe/zRinv8vX5z/S3Ci/wAAAAAAAAAAAAAAAAAAAABCaJz/L1
        6Z/zJgm/8yYJv/\nMmCb/zJgm/8yYJv/MmCb/zJgm/8wX5r/p7vU////////////
        /////ylYlv8yYJv/MmCb/zJgm/8u\nXZn/SW2g/wAAAAAAAAAAAAAAAAAAAAA+ZZ
        r/K1mV/ytZlP8rWZT/K1mU/ytZlP8rWZT/K1mU/ytZ\nlP8pWJP/pLfR////////
        /////////yFRj/8rWZT/K1mU/ytZlP8qWZT/Rmue/wAAAAAAAAAAAAAA\nAAAAAA
        A6YZf/ZYWv/52yzP+dssz/nbLM/52yzP+dscz/nbHM/52xzP+cscz/1N3p//////
        //////\n/////5etyf+cscz/nLHM/5yxzP9fga3/RGic/wAAAAAAAAAAAAAAAAAA
        AAA2XZT/YYKs/5esyP+X\nrMj/l6zI/5esyP+XrMj/l6zI/5esyP+Wq8j/0tvn//
        ///////////////5Koxv+XrMj/l6zI/5es\nyP9cfqn/QGWZ/wAAAAAAAAAAAAAA
        AgAAAAAyWpH/YIGq/5arxv+Vq8b/lavG/5Wrxv+Vq8b/lavG\n/5Wrxv+Vqsb/0d
        vm/////////////////5GnxP+Vq8b/lavG/5asxv9bfaf/PGKW/wAAAAAAAAAC\n
        AAAABQAAAAwqUov8Nl6R/19+p/9ffqf/Xn6n/15+p/9efab/XX2m/119pv9dfKb/
        e5W2/5Gnw/+R\np8P/lanE/1t7pf9dfab/Xn2n/119pv83X5L/M1qQ/AAAAAwAAA
        AFAAAACgAAACgSK0+NKlGK/DFa\nkv82XZX/OWCW/zximP8/ZZr/Qmeb/0NonP9E
        aZ3/Rmqd/0Zrnf9Gap3/RGmc/0NonP9BZ5v/P2WZ\n/zximP8zWI/8EitQjQAAAC
        gAAAAKAAAACAAAACIAAABIAAAAWwAAAGIAAABjAAAAYwAAAGMAAABj\nAAAAYwAA
        AGMAAABjAAAAYwAAAGMAAABjAAAAYwAAAGMAAABjAAAAYwAAAGIAAABbAAAASAAA
        ACIA\nAAAIAAAAAwAAAA0AAAAcAAAAJgAAACkAAAApAAAAKQAAACkAAAApAAAAKQ
        AAACkAAAApAAAAKQAA\nACkAAAApAAAAKQAAACkAAAApAAAAKQAAACkAAAAmAAAA
        HAAAAA0AAAADAAAAAAAAAAIAAAAFAAAA\nBgAAAAYAAAAHAAAABwAAAAcAAAAHAA
        AABwAAAAcAAAAHAAAABwAAAAcAAAAHAAAABwAAAAcAAAAH\nAAAABwAAAAYAAAAG
        AAAABQAAAAIAAAAA\n
        """
        fbimage = base64.decodestring(fbimageencoded)
        pixbuf = gtk.gdk.pixbuf_new_from_data(fbimage, gtk.gdk.COLORSPACE_RGB, True, 8, 24, 24, 96)
        icon_set = gtk.IconSet(pixbuf)
        factory.add('facebook-logo', icon_set)
        if self.unread:
            self.addunread()
            self.unreadid = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.unreadcheck)
            self.unreadid.start()
        if self.pokes:
            self.addpokes()
            
            self.pokesid = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.pokescheck)
            self.pokesid.start()

            
        self.controller.mainWindow.userPanel.vbox2h1.show_all()
        ##Adds a button to the conversation manager if enabled
        if self.buttonconv:
            for conversation in self.getOpenConversations():
                self.addbuttonconv(conversation=conversation)
            self.buttonadded = self.controller.conversationManager.connect_after('new-conversation-ui',
                                                                         self.addbuttonconv)
            self.buttonremove = self.controller.conversationManager.connect('close-conversation-ui',
                                                                         self.removebuttonconv)
        self.hbox = gtk.HBox()
        if self.buttonhome:
            self.addbuttonhome()
        ##Check for a new personal image if enabled
        if self.avatar:
            self.setavatar()
        self.enabled = True
        ##Check for a new status if enabled, and starts the timer
        if self.status == '1':
            self.checkstatus()            
            self.timeout = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.checkstatus)
            self.timeout.start()
            
        if self.config.getPluginValue(self.name, 'comments','1') == '1':
            self.commentsbutton()
            self.commentsid = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.commentscheck)
            self.commentsid.start()
            
        self.controller.mainWindow.userPanel.vbox2h2.pack_start(self.hbox,True,False)
        self.hbox.show_all()

        self.msn.connect( 'self-personal-message-changed', self.changestatus )

    def getcomments(self):
        
        comment_id = self.config.getPluginValue(self.name, 'uid', '')+'_'+self.config.getPluginValue(self.name, 'status_id', '')
        count = len(self.fb.fql.query('SELECT "" FROM comment WHERE post_id="'+ comment_id +'"'))
        
        if self.config.getPluginValue(self.name, 'commentscounted', '') != str(count):
            brutcomments = self.fb.stream.getComments(comment_id)
            self.uids = []
            for x in brutcomments:
                if ((str(x['fromid']) in self.config.getPluginValue(self.name, 'uids', '')) == False) and ((str(x['fromid']) in self.uids) == False):
                    urlimage = (self.fb.users.getInfo(str(x['fromid']), ['pic_square'])[0])['pic_square']
                    if urlimage != None:
                        urllib.urlretrieve(urlimage, self.dest_filename + str(x['fromid']) + '.jpg')
                    else:
                        urllib.urlretrieve('http://static.ak.fbcdn.net/pics/q_silhouette_logo.gif', self.dest_filename + str(x['fromid']) + '.jpg')
                self.uids.append(str(x['fromid']))
            names = self.fb.users.getInfo(self.uids,'name')
            nameslist = []
            for x in names:
                nameslist.append(x['name'])
            def nub(inpt):
                seen = set()
                out = []
                for item in inpt:
                    if item not in seen:
                        seen.add(item)
                        out.append(item)
                return out
            ids = nub(self.uids)
            namesref = {}
            for x,y in zip(nameslist,ids):
                name = (x)+' :'
                namesref[y] = name
            self.authors = []
            self.commenttexts = []
            for x in brutcomments:
                text = x['text']
                name = namesref[str(x['fromid'])]
                self.authors.append(name)
                self.commenttexts.append(text)
            self.config.setPluginValue(self.name, 'authors', self.authors)
            self.config.setPluginValue(self.name, 'commenttexts', self.commenttexts)
            self.config.setPluginValue(self.name, 'uids', self.uids)
        else:
            self.authors = eval(self.config.getPluginValue(self.name, 'authors', ''))
            self.commenttexts = eval(self.config.getPluginValue(self.name, 'commenttexts', ''))
            self.uids = eval(self.config.getPluginValue(self.name, 'uids', ''))

        self.config.setPluginValue(self.name, 'commentscounted', str(count))
        try:
            self.commentsgetone.cancel()
        except:
            ''
        try:
            self.commentsgettwo.cancel()
        except:
            ''
    def addcomments(self, fbcomments):

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect("destroy", gtk.main_quit)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        window.set_title(_('Comments'))
        window.resize(500, 350)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scrolled_window.set_border_width(5)
        box = gtk.VBox(False, 0)
        statusMessageLabel = gtk.Label(self.config.getPluginValue(self.name, 'currentstatus', ''))
        statusMessageLabel.set_markup('<b>'+statusMessageLabel.get_text()+'</b>')
        separatorLabel = gtk.Label("--------------------------------------------------------------------------------------------")
        separatorLabel.set_markup('<big>'+separatorLabel.get_text()+'</big>')
        box.pack_start(statusMessageLabel, False, False, 0)
        box.pack_start(separatorLabel, False, False, 0)
        scrolled_window.add_with_viewport(box)
        window.add(scrolled_window)
        
        self.getcomments()
        
        size = len(self.authors)
        
        for x in range(0,size):
            commentBox = gtk.EventBox()
            commentBox.set_border_width(2)
            if not(x%2): #this check if the comment is odd
                commentBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(62708,62708,45489,0))
            contactImage = gtk.Image()
            contactImage.set_from_file(self.dest_filename+str(self.uids[x])+'.jpg')
            contactImage.set_alignment(0,0)
            authorLabel = gtk.Label(self.authors[x])
            authorLabel.set_alignment(0, 0)
            authorLabel.set_markup('<u><b>'+authorLabel.get_text()+'</b></u>')
            commentLabel = gtk.Label(self.commenttexts[x])
            commentLabel.set_alignment(0, 0)
            commentLabel.set_line_wrap(True)
            HorBox = gtk.HBox(False, 20)
            HorBox.pack_start(contactImage, False, False, 0)
            HorBox.set_border_width(5)
            VerBox = gtk.VBox(False, 0)
            VerBox.pack_start(authorLabel, False, False, 0)
            VerBox.pack_start(commentLabel,True, True, 0)
            HorBox.pack_start(VerBox, True, True, 0)
            commentBox.add(HorBox)
            box.add(commentBox)

        window.show_all()

        gtk.main()


    def commentsbutton(self):
        fbimageencoded = \
        """R5YOAEaWDQBGlgwARZUMAEWWDQBFlg0ARZYNAEWWDQBFlg0ARZYNAEWWDQBFlg0A
        RZYNAEWWDQBF\nlg0ARZYNAEWWDQBFlg0ARZYNAEWWDQBFlQwARpYMAEaWDQBHlg
        4ARZUMAEaWDABOmxYAZKcuAGao\nMQBmqDAAZqgxAGaoMQBmqDEAZqgxAGaoMQBm
        qDEAZqgxAGaoMQBmqDEAZqgxAGaoMQBmqDEAZqgw\nAGaoMQBkpy4ATpsWAEaWDA
        BFlQwARZUMAEaWDQB1sEIAlsNmAJbCZgCXw2cAl8NnAJfDZgCXw2YA\nl8NnAJfD
        ZwCXw2cAl8NmAJfDZgCXw2YAl8NmAJfDZgCXw2YAl8NnAJbCZgCWw2YAdbBCAEaW
        DQBF\nlQwARZUMAEeXDgCBtk4AksBiAJLAYQCRv2AAkb9gAJLAYQCSwGEAksBhAJ
        G/YACRwGAAk8FiAJLA\nYQCSwGEAksBhAJLAYQCSwGEAksBhAJLAYQCSwGIAgbZO
        AEeXDgBFlQwARZUMAEaWDgCAtk0Ak8Fi\nAEaWDENIlw/fSZgR/kmYEf9JmBH+SZ
        gR/0mYEf9JmBH/SZgR/0mYEf9JmBH/SZgR/kmYEf9JmBH+\nSJcP30aWDEOTwWIA
        gLZNAEaWDgBFlQwARZUMAEeWDgCAtk0Akb9gAEqYEe95s0b/hrlV/oe6Vf6H\nul
        X/h7pV/4e6Vf+Hulb/h7pV/4e6Vf+HulX/h7pV/4e6Vf6GuVX+ebNG/0qYEe+TwW
        IAgLZNAEeW\nDgBFlQwARZUMAEeWDgB+tUsAlsJmAE6bFv6OvV3+kb9h/5C+X/+R
        v2D+kb9g/5G/YP+Qv1//ksBh\n/5G/YP+Rv2D/kb9g/pG/YP+Rv2H/jr1d/k6bFv
        6TwWMAgLZNAEeWDgBFlQwARZUMAEaWDgB+tUoA\nsdGNAE6aFv+NvVv+kcBg/q/R
        jP+Xw2n/kL5e/6nMgf+fxnT/kb9f/5PBYv+TwWL/k8Fi/5PBYv+S\nwGH+jr5c/k
        6aFv+TwGEAgLZNAEaWDgBFlQwARZUMAEaWDQCAtk4AzuK3AE6aFv6Ju1b/y+G1/9
        7s\n0P+Vwmb/ncZy/+vz4v+jyXr/kb9g/5PBYv+TwWL/ksBh/5PBYv+TwWL/jr5d
        /06aFv6axGwAfrZL\nAEeWDgBFlQwARZUMAEaWDQCBt08A1ufDAEyZFf+exnP///
        ///7fUl/+Dt0v/3+zS/97sz/+TwGP/\nkcBg/5bCZ/+SwGH/kcBg/5TBZP+Wwmf/
        jb1b/02aFv/I364AgLZNAEaWDQBFlQwARZUMAEaWDgB/\ntUsAtNORAE2ZFP+z05
        L//v7+/+Tv2P+TwGL/9vny//7+/v+lyn3/pMp7//X48f/X58b/kL9e/93r\n0P/v
        9uj/oMh2/02ZFP/W6MMAgbdPAEaWDQBFlQwARZUMAEeWDgB/tk0AlMJkAE2ZFf+a
        xG3/8ffr\n/9rqy/+NvVv/zeK3//T48P+hyHb/osl5//r8+P/z9+3/ksBh/+Ht0/
        /9/v3/stOR/02ZFP/F3aoA\nf7ZMAEaWDgBFlQwARZUMAEeWDgCAtk0Ak8FiAE6a
        Fv+NvVv/kL9e/5C/X/+SwGH/kL5e/5C/Xv+S\nwGD/k8Bj/97s0P/a6cj/g7hM/7
        fUl///////msVu/02ZFf+iynkAfbRJAEeWDgBFlQwARZUMAEeW\nDgCAtk0Ak8Fi
        AE6aFv6Ovlz/ksFh/5LAYf+SwGL/ksBh/5PBYv+Qvl//qc2D/+z05f+WwWf/mMRr
        \n/+ny3/+82Z//irtX/06aFv6SwGEAgLZNAEeWDgBFlQwARZUMAEaWDgCAtk0Ak8
        FjAE6aFv6OvV3+\nksBh/5LAYf6TwWL/k8Fi/5LAYf+SwGD/ncZx/6DId/+RwGD/
        l8Jo/6jMgv6PvVz/jr5c/k6aFv6T\nwWEAgLZNAEaWDgBFlQwARZUMAEeWDgCBtk
        0Ak8BiAE6aFv+Pvl3+ksBh/pPBYv+SwGH/ksBh/5G/\nYP+TwWL+ksBh/5LAYf+T
        wWL/k8Bi/5LAYP+SwGH+j75e/k6aFv+TwGIAgbZNAEeWDgBFlQwARZUM\nAEaWDg
        B/tk0Ak8FiAEmYEOt2sEL/hLhS/4W4U/+Pvl7+ksBh/pPAYv6KvFn/hLhR/4S4Uv
        +EuFL/\nhLhS/4S4Uv+EuFL/drBC/0mYEOuTwWIAf7ZNAEaWDgBFlQwARZUMAEaW
        DABmqDAAirxZAEWVDD1G\nlQ2xSJgQu0uYEu+GuFP+l8Nn/nuzR/9Qmxj/SJcPuE
        iXEL1IlxC9SJcQvUiXEL1IlxC9RpUNsUWV\nDD2KvFkAZqgwAEaWDABFlQwARpYN
        AEaWDQBHlg8AUZwZAFOeHABElAoBaqo0AEqXEMKJu1f/aak0\n/kWVDPBElQtKU5
        4bAEOUCgFDlAoBQ5QKAUOUCgFDlAoBRJQLAVOeHABRnBkAR5YPAEaWDQBGlg0A\n
        AAAAAEeXDgBFlQwARZUMAESVCwBCkwcASZYQAkiXEMZRnBn/QJIHv0OUCi5FlgwA
        RZULAESVCwBE\nlQsARJULAESVCwBElQsARJULAESVCwBFlQwARZUMAEeXDgAAAA
        AAR5cOAAAAAAAAAAAAAAAAAEmW\nEQBBkwcARZUMAUWVDKdElAtqRZUMCUSVCwBG
        lg0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAA
        BHlw4AAAAAAAAAAAAAAAAAAAAAAEaVDQBDlAoAWKAhAF2iJgBFlQwA\nRJULAEeW
        DgAAAAAAAAAAAEeXDgAAAAAAAAAAAAAAAAAAAAAARpYNAAAAAABGlg0AAAAAAAAA
        AAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAEaWDQBGlg0ARpYNAEWVDABFlQwAR5YOAA
        AAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAEaWDQBGlg0ARpYNAEWVDABGnA0AAA
        AAAC5+AABHlw4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAA\n
        """
        fbimage = base64.decodestring(fbimageencoded)
        commentsicon = gtk.gdk.pixbuf_new_from_data(fbimage, gtk.gdk.COLORSPACE_RGB, True, 8, 24, 24, 96)
        self.fbcomments = ImageButton(commentsicon,'(0)')
        self.fbcomments.set_relief(gtk.RELIEF_NONE)
        self.fbcomments.connect('clicked',self.addcomments)
        self.fbcomments.set_tooltip_text(_("My current Facebook status' comments"))
        if self.config.getPluginValue(self.name, 'statusprinted', '') != '':
            comment_id = self.config.getPluginValue(self.name, 'uid', '')+'_'+self.config.getPluginValue(self.name, 'status_id', '')
            count = len(self.fb.fql.query('SELECT "" FROM comment WHERE post_id="'+ comment_id +'"'))
        else:
            count = '0'
        if str(count) != '0' and self.config.getPluginValue(self.name, 'statusprinted', '') != '':
            self.fbcomments.setText('('+str(count)+')')
            self.hbox.pack_start(self.fbcomments, True, False)
            self.commentsactive = True
        else:
            self.commentsactive = False
    def addbuttonhome(self):
        self.fbbuttonmain = gtk.ToolButton()
        self.fbbuttonmain.set_label('Facebook')
        self.fbbuttonmain.set_stock_id('facebook-logo')
        self.fbbuttonmain.connect('clicked',self.gofacebook)
        self.fbbuttonmain.set_tooltip_text(_("Go to your Facebook homepage"))
        self.hbox.pack_end(self.fbbuttonmain,True,False)

    def addpokes(self):
        pkcount = (self.fb.notifications.get()['pokes'])['unread']
        iconPoke = self.theme.getSmiley("(y)") #poke icon
        self.fbpk = ImageButton(iconPoke, '(0)')
        self.fbpk.set_relief(gtk.RELIEF_NONE)
        self.fbpk.connect('clicked', self.gofacebook)
        self.fbpk.setText('(' + str(pkcount) + ')')
        self.fbpk.set_tooltip_text(_("Facebook - %s unread poke(s)") % str(pkcount))
        if str(pkcount) != '0':
            self.controller.mainWindow.userPanel.vbox2h1.pack_start(self.fbpk, True, False)
            self.pokesactive = True
        else:
            self.pokesactive = False

    def addunread(self):
        fbmailencoded = \
        """RoPEAEaDxABGgsMARoLDAEaCwwBGgsMARoLDAEaCwwBGgsMARoLDAEaCwwBGgsMA
        RoLDAEaCwwBG\ngsMARoLDAEaCwwBGgsMARoLDAEaCwwBGgsMARoLDAEaCwwBGgs
        MARoPEAEaCwwBGgsMARoLDAEaC\nwwBGgsMARoLDAEaCwwBGgsMARoLDAEaCwwBG
        gsMARoLDAEaCwwBGgsMARoLDAEaCwwBGgsMARoLD\nAEaCwwBGgsMARoLDAEaCww
        BGgsMARoLDAEaCwwBVmMkAc6DQAHOg0ABzoNAAc6DQAHOg0ABzoNAA\nc6DQAHOg
        0ABzoNAAc6DQAHOg0ABzoNAAc6DQAHOg0ABzoNAAc6DQAHOg0ABzoNAAVZjJAEaC
        wwBG\ngsMARoLDAKTC4AD///8A////AP///wD///8A////AP///wD///8A////AP
        ///wD///8A////AP//\n/wD///8A////AP///wD///8A////AP///wD///8A////
        AKTC4ABGgsMARoLDAP///wD///8A////\nAP///wD///8A////AP///wD///8A//
        //AP///wD///8A////AP///wD///8A////AP///wD///8A\n////AP///wD///8A
        ////AP///wBCf74ARoLDAP///wD///8A/v7+IlJ1xf9SdcX/UnXF/1J1xf9S\ndc
        X/UnXF/1J1xf9SdcX/UnXF/1J1xf9SdcX/UnXF/1J1xf9SdcX/UnXF/1J1xf////
        8i////AP//\n/wBCf74ARoLDAP///wD///8AUnXF//////3//////////+70+f/g
        6/T/4ev0/+Hr9P/h6/T/4ev0\n/+Hr9P/h6/T/4ez0/9zp8////v7///////////
        1SdcX/////AP///wBCf74ARoLDAP///wD///8A\nUnXF//f6/P/4+vz//////+Tt
        9v9bfMj/bInO/2qIzf9qiM3/aojN/2qIzf9sic7/ZIPL/7rO3///\n//////////
        ///v9SdcX/////AP///wBCf74ARoLDAP///wD///8AUnXF/9bj8v+Tt9v//Pz9//
        //\n//+gwOD/WoLI/1t8yP9bfMj/W3zI/1t8yP9XeMf/aIfN//38+/////7/xdjk
        /9vq8/9SdcX/////\nAP///wBCf74AQn++AP///wD///8AUnXF/9Ph8f9SdcX/bY
        rO//n5+v/8/Pv/ts7f/2B/yv9bfMj/\nXn7J/1t8yP92kdH/7fP5//////+70ej/
        UnXF/9Lh8f9SdcX/////AP///wBCf74ARoLDAP///wD/\n//8AUnXF/9Ph8f9Uds
        b/W3zI/1t8yP///////////8HW6f9nhcz/YH/K/5y73P/2+fz//////5e5\n3P9U
        dsb/VHbG/9Ph8f9SdcX/////AP///wBCf74AQn++AP///wD///8AUnXF/9Ph8f9U
        dsb/Xn7J\n/1x9yP+xy+X/8/f7///////P3u7/q83i///++f////7/2Ofv/1h5x/
        9efsn/VHbG/9Ph8f9SdcX/\n////AP///wBCf74AQn++AP///wD///8AUnXF/9Ph
        8f9Udsb/Xn7J/1t8yP9bfMj/lbnc//D0+P//\n//////////////+7z+X/Z4XM/1
        x9yP9efsn/VHbG/9Ph8f9SdcX/////AP///wBCf74AQn++AP//\n/wD///8AUnXF
        /9Ph8f9Vd8b/Xn7J/15+yf9efsn/XH3I/3ic0//s7ez//////5283v9gf8r/XH3I
        \n/15+yf9efsn/VXfG/9Ph8f9SdcX/////AP///wBCf74ALHu3AP///wD///8AUn
        XF/8zg7v9IbMH/\nT3LE/09yxP9PcsT/T3LE/09yxP9ll87/c6zS/01xw/9PcsT/
        T3LE/09yxP9PcsT/SGzB/8zg7v9S\ndcX/////AP///wAse7cAKH+5AP///wD///
        8AUnXF/8vg7v9EasD/T3LE/09yxP9PcsT/T3LE/09y\nxP9NccP/THDD/09yxP9P
        csT/T3LE/09yxP9PcsT/RGrA/8vg7v9SdcX/////AP///wAWebMAFnmz\nAP///w
        D///8AUnXF/8vi7/1NccP/V3jH/1d4x/9XeMf/V3jH/1d4x/9XeMf/V3jH/1d4x/
        9XeMf/\nV3jH/1d4x/9XeMf/TXHD/8zi7/9SdcX/////AP///wAWebMAFnmzAP//
        /wD///8AUnXF/1J1xf/Y\n5/L92unz/9rp8//a6fP/2unz/9rp8//a6fP/2unz/9
        rp8//a6fP/2unz/9rp8//a6fP/2Ojy/1J1\nxf9SdcX/////AP///wAWebMAFnmz
        AP///wD///8A////AFJ1xf9SdcX/UnXF/1J1xf9SdcX/UnXF\n/1J1xf9SdcX/Un
        XF/1J1xf9SdcX/UnXF/1J1xf9SdcX/UnXF/1J1xf/+/v4j////AP///wAFc6oA\n
        CHixAJG42gD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A
        ////AP///wD/\n//8A////AP///wD///8A////AP///wD///8A////AJG42gAFc6
        oACHixAAh4sQAof7kARZS8AEWU\nvABFlLwARZS8AEWUvABFlLwARZS8AEWUvABF
        lLwARZS8AEWUvABFlLwARZS8AEWUvABFlLwARZS8\nAEWUvABFlLwAKH+5AAVzqg
        AFc6oACHixAAh4sQAIeLEABXOqAAVzqgAFc6oABXOqAAVzqgAFc6oA\nBXOqAAVz
        qgAFc6oABXOqAAVzqgAFc6oABXOqAAVzqgAFc6oABXOqAAVzqgAFc6oABXOqAAVz
        qgAF\nc6oAA3ixAAN4sQADeLEABXOqAAVzqgAFc6oABXOqAAVzqgAFc6oABXOqAA
        VzqgAFc6oABXOqAAVz\nqgAFc6oABXOqAAVzqgAFc6oABXOqAAVzqgAFc6oABXOq
        AAVzqgAFc6oAA3ixAAN4sQADeLEAA3ix\nAAVzqgAFc6oABXOqAAVzqgAFc6oABX
        OqAAVzqgAFc6oABXOqAAVzqgAFc6oABXOqAAVzqgAFc6oA\nBXOqAAVzqgAFc6oA
        BXOqAAVzqgADeLEA\n
        """
        fbmail = base64.decodestring(fbmailencoded)
        fbpmpixbuf = gtk.gdk.pixbuf_new_from_data(fbmail, gtk.gdk.COLORSPACE_RGB, True, 8, 24, 24, 96)
        pmcount = (self.fb.notifications.get()['messages'])['unread']
        self.fbpm = ImageButton(fbpmpixbuf, '(0)')
        self.fbpm.set_relief(gtk.RELIEF_NONE)
        self.fbpm.connect('clicked', self.gofacebookinbox)
        self.fbpm.setText('(' + str(pmcount) + ')')
        self.fbpm.set_tooltip_text(_("Facebook - %s unread message(s)") % str(pmcount))
        if str(pmcount) != '0':
            self.controller.mainWindow.userPanel.vbox2h1.pack_start(self.fbpm, True, False)
            self.unreadactive = True
        else:
            self.unreadactive = False

    def addbuttonconv(self, conversationManager=None, conversation=None, window=None):
        '''This function adds a button. If clicked, it calls gofacebook'''
        self.fbbutton = gtk.ToolButton()
        self.fbbutton.set_label(_('Facebook'))
        self.fbbutton.set_stock_id('facebook-logo')
        self.fbbutton.connect('clicked',self.gofacebook)
        self.fbbutton.set_tooltip_text(_("Go to your Facebook homepage"))
        self.fbbutton.show()
        conversation.ui.input.toolbar.add(self.fbbutton)
        conversation.ui.input.toolbar.insert(gtk.SeparatorToolItem(), -1)

    def removebuttonconv(self, conversationManager=None, conversation=None, window=None):
        for button in conversation.ui.input.toolbar.get_children():
            conversation.ui.input.toolbar.remove(self.fbbutton)
            self.fbbutton.destroy()
    def gofacebook(self, fbbutton):
        '''Opens a new tab (if any) and goes to facebook'''
        desktop.open('http://www.facebook.com/home.php')

    def gofacebookinbox(self, fbpm):
        '''Opens a new tab (if any) and goes to facebook'''
        desktop.open('http://www.facebook.com/inbox/')

    def stop(self):
        '''This is called when the plugin is stopped'''
        ##Removes the status checking if enabled
        if self.status == '1':
            self.timeout.cancel()            
        if self.pokes:
            self.pokesid.cancel()
        if self.comments:
            self.commentsid.cancel()
        if self.unread:
            self.unreadid.cancel()
        ##Removes buttons from conversation if exists
        if self.buttonconv:
            self.controller.conversationManager.disconnect(self.buttonremove)
            self.controller.conversationManager.disconnect(self.buttonadded)
            for conversation in self.getOpenConversations():
                self.removebuttonconv(conversation=conversation)
        ##Removes buttons from homepage if exists
        if self.buttonhome:
            self.fbbuttonmain.destroy()
        if self.unread and self.unreadactive == True :
            self.fbpm.destroy()
        if self.pokes and self.pokesactive == True :
            self.fbpk.destroy()
        if self.comments and self.commentsactive == True:
            self.fbcomments.destroy()
        self.enabled = False

    def check(self):
        '''This part is used for checkings before the plugin to be started'''
        api_key = '92d4a977a81ac68bb53fdb4dac115fd9'
        secret_key = 'd51f6f904f0082684c899d4d511fe99b'
        self.fb = Facebook(api_key, secret_key)
        if self.config.getPluginValue(self.name, 'expires', '') == '0' :
            self.fb.session_key = self.config.getPluginValue(self.name, 'session_key', '')
            self.fb.secret = self.config.getPluginValue(self.name, 'secret', '')
            self.fbreturn = True

        ## If it expires, get a new auth :
        else:
            if self.config.getPluginValue(self.name, 'session_key', '') != '':
                uidgotten = str(self.fb.users.getLoggedInUser())
                updatestatus = self.fb.users.hasAppPermission("status_update",uidgotten)
            else:
                uidgotten = '00'
                updatestatus = '00'
            if uidgotten == self.config.getPluginValue(self.name, 'uid','') and str(updatestatus) == '1':
                self.auth = self.fb.auth.getSession()
                self.config.setPluginValue( self.name, 'session_key', self.auth['session_key'] )
                self.config.setPluginValue( self.name, 'secret', self.auth['secret'] )
                self.config.setPluginValue( self.name, 'expires', str(self.auth['expires']) )
            else:        
                self.fb.auth.createToken()
                self.fb.login(popup=True)
                def authbox():
                    mdone = gtk.MessageDialog(None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                            gtk.BUTTONS_OK_CANCEL, _('Please login on Facebook (just opened in your browser). Check the box "Keep me logged in to Emesene Plugin". Then you can valid.'))
                    response = mdone.run()
                    mdone.destroy()
                    if response == gtk.RESPONSE_OK:
                        try:
                            self.auth = self.fb.auth.getSession()
                            self.config.setPluginValue( self.name, 'session_key', self.auth['session_key'] )
                            self.config.setPluginValue( self.name, 'secret', self.auth['secret'] )
                            self.config.setPluginValue( self.name, 'uid', self.auth['uid'] )
                            self.config.setPluginValue( self.name, 'expires', str(self.auth['expires']) )
                            
                            self.fb.request_extended_permission('status_update', popup=False)
                            
                            md = gtk.MessageDialog(None,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                                 gtk.BUTTONS_YES_NO, _("Now, you can authorize the plugin to update your Facebook status. If you say yes, your Facebook status and your Emesene personal message will be synchronized"))
                            answer = md.run()
                            ## If the user said yes, ask facebook if the user hasAppPermission, if not, status disabled
                            if answer == gtk.RESPONSE_YES:
                                updatestatus = self.fb.users.hasAppPermission("status_update",self.config.getPluginValue(self.name, 'uid',''))
                                if str(updatestatus) == '1':
                                    self.config.setPluginValue( self.name, 'status', '1' )
                                else:
                                    md = gtk.MessageDialog(None,
                                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                                         gtk.BUTTONS_OK, _("You don't have the permission to update your Facebook status with this plugin. The status synchronization option has been disabled, but you can still enable it in the plugin properties."))
                                    md.run()
                                    md.destroy()
                                    self.config.setPluginValue( self.name, 'status', '0' )
                            else:
                                self.config.setPluginValue( self.name, 'status', '0' )
                            md.destroy()
                            self.fbreturn = True
                            self.enabled = True
                        except:
                            md = gtk.MessageDialog(None,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                                 gtk.BUTTONS_OK, _("The authentication process didn't work. Please try again"))
                            md.run()
                            md.destroy()
                            self.fb.auth.createToken()
                            self.fb.login(popup=True)
                            authbox()
                    else:
                        self.fbreturn = False
                authbox()
        if self.fbreturn == True:
            return (True, 'Ok')
        else:
            return (False, _('As you cancelled, this plugin was disabled. But you can enable it in the plugins list.'))
    def configure(self):
        '''Display a configuration dialog'''
        l = []
        ##STATUS SYNCHRONIZATION##

        l.append(Plugin.Option('', gtk.Widget, '', '', gtk.Label(_("[ Facebook synchronization ]"))))

        l.append(Plugin.Option('status', bool, \
                _('Synchronize my Facebook status and my Emesene personal message'), '', self.config.\
                getPluginValue(self.name, 'status', '1') == '1'))
        
        l.append(Plugin.Option('avatar', bool, \
                _('Update my Emesene avatar from my Facebook profile image (on every startup)'), '', self.config.\
                getPluginValue(self.name, 'avatar', '1') == '1'))
        ##STATUS DISPLAY
        l.append(Plugin.Option('', gtk.Widget, '', '', gtk.Label(_("[ Status display ]"))))

        l.append(Plugin.Option('prefix', str, _("Custom status prefix (can be blank):"), '',\
            self.config.getPluginValue( self.name, 'prefix', '' )) )
        l.append(Plugin.Option('suffix', str, _("Custom status suffix (can be blank):"), '',\
            self.config.getPluginValue( self.name, 'suffix', '' )) )

        l.append(Plugin.Option('time', bool, \
                _('Show time (default is messages such as "2 hours ago")'), '', self.config.\
                getPluginValue(self.name, 'time', '0') == '1'))
        l.append(Plugin.Option('format', str, _("Custom time (example: \'%(q)sx, %(q)sX\'):") % {'q': '%'}, '',\
            self.config.getPluginValue( self.name, 'format', '' )) )

        l.append(Plugin.Option('separator', list, _('Time separator'), '',
                 self.config.getPluginValue\
                         ( self.name, 'separator', '[Time]' ), ['[Time]', '(Time)', '-- Time', 'Time' ]))

        ##MISC
        l.append(Plugin.Option('', gtk.Widget, '', '', gtk.Label(_("[ Miscellaneous ]"))))
        l.append(Plugin.Option('checktime', str, _('Check for Facebook every [sec]:'), '',\
            self.config.getPluginValue( self.name, 'checktime', '30' )) )
        l.append(Plugin.Option('confirmation', bool, \
                _('Display a confirmation box before my Facebook status to be updated'), '', self.config.\
                getPluginValue(self.name, 'confirmation', '1') == '1'))
        l.append(Plugin.Option('buttonhome', bool, \
                _('Add a "Facebook Homepage" button to the main window'), '', self.config.\
                getPluginValue(self.name, 'buttonhome', '1') == '1'))
        l.append(Plugin.Option('buttonconv', bool, \
                _('Add a "Facebook Homepage" button to each conversation windows'), '', self.config.\
                getPluginValue(self.name, 'buttonconv', '0') == '1'))
        l.append(Plugin.Option('unread', bool, \
                _('Notify for unread messages on the main window'), '', self.config.\
                getPluginValue(self.name, 'unread', '1') == '1'))
        l.append(Plugin.Option('pokes', bool, \
                _('Notify for unread pokes on the main window'), '', self.config.\
                getPluginValue(self.name, 'pokes', '0') == '1'))
        l.append(Plugin.Option('comments', bool, \
                _('Display comments for my current Facebook status'), '', self.config.\
                getPluginValue(self.name, 'comments', '1') == '1'))


        response = Plugin.ConfigWindow(_('Facebook Plugin'), l).run()
        ## If the user didn't cancel :

        if response != None:
            ## Used for the plugin not to ask for a fb update if the user sets time display
            self.timechanged = False

            ##Sets the new checktimetime, if it has changed
            if self.config.getPluginValue(self.name, 'checktime', '30') != str(int(response['checktime'].value)):
                self.config.setPluginValue(self.name, 'checktime', str(int(response['checktime'].value)))
                self.timeout.cancel()
                self.timeout = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.checkstatus)
                self.timeout.start()
                
            if self.config.getPluginValue(self.name, 'confirmation', '1') != str(int(response['confirmation'].value)):
                self.config.setPluginValue(self.name, 'confirmation', str(int(response['confirmation'].value)))
            
            if self.config.getPluginValue(self.name, 'comments', '1') != str(int(response['comments'].value)):
                self.config.setPluginValue(self.name, 'comments', str(int(response['comments'].value)))
                if self.config.getPluginValue(self.name, 'comments', '1') == '1':
                    self.config.setPluginValue( self.name, 'comments', '1' )
                    self.commentsid = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.commentscheck)
                    self.commentsid.start()
                    
                    self.commentsbutton()
                    self.hbox.show_all()
                else:
                    self.fbcomments.destroy()
                    self.commentsid.cancel()

            ##Sets the new status value
            if str(int(response['status'].value)) == '1':
                if self.config.getPluginValue(self.name, 'status', '1') == '0':
                    updatestatus = self.fb.users.hasAppPermission("status_update",self.config.getPluginValue(self.name, 'uid',''))
                    if str(updatestatus) != '1':
                        self.fb.request_extended_permission("status_update", popup=True)
                        md = gtk.MessageDialog(None,
                             gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                             gtk.BUTTONS_YES_NO, _("Now, you can authorize the plugin to update your Facebook status. If you say yes, your Facebook status and your Emesene personal message will be synchronized"))
                        answer = md.run()
                        md.destroy()
                        if answer == gtk.RESPONSE_YES:
                            updatestatus = self.fb.users.hasAppPermission("status_update",self.config.getPluginValue(self.name, 'uid',''))
                            
                            if str(updatestatus) == '1':
                                self.config.setPluginValue( self.name, 'status', '1' )
                                self.status = self.config.getPluginValue \
                                    (self.name, 'status', '1')
                                self.checkstatus()
                                self.timeout = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.checkstatus)
                                self.timeout.start()
                            else:
                                self.config.setPluginValue( self.name, 'status', '0' )
                                self.status = self.config.getPluginValue \
                                    (self.name, 'status', '1')
                                md = gtk.MessageDialog(None,
                                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                                     gtk.BUTTONS_OK, _("You don't have the permission to update your Facebook status with this plugin. The status synchronization option has been disabled, but you can still enable it in the plugin properties."))
                                md.run()
                                md.destroy()
                        else:
                            self.status = self.config.getPluginValue \
                                (self.name, 'status', '1')
                            self.config.setPluginValue( self.name, 'status', '0' )
                    else:
                        self.config.setPluginValue( self.name, 'status', '1' )
                        self.status = self.config.getPluginValue \
                            (self.name, 'status', '1')
                        self.checkstatus()
                        self.timeout = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.checkstatus)
                        self.timeout.start()
                else:
                    self.config.setPluginValue(self.name, 'status', str(int(response['status'].value)))
                    self.status = self.config.getPluginValue \
                        (self.name, 'status', '1')
                if self.config.getPluginValue(self.name, 'time', '0') != str(int(response['time'].value)):
                    self.timechanged = True
                    self.config.setPluginValue(self.name, 'time', str(int(response['time'].value)))
                    self.time = (self.config.getPluginValue \
                    (self.name, 'time', '0') == '1')
                    self.checkstatus()
            else:
                if self.config.getPluginValue(self.name, 'status', '1') == '1':
                    try:
                        self.timeout.cancel()
                        self.fbcomments.destroy()
                        self.commentsid.cancel()
                    except:
                        ""
                self.config.setPluginValue(self.name, 'time', '0')
                self.config.setPluginValue(self.name, 'comments', '0')
                self.time = (self.config.getPluginValue \
                    (self.name, 'time', '0') == '1')
                self.config.setPluginValue(self.name, 'status', str(int(response['status'].value)))
                self.status = self.config.getPluginValue \
                    (self.name, 'status', '1')

            self.config.setPluginValue(self.name, 'status', str(int(response['status'].value)))
            self.status = self.config.getPluginValue \
                (self.name, 'status', '1')

            if self.config.getPluginValue(self.name, 'separator', '[Time]') != str(response['separator'].value):
                self.config.setPluginValue(self.name, 'separator', str(response['separator'].value))
                if self.config.getPluginValue(self.name, 'time', '0') == '1':
                    self.timechanged = True
                    self.checkstatus()
            if self.config.getPluginValue(self.name, 'prefix', '') != str(response['prefix'].value):
                self.config.setPluginValue(self.name, 'prefix', str(response['prefix'].value))
                self.timechanged = True
                self.checkstatus()
            if self.config.getPluginValue(self.name, 'suffix', '') != str(response['suffix'].value):
                self.config.setPluginValue(self.name, 'suffix', str(response['suffix'].value))
                self.timechanged = True
                self.checkstatus()
            if self.config.getPluginValue(self.name, 'format', '') != str(response['format'].value):
                self.config.setPluginValue(self.name, 'format', str(response['format'].value))
                if self.config.getPluginValue(self.name, 'time', '0') == '1':
                    self.timechanged = True
                    self.checkstatus()
            ##AVATAR
            if str(int(response['avatar'].value)) == '1' and self.config.getPluginValue(self.name, 'avatar', '1') == '0' :
                self.setavatar()
            self.config.setPluginValue(self.name, 'avatar', str(int(response['avatar'].value)))
            self.avatar = (self.config.getPluginValue \
                (self.name, 'avatar', '1') == '1')
            ##BUTTON
            ## If the "buttonconv" value changed, set the new value and add the button if it was disabled,
            ## or remove the button if it was enabled.
            if self.config.getPluginValue(self.name, 'buttonhome', '1') != str(int(response['buttonhome'].value)):
                self.config.setPluginValue(self.name, 'buttonhome', str(int(response['buttonhome'].value)))
                if self.config.getPluginValue(self.name, 'buttonhome', '1') == '1':
                    self.addbuttonhome()
                    self.hbox.show_all()
                else:
                    self.fbbuttonmain.destroy()

            if self.config.getPluginValue(self.name, 'unread', '1') != str(int(response['unread'].value)):
                self.config.setPluginValue(self.name, 'unread', str(int(response['unread'].value)))
                if self.config.getPluginValue(self.name, 'unread', '1') == '1':
                    self.unreadid = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.unreadcheck)
                    self.unreadid.start()
            
                    self.addunread()
                    self.controller.mainWindow.userPanel.vbox2h1.show_all()
                    self.unreadcheck()
                else:
                    self.fbpm.destroy()
                    self.unreadid.cancel()

            if self.config.getPluginValue(self.name, 'pokes', '0') != str(int(response['pokes'].value)):
                self.config.setPluginValue(self.name, 'pokes', str(int(response['pokes'].value)))
                if self.config.getPluginValue(self.name, 'pokes', '0') == '1':
                    
                    self.pokesid = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.pokescheck)
                    self.pokesid.start()
                
                    
                    self.addpokes()
                    self.controller.mainWindow.userPanel.vbox2h1.show_all()
                    self.pokescheck()
                else:
                    self.fbpk.destroy()
                    self.pokesid.cancel()

            if self.config.getPluginValue(self.name, 'buttonconv', '0') != str(int(response['buttonconv'].value)):
                self.config.setPluginValue(self.name, 'buttonconv', str(int(response['buttonconv'].value)))
                if self.config.getPluginValue(self.name, 'buttonconv', '0') == '1':
                    for conversation in self.getOpenConversations():
                        self.addbuttonconv(conversation=conversation)
                    self.buttonadded = self.controller.conversationManager.connect_after('new-conversation-ui',
                                                                                 self.addbuttonconv)
                    self.buttonremove = self.controller.conversationManager.connect('close-conversation-ui',
                                                                                 self.removebuttonconv)
                else:
                    self.controller.conversationManager.disconnect(self.buttonremove)
                    self.controller.conversationManager.disconnect(self.buttonadded)
                    for conversation in self.getOpenConversations():
                        self.removebuttonconv(conversation=conversation)

        return True

    def commentscheck(self):
        if self.config.getPluginValue(self.name, 'statusprinted','') != '':
            comment_id = self.config.getPluginValue(self.name, 'uid', '')+'_'+self.config.getPluginValue(self.name, 'status_id', '')
            count = len(self.fb.fql.query('SELECT "" FROM comment WHERE post_id="'+ comment_id +'"'))
            if (str(count) != '0' and self.commentsactive != True):
                self.commentsbutton()
                self.hbox.show_all()
                self.commentsgetone = SimpleThread(self.getcomments)
                self.commentsgetone.start()
            if str(count) == '0' and self.commentsactive == True:
                self.fbcomments.destroy()
                self.commentsactive = False
            elif self.config.getPluginValue(self.name, 'commentscount', '') != str(count):
                self.fbcomments.setText("("+str(count)+")")
                self.commentsgettwo = SimpleThread(self.getcomments)
                self.commentsgettwo.start()
            self.config.setPluginValue(self.name, 'commentscount', str(count))

        elif self.commentsactive == True:
            self.fbcomments.destroy()
            self.commentsactive = False
        return True

    def unreadcheck(self):
        pmcount = (self.fb.notifications.get()['messages'])['unread']
        if str(pmcount) != '0' and self.unreadactive != True:
            self.addunread()
            self.controller.mainWindow.userPanel.vbox2h1.show_all()
        if str(pmcount) == '0' and self.unreadactive == True:
            self.fbpm.destroy()
            self.unreadactive = False
        elif self.config.getPluginValue(self.name, 'unreadcount', '') != str(pmcount):
            self.fbpm.setText('(' + str(pmcount) + ')')
            self.fbpm.set_tooltip_text(_("Facebook - %s unread message(s)") % str(pmcount))
        self.config.setPluginValue(self.name, 'unreadcount', str(pmcount))
        return True

    def pokescheck(self):
        pkcount = (self.fb.notifications.get()['pokes'])['unread']
        if str(pkcount) != '0' and self.pokesactive != True:
            self.addpokes()
            self.controller.mainWindow.userPanel.vbox2h1.show_all()
        if str(pkcount) == '0' and self.pokesactive == True:
            self.fbpk.destroy()
            self.pokesactive = False
        elif self.config.getPluginValue(self.name, 'pokescount', '') != str(pkcount):
            self.fbpk.setText('(' + str(pkcount) + ')')
            self.fbpk.set_tooltip_text(_("Facebook - %s unread poke(s)") % str(pkcount))
        self.config.setPluginValue(self.name, 'pokescount', str(pkcount))
        return True

    def checkstatus(self):
        if self.status == '1' and self.enabled == True :
            if self.timechanged == True :
                if str(self.message['message']) != '':
                    if self.config.getPluginValue(self.name, 'time', '0') == '1':
                        self.addtime()
                        pm = self.config.getPluginValue(self.name, 'prefix', '') + self.pm + self.config.getPluginValue(self.name, 'suffix', '')
                        self.config.setPluginValue( self.name, 'statusprinted', pm )
                        self.msn.changePersonalMessage(pm)
                    else:
                        pm = self.config.getPluginValue(self.name, 'prefix', '') + self.config.getPluginValue(self.name, 'currentstatus', '') + self.config.getPluginValue(self.name, 'suffix', '')
                        self.config.setPluginValue( self.name, 'statusprinted', pm )
                        self.msn.changePersonalMessage(pm)

            else:
                self.message = (self.fb.users.getInfo([self.config.getPluginValue(self.name, 'uid', '')], ['status'])[0])['status']
                if str(self.message['message']) != '' :
                    if str(self.message['message']) != self.config.getPluginValue(self.name, 'currentstatus', ''):
                        self.getstatus()
                        self.config.setPluginValue( self.name, 'commentscounted', '' )
                    else:
                        self.msn.changePersonalMessage(self.config.getPluginValue(self.name, 'statusprinted', ''))
                        ##Personal Message sucessfully set'
                    if self.config.getPluginValue(self.name, 'time', '0') == '1':
                        self.addtime()
                        pm = self.config.getPluginValue(self.name, 'prefix', '') + self.pm + self.config.getPluginValue(self.name, 'suffix', '')
                        if pm != self.config.getPluginValue(self.name, 'statusprinted', ''):
                            self.config.setPluginValue( self.name, 'statusprinted', pm )
                            self.msn.changePersonalMessage(pm)
                else:
                    self.doichangestatus = False
                    self.config.setPluginValue( self.name, 'statusprinted', '' )
                    self.config.setPluginValue( self.name, 'currentstatus', '' )
                    self.msn.changePersonalMessage('')
                    try:
                        self.config.setPluginValue( self.name, 'commentscounted', '' )
                        self.fbcomments.destroy()
                        self.commentsactive = False
                    except:
                        ''
                self.doichangestatus = True
                return True

            self.timechanged = False
        else:
            return False

    def addtime(self):
        if self.config.getPluginValue( self.name, 'format', '' ) == '':
            from datetime import datetime
            status = datetime.fromtimestamp(float(self.message['time']))
            now = datetime.now()
            delta = now - status
            if delta.days != 0:
                if delta.days == 1:
                    statustime = _("Yesterday (%s)") % str(time.strftime("%X", time.localtime(self.message['time'])))
                else:
                    statustime = _("%(n)s days ago (%(t)s)") % {'n': str(delta.days), 't': time.strftime("%X", time.localtime(self.message['time']))}
            else:
                if delta.seconds >= 3599:
                        if delta.seconds/3600 == 1:
                            statustime = _("An hour ago")
                        else:
                            statustime = _("%s hours ago") % str(delta.seconds/3600)
                else:
                    if delta.seconds/60 <= 1 or delta.seconds/60 ==1 :
                        statustime = _("One minute ago")
                    else:
                        statustime = _("%s minutes ago") % str(delta.seconds/60)
        else:
            timeseconds = time.localtime(self.message['time'])
            timeformat = self.config.getPluginValue( self.name, 'format', '' )
            statustime = time.strftime(timeformat, timeseconds)

        if self.config.getPluginValue( self.name, 'separator', '[Time]' ) == '[Time]':
            self.pm = self.message['message'] + ' [' + statustime + ']'
        elif self.config.getPluginValue( self.name, 'separator', '[Time]' ) == '(Time)':
            self.pm = self.message['message'] + ' (' + statustime + ')'
        elif self.config.getPluginValue( self.name, 'separator', '[Time]' ) == '-- Time':
            self.pm = self.message['message'] + ' -- ' + statustime
        else:
            self.pm = self.message['message'] + ' ' + statustime

    def getstatus(self):
        pm = self.message['message']
        self.config.setPluginValue( self.name, 'currentstatus', pm )
        self.config.setPluginValue( self.name, 'status_id', self.message['status_id'] )
        if self.config.getPluginValue(self.name, 'time', '0') == '1':
            self.addtime()
        else:
            self.pm = pm
        pm = self.config.getPluginValue(self.name, 'prefix', '') + self.pm + self.config.getPluginValue(self.name, 'suffix', '')
        self.config.setPluginValue( self.name, 'statusprinted', pm )
        self.msn.changePersonalMessage(pm)
        ##Status successfully updated from facebook'

    def changestatus(self, *args):
        if self.enabled and self.doichangestatus == True and self.status == '1':
            self.timeout.cancel()
            if str(args[2]) == '' and str(args[2]) != self.config.getPluginValue(self.name, 'statusprinted', ''):
                if self.config.getPluginValue(self.name, 'confirmation', '1') == '1':
                    md = gtk.MessageDialog(None,
                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                         gtk.BUTTONS_YES_NO, _("Are you sure you want to clear your facebook status ?"))
                    response = md.run()
                    if response == gtk.RESPONSE_YES:
                        self.fb.users.setStatus(status='', clear=True)
                        self.config.setPluginValue( self.name, 'statusprinted', '' )
                        try:
                            self.config.setPluginValue( self.name, 'commentscounted', '' )
                            self.fbcomments.destroy()
                            self.commentsactive = False
                        except:
                            ''
                        self.checkstatus()
                    else:
                        self.msn.changePersonalMessage(self.config.getPluginValue(self.name, 'statusprinted', ''))
                    md.destroy()
                else:
                    self.fb.users.setStatus(status='', clear=True)
                    self.config.setPluginValue( self.name, 'statusprinted', '' )
                    self.checkstatus()
            elif str(args[2]) != self.config.getPluginValue(self.name, 'statusprinted', ''):
                if self.config.getPluginValue(self.name, 'confirmation', '1') == '1':
                    question = _('Are you sure you want to set "%s" as your new facebook status ?') % str(args[2])
                    md = gtk.MessageDialog(None,
                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                         gtk.BUTTONS_YES_NO, question)
                    response = md.run()
                    if response == gtk.RESPONSE_YES:
                        self.fb.users.setStatus(status=str(args[2]), clear=False, status_includes_verb=True)
                        try:
                            self.config.setPluginValue( self.name, 'commentscounted', '' )
                            self.fbcomments.destroy()
                            self.commentsactive = False
                        except:
                            ''                        
                        self.checkstatus()
                    else:
                        self.msn.changePersonalMessage(self.config.getPluginValue(self.name, 'statusprinted', ''))
                    md.destroy()
                else:
                    self.fb.users.setStatus(status=str(args[2]), clear=False, status_includes_verb=True)
                    self.checkstatus()
            self.timeout = ThreadTimer(int(self.config.getPluginValue(self.name, 'checktime','30')), self.checkstatus)
            self.timeout.start()


    def setavatar(self):
        profilepicurl = (self.fb.users.getInfo([self.config.getPluginValue(self.name, 'uid', '')], ['pic'])[0])['pic']
        if profilepicurl != self.config.getPluginValue(self.name, 'avatarurl', '') and profilepicurl != '' :
            self.config.setPluginValue( self.name, 'avatarurl', profilepicurl )
            urllib.urlretrieve(profilepicurl, self.dest_filename+'profilepic.jpg')
            ##Avatar successfully updated from facebook'
            ##Same avatar than the one saved before'
        self.controller.changeAvatar(self.dest_filename+'profilepic.jpg')
        ##Avatar sucessfully set'

class BaseImageButton:
    def __init__(self, icon, string=None):
        self.icon = icon
        self.image = gtk.Image()
        hbox = gtk.HBox()
        self.setIcon(icon)
        hbox.pack_start(self.image, True, True, 3)

        if string:
            self.label = gtk.Label(string)
            hbox.pack_start(self.label, False, False, 3)

        self.add(hbox)

    def setText(self, string):
        self.label.set_text(string)

    def getText(self):
        return self.label.get_text()

    def setIcon(self, icon):
        if type(icon) == gtk.gdk.PixbufAnimation:
            self.image.set_from_pixbuf(self.scaleImage(icon.get_static_image()))
        elif type(icon) == gtk.gdk.Pixbuf:
            self.image.set_from_pixbuf(self.scaleImage(icon))
        else:
            self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE ,gtk.ICON_SIZE_SMALL_TOOLBAR)

    def getIcon(self):
        return self.icon

    def scaleImage(self, image):
        h,w = image.get_height(), image.get_width()
        width_max, height_max = 18, 16
        width=float(image.get_width())
        height=float(image.get_height())
        if (width/width_max) > (height/height_max):
            height=int((height/width)*width_max)
            width=width_max
        else:
            width=int((width/height)*height_max)
            height=height_max

        image = image.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        gc.collect() # Tell Python to clean up the memory
        return image

class ImageButton(gtk.Button, BaseImageButton):
    def __init__(self, icon, string=None):
        gtk.Button.__init__(self)
        BaseImageButton.__init__(self, icon, string)

class SimpleThread(Thread):
    def __init__(self, function):
        Thread.__init__(self)
        self.function = function
        self.finished = Event()
        self.event = Event()
    def run(self):
        self.function()
    def cancel(self):
        self.finished.set()
        self.event.set()
  
class ThreadTimer(Thread):
    def __init__(self, interval, function):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.finished = Event()
        self.event = Event()
 
    def run(self):
        while not self.finished.is_set():
            self.event.wait(self.interval)
            if not self.finished.is_set() and not self.event.is_set():
                self.function()
 
    def cancel(self):
        self.finished.set()
        self.event.set()
