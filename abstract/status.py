# -*- coding: utf-8 -*-
'''a module to handle abstract status for different IM clients'''

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

#import gettext
#_ = gettext.gettext

OFFLINE = 0
ONLINE = 1
BUSY = 2
AWAY = 3
IDLE = 4
INVISIBLE = 5
LUNCH = 6
TELEPHONE = 7
BE_RIGHT_BACK = 8

ORDERED = [ONLINE, BUSY, AWAY, BE_RIGHT_BACK, IDLE, LUNCH, TELEPHONE,
    INVISIBLE, OFFLINE]

STATUS = {OFFLINE : _('Offline'),
    ONLINE : _('Online'),
    BUSY : _('Busy'),
    AWAY : _('Away'),
    IDLE : _('Idle'),
    INVISIBLE : _('Invisible'),
    LUNCH : _('Lunch'),
    TELEPHONE : _('On the phone'),
    BE_RIGHT_BACK : _('Be right back')}

REVERSE = dict([(y, x) for x, y in STATUS.items()])

def is_valid(status):
    '''return True if status is a valid status value'''

    return status in STATUS
        
