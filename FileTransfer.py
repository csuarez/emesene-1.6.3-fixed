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
import time
import gtk
import gobject

import emesenelib.common
import desktop

class FileTransfer:
    ''' this class represents one filetransfer'''

    def __init__(self, controller, p2p, conversation, session, context, sender, path):
        '''Constructor
        The sender parameter accepts the special value "Me", which is not
        a valid mail, and is used for sent files'''

        #constants
        #self.state should always be one of those states
        self.WAITING = 0
        self.TRANSFERING = 1
        self.RECEIVED = 2
        self.FAILED = 3

        self.controller = controller
        self.p2p = p2p
        self.conversation = conversation
        self.session = int(session)
        self.context = context
        self.sender = sender

        self.receivedBytes = 0
        self.state = self.WAITING

        self.timeAccepted = None
        
        self.previewImage = None
        if context.preview != '':
            try:
                loader = gtk.gdk.PixbufLoader()
                loader.write(context.preview)
                loader.close()

                self.previewImage = loader.get_pixbuf()
                del loader
            except gobject.GError:
                del loader

        self.localPath = None
        self.dirPath = None
        
        if path is not None:
            self.localPath = path
            self.dirPath = os.path.split(path)[0]
        
        if sender == 'Me':
            self.conversation.appendOutputText(None, \
                _('Sending %s') % self.context.filename, 'information')
        else:
            args = {'mail': self.p2p.mail, 'file': self.context.filename}
            self.conversation.appendOutputText(None, \
                _('%(mail)s is sending you %(file)s') % args, \
                'information')

        self.signals = []
        sap = self.signals.append
        sap(self.p2p.connect('transfer-progress', self.onFtProgress))
        sap(self.p2p.connect('transfer-failed', self.onFtFailed))
        sap(self.p2p.connect('file-transfer-complete', self.onFtReceived))
        if sender == 'Me':
            sap(self.p2p.connect('file-transfer-accepted', self.onFtAccepted))

    def disconnect(self):
        for identifier in self.signals:
            self.p2p.disconnect(identifier)
        self.signals = []

    def getPreviewImage(self):
        return self.previewImage

    def getBytes(self):
        '''returns a tuple with received and total bytes'''
        return int(self.receivedBytes), int(self.context.file_size)

    def accept(self):
        '''accept this transfer'''

        self.conversation.appendOutputText(None, \
            _('You have accepted %s') % self.context.filename, \
            'information')

        self.p2p.emit('file-transfer-accepted', self.session, self.context,
            self.sender)
        self.timeAccepted = time.time()

        self.state = self.TRANSFERING
        self.ui.stateChanged()

    def cancel(self):
        '''cancel this transfer'''

        self.conversation.appendOutputText(None,
            _('You have canceled the transfer of %s') % self.context.filename,
            'information')

        self.p2p.emit('file-transfer-canceled', self.session, self.context,
            self.sender)

        self.state = self.FAILED
        self.ui.stateChanged()
        self.remove()

    def getElapsedTime(self):
        '''return the time elapsed since this transfer was accepted'''
        if not self.timeAccepted:
            return 0
        else:
            return int(time.time()) - int(self.timeAccepted)

    def getAverageSpeed(self):
        '''get average file transfer speed (bytes per second)'''
        time = self.getElapsedTime()
        if time == 0: # prevent division by zero
            return 0
        else:
            return self.receivedBytes / time

    def getEstimatedTimeLeft(self):
        '''get estimated time left to complete the transfer'''
        speed = self.getAverageSpeed()
        if speed == 0:
            return 0
        else:
            return (self.context.file_size - self.receivedBytes) / speed

    def remove(self):
        '''remove this transfer'''
        self.conversation.transfers.remove(self)
        self.disconnect()

    def onFtAccepted(self, p2p, session, context, sender):
        if session != self.session: return

        self.conversation.appendOutputText(None, \
            _('Starting transfer of %s') % self.context.filename, \
            'information')

        self.timeAccepted = time.time()

        self.state = self.TRANSFERING
        self.ui.stateChanged()

    def onFtProgress(self, switchboard, session, bytes):
        if session != self.session: return

        self.receivedBytes = int(bytes)
        self.ui.updateProgress()

    def onFtFailed(self, switchboard, session, reason):
        if session != self.session: return

        output = _('Transfer of %s failed.') % self.context.filename + ' '

        if reason == 'corrupt':
            output += _('Some parts of the file are missing')
        elif reason == 'cancelled':
            output += _('Interrupted by user')
        elif reason == 'error':
            output += _('Transfer error')
        self.conversation.appendOutputText(None, output, 'error')

        self.state = self.FAILED
        self.ui.stateChanged()

    def onFtReceived(self, p2p, session, context, src, sender):
        '''called when filetransfer is finished'''
        if session != self.session: return

        if sender == 'Me':
            self.conversation.appendOutputText(None, \
                _('%s sent successfully') % context.filename, 'information')
        else:
            self.conversation.appendOutputText(None, \
                _('%s received successfully.') % context.filename, \
                'information')
        self.conversation.doMessageWaiting(sender)

        self.receivedBytes = context.file_size
        self.state = self.RECEIVED
        self.ui.stateChanged()

        if sender == 'Me' or src.closed:
            self.disconnect()
            return

        # get file dir
        config = self.controller.config
        receivedFilesDir = os.path.expanduser(config.user['receivedFilesDir'])

        # if directory is invalid, save to home directory
        if not os.path.exists(receivedFilesDir):
            print receivedFilesDir + ' does not exist. ' \
                'Saving files to home directory.'
            receivedFilesDir = os.path.expanduser('~/')

        # separated folders between contacts
        if config.user['receivedFilesSortedByUser']:
            receivedFilesDirSub = os.path.join(receivedFilesDir, p2p.mail)

            if os.path.exists(receivedFilesDirSub):
                receivedFilesDir = receivedFilesDirSub
            else:
                os.mkdir(receivedFilesDirSub)
                # ugly, but "if os.mkdir(..)" doesn't work :S
                if os.path.exists(receivedFilesDirSub):
                    receivedFilesDir = receivedFilesDirSub
                    # if we can't create the dir, we put the file directly
                    # in received files dir

        self.dirPath = receivedFilesDir
        name = os.path.join(receivedFilesDir, self.getFilename())

        num = 0
        numstr = ''

        while os.path.exists(name + numstr):
            num += 1
            numstr = '.' + str(num)

        self.localPath = name + numstr

        # we don't copy because the permissions may be too restrictive
        # and not match the user preferred umask blah blah
        dest = open(self.localPath, 'wb')
        src.seek(0)
        buffer = src.read(32 * 1024)
        while buffer:
            dest.write(buffer)
            buffer = src.read(32 * 1024)
        dest.close()
        src.close()

        self.disconnect()

    def open(self):
        '''open received file'''
        if self.localPath:
            try:
                desktop.open(self.localPath)
            except OSError:
                pass
                
    def opendir(self):
        '''open directory'''
        desktop.open(self.dirPath)

    def getFilename(self):
        return self.context.filename

    def setBytesReceived(self, bytes):
        self.receivedBytes = bytes

    def getFraction(self):
        '''return the progress of this transfer as a float from 0 to 1'''
        if self.context.file_size:
            return float(self.receivedBytes) / float(self.context.file_size)
        else:
            return 1
