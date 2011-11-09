# -*- coding: utf-8 -*-

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
import shutil
import gobject

import paths
import emesenelib.common

import random
id = 'emesene'+str(random.random()) #used for dp roaming

DEFAULT_GLOBAL_CONFIG = {
    'rememberMe': True,
    'rememberMyPassword': False,
    'debug': False,
    'binary': False,
    'httpMethod': False,
    'useProxy': False,
    'proxyHost': 'http://127.0.0.1',
    'proxyPort': 80,
    'proxyUsername' : '',
    'proxyPassword' : '',
    'mainWindowGeometry': '440x260+0+0',
    'autoLogin': False,
    'lastLoggedAccount': '',
    'rgbaColormap' : False,
    'disableTrayIcon' : False,
    'overrideDesktop' : '',
    'overrideMail' : '',
    'startup' : 'default',
    'dontShowAvatarInLoginWindow' : 0,
    'Id' : id,
}


DEFAULT_USER_CONFIG = {
    'theme': 'default',
    'smilieTheme': 'default',
    'conversationLayout' : 'default',
    'smallIcons': False,
    'showByNick': True,
    'showOffline': False,
    'showEmptyGroups': False,
    'orderByStatus': False,
    'collapsedGroups': '',
    'autoReply': False,
    'autoReplyMessage': _('I\'m not here (this is an autoreply)'),
    'rememberMyPassword': False,
    'fontFace': 'Sans',
    'fontColor': '#000000',
    'fontSize': 10,
    'fontUnderline' : False,
    'fontBold' : False,
    'fontItalic' : False,
    'fontStrike' : False,
    'showTimestamp': False, # XXX: check if this works
    'convWindowGeometry': '480x450+0+0',
    'convWindowWidth': '450',
    'convWindowHeight': '480',
    'convInputHeight' : 140,
    'convListWidth' : 130,
    'convMaximized' : False,
    'saveLogsAutomatically' : False,
    'activePlugins': 'Plus', # CSV of plugin names
    'emoticonDir': '',
    'avatarDir' : '',
    'avatarPath' : '',
    'parseSmilies' : True,
    'typingColor': '#339999',
    'messageWaitingColor': '#ef2929',
    'personalMessageColor': '#AAAAAA',
    'useFriendsUnifiedFormat' : False,
    'friendsUnifiedFont' : 'Sans',
    'friendsUnifiedColor' : '#000000',
    'windows' : False,
    'webcamDevice' : 'video0',
    'webcamContrast' : 1.0,
    'webcamSaturation' : 1.0,
    'webcamHue' : 0.0,
    'webcamBrightness' : 0.0,
    # almost every setting in this block has signals
    'showUserPanel' : True,
    'showSearchEntry' : True,
    'showStatusCombo' : True,
    #'statusComboOnTop' : False,
    'statusComboPos' : 0,
    'showMenubar' : True,
    'showMenu' : True,
    'showHeader' : True,
    'showToolbar' : True,
    'showAvatars' : True,
    'showStatusBar' : True,
    'showAvatarMine' : True, # signal not needed
    'showAvatarOther' : True, # signal not needed
    'showTabCloseButton' : True, # TODO: w/o signal
    'avatarsInUserList' : True, # TODO: w/o signal
    'avatarsInTaskbar' : False,
    'hideNewWindow' : False,
    'showMailTyping' : False,
    'dontDisturbOnBusy' : True,
    'showSendButton' : False,
    'showCountContact' : True,
    'showTabImageStatus' : False,
    'mediaEnabled' : False,
    'blinkTrayIcon' : True,
    'statusbarHighLight' : True,
    'sortNickGroupByContact' : 0, # 0 = sort by nickname | 1 = sort by mail
    'sortNickGroupByStatusPriority' : 0, # sort contact in group by status

    'statusTransformation' : 'corner|alpha|gray', # valid values are corner, pixelate, alpha, gray(seperated by | )

    'useAliasIfAvailable' : True, # show alias everywhere if an alias is set
    'sendTyping' : True, # send the is typing notification to other clients
    'userListAvatarSize': 32,

    'receivedFilesSortedByUser' : False,
    'receivedFilesDir' : '~/',
    'disableEsc' : False, # disable the esc key to close conversations
    'disableFormat': False,
    'convHeaderTemplate': "['<span foreground=\"%s\">%s</span>$\\n$<span "+ \
                     "foreground=\"%s\">%s</span>','color;pm;color;email']",
    'autoAcceptTransfer': False,
    'sendKeepalive': False,
    'canResizeEmoticons' : False,
    'avatarsOnRight' : True,
    'receiveP4context' : False,
    'preventClosingTime' : False,
    'showLastMessageReceivedAt' : True,
    'enableSounds' : True,
    'soundsplayOnline' : True,
    'soundsplayOffline' : True,
    'soundsmuteSound' : False,
    'soundsplayMessage' : True,
    'soundsplayNudge' : True,
    'soundsplayTransfer' : True,
    'soundsplayInactive' : True,
    'soundsplaySend' : False,
    'soundsplayError' : False,
    'soundsdisableBusy' : False,
    'soundstheme' : 'default',
    'soundsbeep' : False,
    'toolFontType' : True,
    'toolFontColor' : True,
    'toolFontStyle' : True,
    'toolSmilies' : True,
    'toolNudge' : True,
    'toolInvite' : True,
    'toolSendFile' : True,
    'toolWebcam' : True,
    'toolClear' : True,
    'avatarDate' : '1800-01-01T00:00:00',
}

