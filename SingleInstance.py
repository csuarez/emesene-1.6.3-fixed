# -*- coding: utf-8 -*-

#   This file is a plugin for emesene.
#
#    Dbus Emesene Plugin is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Dbus Emesene Plugin is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys, os, errno, tempfile

HAVE_DBUS = False

BUS_NAME = 'org.emesene.dbus'
OBJECT_PATH = '/org/emesene/dbus'

if os.name == "posix":
    try:
        import dbus, dbus.service
        dbusError = ''
        if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
            import dbus.glib
        if getattr(dbus, 'version', (0,0,0)) >= (0,80,0):
            import _dbus_bindings as dbus_bindings
            from dbus.mainloop.glib import DBusGMainLoop
            DBusGMainLoop(set_as_default=True)
            NEW_DBUS = True
        else:
            import dbus.mainloop.glib
            import dbus.dbus_bindings as dbus_bindings  
            NEW_DBUS = False
        HAVE_DBUS = True
    except Exception, e:
        HAVE_DBUS = False
        dbusError = e

class SingleInstance:
    def __init__(self):
        uid = ''
        if os.name == 'posix':
            uid = str(os.geteuid())
        self.lockfile = os.path.normpath(tempfile.gettempdir() + '/emesene1-' + uid + '.lock')

    def is_running(self):
        if os.name == 'posix':
            import fcntl
            self.fp = open(self.lockfile, 'w')
            try:
                fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return True
            return False
        else:
            try:
                # if file already exists, we try to remove (in case previous execution was interrupted)
                if(os.path.exists(self.lockfile)):
                    os.unlink(self.lockfile)
                self.fd =  os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
            except OSError, e:
                if e.errno == 13:
                    return True
                print e.errno
                return False
            return False
                
    def show(self):
        if HAVE_DBUS == False:
            return
        try:
            self.bus = dbus.SessionBus()
            self.dbus = self.bus.get_object(BUS_NAME, OBJECT_PATH)
            self.dbus.show()
    	except Exception:
            pass

    def __del__(self):
        if os.name == 'nt':
            if hasattr(self, 'fd'):
                os.close(self.fd)
                os.unlink(self.lockfile)


