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

DIR_SEP = os.sep

if hasattr(sys, "frozen"):
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.abspath(os.path.dirname(__file__))

if (os.name != 'nt'): 
    HOME_DIR = os.path.expanduser('~')
else:
    HOME_DIR = os.path.expanduser("~").decode(sys.getfilesystemencoding())
CONF_DIR_NAME = '.config' + DIR_SEP + 'emesene1.0'
CONFIG_DIR = HOME_DIR + DIR_SEP + CONF_DIR_NAME
    
THEME_HOME_PATH = CONFIG_DIR + DIR_SEP + 'themes'
THEME_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + 'themes'
DEFAULT_THEME_PATH = THEME_SYSTEM_WIDE_PATH + DIR_SEP + 'default' + DIR_SEP

PLUGINS_HOME = 'pluginsEmesene'
PLUGINS_SYSTEM_WIDE = 'plugins_base'
PLUGIN_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + PLUGINS_SYSTEM_WIDE
PLUGIN_HOME_PATH = CONFIG_DIR + DIR_SEP + PLUGINS_HOME

SMILIES_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + 'smilies'
SMILIES_HOME_PATH = CONFIG_DIR + DIR_SEP + 'smilies'
DEFAULT_SMILIES_PATH = SMILIES_SYSTEM_WIDE_PATH + DIR_SEP + 'default' + DIR_SEP

CONVTHEMES_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + 'conversation_themes'
CONVTHEMES_HOME_PATH = CONFIG_DIR + DIR_SEP + 'conversation_themes'
DEFAULT_CONVTHEMES_PATH = CONVTHEMES_SYSTEM_WIDE_PATH + DIR_SEP + 'default' + DIR_SEP

LANG_PATH = APP_PATH + DIR_SEP + 'po'
SOUNDS_PATH = APP_PATH + DIR_SEP + 'sound_themes'

del os, sys