class Config(gobject.GObject):
    '''This class contains all the stuff relative to the configuration of
    emesene. You can get or set configuration values and will be saved to
    a file for persistence'''

    __gsignals__ = {
        # value, oldvalue
        'change' : (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_DETAILED, \
          gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }


    # -- GLOBAL CONFIG -- #
    def __init__(self):
        '''Constructor : this will create needed files for global configuration'''
        gobject.GObject.__init__(self)

        self.currentUser = ''
        self.glob = {}
        self.user = {}

        # This dict is a bit different from the two others
        # It's not a key : value dict but a plugin_name : [ key : value ] dict
        # Also it's a plain old dict, don't use it directly
        self.pluginsConfigDict = {}

        if os.name != 'nt' or hasattr(sys, "frozen"):
            # home dirs don't work outside py2exe (!)
            _mkdir('', paths.HOME_DIR, '.config')
            _mkdir('Config dir', paths.CONFIG_DIR)
            _mkdir('Theme dir in config', paths.THEME_HOME_PATH)
            _mkdir('Smilies dir in config', paths.SMILIES_HOME_PATH)
            _mkdir('Convthemes dir in config', paths.CONVTHEMES_HOME_PATH)
            _mkdir('Theme dir in config', paths.THEME_HOME_PATH)
            _mkdir('Plugins dir in config', paths.PLUGIN_HOME_PATH)
            open(os.path.join(paths.PLUGIN_HOME_PATH, '__init__.py'), 'w')\
                .write("__path__.append('%s')" % paths.PLUGIN_SYSTEM_WIDE_PATH)

        if _mkfile('Config file', paths.CONFIG_DIR, 'config'):
            self.glob = ConfigDict(self, self.writeGlobalConfig, \
                DEFAULT_GLOBAL_CONFIG)
            self.writeGlobalConfig()

        self.readGlobalConfig()

    def readGlobalConfig(self):
        '''read the config file and create a dictionarie with key and value
        of all the key=value\n in the config file'''

        globalConfigDict = DEFAULT_GLOBAL_CONFIG.copy()
        conf = None
        try:
            conf = open(paths.CONFIG_DIR + '/config', 'r')
            string = conf.read()

            for i in string.splitlines():
                if i != '':
                    try:
                        delim = i.find('=')
                        key = i[:delim]
                        value = i[delim+1:]
                        if key in DEFAULT_GLOBAL_CONFIG:
                            globalConfigDict[ key ] = value
                        else:
                            emesenelib.common.debug(key + ' is not a valid config key, ignored')
                    except Exception, e:
                        emesenelib.common.debug(key + ' config value is incorrect')

            conf.close()
        except:
            if conf:
                conf.close()

        self.glob = ConfigDict(self, self.writeGlobalConfig, DEFAULT_GLOBAL_CONFIG, globalConfigDict)

    def writeGlobalConfig(self):
        '''write the config to the file, overwrite current config file'''

        try:
            conf = open(paths.CONFIG_DIR + '/config', 'w')

            for k, v in self.glob:
                if type(v) == bool:
                    conf.write(k + '=' + str(int(v)) + '\n')
                else:
                    conf.write(k + '=' + str(v) + '\n')

            conf.close()
        except Exception, e:
            emesenelib.common.debug('exception writing config:\n')
            emesenelib.common.debug(e)

    # -- USER CONFIG -- #
    def setCurrentUser(self, email):
        ''' Create and/or read needed file for user config
        /!\ This function MUST be called before any set/getUserConfig'''

        self.currentUser = email.replace('@', '_').replace('.', '_')
        self.glob['lastLoggedAccount'] = email


        if email != '':

            _mkdir('User config dir', paths.CONFIG_DIR, self.currentUser)

            if _mkfile('Config file created: ', paths.CONFIG_DIR, \
               self.currentUser, 'config'):
                self.user = ConfigDict(self, self.writeUserConfig, \
                    DEFAULT_USER_CONFIG)
                self.writeUserConfig()

            _mkdir('', paths.CONFIG_DIR, self.currentUser, 'logs')
            _mkdir('', paths.CONFIG_DIR, self.currentUser, 'cache')
            _mkdir('', paths.CONFIG_DIR, self.currentUser, 'avatars')
            _mkdir('', paths.CONFIG_DIR, self.currentUser, 'custom_emoticons')
            self.readUserConfig()

        else:
            self.user = {}

    def getCurrentUser(self):
        return self.currentUser

    def readUserConfig(self):
        '''read the config file and create a dictionarie with key and value
        of all the key=value\n in the config file'''

        userConfigDict = DEFAULT_USER_CONFIG.copy()
        conf = None
        try:
            conf = open(paths.CONFIG_DIR + '/' + self.currentUser + '/config', 'r')
            string = conf.read()

            for i in string.splitlines():
                if i != '':
                    try:
                        delim = i.find('=')
                        key = i[:delim]
                        value = i[delim+1:]
                        if key in DEFAULT_USER_CONFIG:
                            userConfigDict[ key ] = value
                        else:
                            emesenelib.common.debug(key + ' is not a valid config key, ignored')
                    except Exception, e:
                        emesenelib.common.debug(key + ' config value is incorrect')

            conf.close()
        except:
            if conf:
                conf.close()

        self.user = ConfigDict(self, self.writeUserConfig, DEFAULT_USER_CONFIG, userConfigDict)

    def writeUserConfig(self):
        '''write the config to the file, overwrite current config file'''

        try:
            conf = open(paths.CONFIG_DIR + '/' + self.currentUser + '/config', 'w')

            for k, v in self.user:
                if type(v) == bool:
                    conf.write(k + '=' + str(int(v)) + '\n')
                else:
                    conf.write(k + '=' + str(v) + '\n')

            conf.close()
        except Exception, e:
            emesenelib.common.debug('exception writing config:\n')
            emesenelib.common.debug(e)

    # --- PLUGINS CONFIG --- work in progress - #
    def readPluginConfig(self, pluginName):
        '''read the plugin config file and create a dict with key and value
        of all the key=value\n in the config file'''

        self.pluginsConfigDict[pluginName] = {}
        conf = None
        try:
            conf = open(self.getUserConfigPath() + os.sep + pluginName + '.conf', 'r')
            string = conf.read()

            for i in string.splitlines():
                if i != '':
                    try:
                        delim = i.find('=')
                        key = i[:delim]
                        value = i[delim+1:]
                        self.pluginsConfigDict[pluginName][key] = value
                    except Exception, e:
                        emesenelib.common.debug(key + ' config value is incorrect')

            conf.close()
        except:
            if conf:
                conf.close()

    def writePluginConfig(self, pluginName):
        '''write the config to the file, overwrite current plugin config file'''

        try:
            conf = open(self.getUserConfigPath() + os.sep + pluginName + '.conf', 'w')

            for k, v in self.pluginsConfigDict[pluginName].iteritems(): # TODO
                conf.write(k + '=' + str(v) + '\n')

            conf.close()
        except Exception, e:
            emesenelib.common.debug('exception writing config:\n')
            emesenelib.common.debug(e)

    def setPluginValue(self, pluginName, key, value):
        self.pluginsConfigDict[pluginName][key] = str(value)
        self.writePluginConfig(pluginName) # TODO: config transactions?

    def getPluginValue(self, pluginName, key, default):
        if pluginName in self.pluginsConfigDict:
            if key in self.pluginsConfigDict[pluginName]:
                return self.pluginsConfigDict[pluginName][key]

        return default

    # --- OTHER STUFF --- #
    def _explorePath( self, path ):
        result = []
        for root, dirs, files in os.walk(path, True):
            if root != path: continue
            for dir in dirs:
                if not dir.startswith('.') and dir not in result:
                    result.append(dir)
            # stops walking the tree
            dirs = []
        return result

    def getThemes(self):
        '''this method is here because i dont know where to put it,
        it return a list of dirs in the theme directory'''

        return self._explorePath(paths.THEME_HOME_PATH) + \
               self._explorePath(paths.THEME_SYSTEM_WIDE_PATH)

    def getSmilieThemes(self):
        '''the same with smilie themes'''

        return self._explorePath(paths.SMILIES_HOME_PATH) + \
               self._explorePath(paths.SMILIES_SYSTEM_WIDE_PATH)

    def getLogPath(self):
        logPath = self.user['logPath']
        if logPath != '':
            return logPath
        else:
            return paths.CONFIG_DIR + os.sep + self.currentUser + os.sep + 'logs'

    def getCachePath(self):
        return paths.CONFIG_DIR + os.sep + self.currentUser + os.sep + 'cache'

    def getUserConfigPath(self):
        return paths.CONFIG_DIR + os.sep + self.currentUser

    def getAvatarsCachePath(self):
        return paths.CONFIG_DIR + os.sep + self.currentUser + os.sep + 'avatars'

    def getCustomEmoticonsPath(self):
        return paths.CONFIG_DIR + os.sep + self.currentUser + os.sep + 'custom_emoticons'

    def getConversationThemesPath(self):
        return paths.CONFIG_DIR + os.sep + 'conversation_themes'


class ConfigDict(dict):
    '''A dictionary that handles type conversion, fallbacks to default, config
    file writing, etc'''

    def __init__(self, config, writeFunc, defaults, store=None):
        self.config = config
        self.writeFunc = writeFunc
        self.defaults = defaults

        if store == None:
            store = defaults.copy()

        self.store = {}
        for key, value in store.iteritems():
            if type(value) == bool:
                self.store[key] = str(int(value))
            else:
                self.store[key] = str(value)

    def __repr__(self):
        return '<ConfigDict based on ' + repr(store) + '>'

    def getDefault(self, name):
        if name in self.defaults:
            return self.defaults[name]
        else:
            return ''

    def __getitem__(self, name):
        '''returns a item from self.store. if it is not available, return that
        item from defaults
        also does some type conversion and bool checks'''

        if name in self.store:
            newType = type(self.getDefault(name))
            if newType == bool:
                if str(self.store[name]).lower() in ('true', 'false'):
                    # workaround for some buggy configs..
                    boolValue = (str(self.store[name]).lower() == 'true')
                    self.store[name] = str(int(boolValue))
                    return boolValue
                else:
                    try:
                        # >>> int('0') == True
                        return bool(int(self.store[name]))
                    except ValueError:
                        return self.getDefault(name)
            else:
                try:
                    return newType(self.store[name])
                except ValueError:
                    return self.getDefault(name)
        else:
            emesenelib.common.debug('Config value was not found: ' + str(name))
            return self.getDefault(name)

    def __setitem__(self, name, value):
        '''sets a config key "name" to the string "value", emits
        callbacks and writes config'''

        if type(value) == bool:
            value = str(int(value))
        else:
            value = str(value)

        oldValue = None
        if name in self.store:
            oldValue = self.store[name]

        self.store[name] = value

        self.config.emit('change::' + name, value, oldValue)
        self.writeFunc() # TODO: config transactions?

    def __iter__(self):
        '''for key, value in configDict'''
        return self.store.iteritems()


def _mkbase(check, make, message, *components):
    '''base function for _mkdir and _mkfile'''
    path = os.path.join(*components)
    if not check(path):
        make(path)
        if message:
            emesenelib.common.debug(message + ' created: ' + path)
        return True
    return False

def _mkdir(message, *components):
    '''makes a directory and prints a message'''
    return _mkbase(os.path.isdir, os.mkdir, message, *components)

def _mkfile(message, *components):
    '''checks if the file exists and prints a message'''
    return _mkbase(os.path.isfile, lambda x: None, message, *components)
