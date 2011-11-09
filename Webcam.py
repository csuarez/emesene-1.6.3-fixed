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

# TODO: handle "cancel webcam" p2p messages
#       port to farsight and stop the pain

import os
import time
import gtk
import gobject

import emesenelib.common
import desktop

HAVE_MIMIC = 1
try:
    import libmimic
except:
    print "Libmimic not found, webcam not available"
    print "Try to compile it with 'python setup.py build_ext -i' (python-dev package required)"
    HAVE_MIMIC = 0

HAVE_WEBCAM = 1
try:
    import WebcamDevice
except Exception, e:
    HAVE_WEBCAM = 0
    print "Can't initialize webcam device, sending disabled!"
    print "Reason:", str(e)

class Webcam:
    ''' this class represents a webcam session'''
    
    def __init__(self, p2p, conversation, session, sender, ourwebcam, controller):
        '''Constructor'''
        if not HAVE_WEBCAM:
            self.NO_WEBCAM = True
            return
        self.NO_WEBCAM = False
        self.p2p = p2p
        self.conversation = conversation
        self.session = int(session)
        self.sender = sender
        self.ourwebcam = ourwebcam
        self.controller=controller
        
        self.signals = []
        sap = self.signals.append
        sap(self.p2p.connect('webcam-frame-received', self.on_webcam_frame))
        sap(self.p2p.connect('webcam-failed', self.on_webcam_failed))
        sap(self.p2p.connect('webcam-ack', self.on_accept))
        
        self.decoder = libmimic.new_decoder()
        self.encoder = libmimic.new_encoder(1) # 1 = hi-res, 0 = low res
        
        self.init = False
        self.webcam = None
        self.errors = 0
        self.image = None
        self.win = None
        self.win_send = None
        self.daarea = None
        
    def prepare_window(self):
        if self.win is not None:
            return
        self.image = gtk.Image()
        self.win = gtk.Window()
        self.win.set_double_buffered(False)
        self.win.set_app_paintable(True)
        self.win.set_opacity(1)
        #self.win.set_resizable(False)
        self.win.set_title(_("%s\'s webcam") % self.sender);
        self.win.add(self.image)
        self.win.show_all()
        self.win.resize(320, 240)
        self.signals.append(self.win.connect('delete-event', self.on_close))
        
    def prepare_send_window(self):
        if self.win_send is not None:
            return
        self.daarea = gtk.DrawingArea()
        self.daarea.set_colormap(gtk.gdk.colormap_get_system())
        self.win_send = gtk.Window()
        self.win_send.set_opacity(1)
        self.win_send.set_double_buffered(False)
        self.win_send.set_app_paintable(True)
        #self.win_send.set_resizable(False)
        self.win_send.set_title(_("Your webcam"));
        self.win_send.add(self.daarea)
        self.win_send.show_all()
        self.win_send.resize(320, 240)
        self.signals.append(self.win_send.connect('delete-event', self.on_close))
        
    def on_close(self, *args):
        self.conversation.appendOutputText(None, _('You have canceled the webcam session'), 'information')
        self.p2p.emit('webcam-canceled', self.session)
        if self.webcam is not None:
            self.webcam.stop()
            
    def on_webcam_failed(self, p2p, session, reason):
        if int(session) != self.session:
            return
            
        self.conversation.appendOutputText(None, _('Webcam canceled'), 'error')
        if self.webcam is not None:
            self.webcam.stop()
            self.webcam = None
    
    def on_webcam_frame(self, p2p, session, sender, frame):
        if int(session) != self.session:
            return
        if self.win is None:
            return
        try:
            width, height, data = libmimic.decode(self.decoder, frame)
            if self.errors > 0:
                self.errors = 0
            #print "self.errors: %d\n" % self.errors
        except:
            print "Decode error"
            self.errors += 1
            print "self.errors: %d\n" % self.errors
            if self.errors > 10:
                print "Too many errors, closing webcam"
                self.on_close()
            return
            
        if not self.init:
            print "Got first frame: %dx%d" % (width, height)
            self.win.set_size_request(width, height)
            self.win.show_all()
            self.init = True
        
        self.image.set_from_pixbuf(gtk.gdk.pixbuf_new_from_data(data,gtk.gdk.COLORSPACE_RGB,False,8,width,height,width*3))
        if self.win is not None:
            self.win.queue_draw()
            self.image.queue_draw()
    
    def decline(self , session):
        if int(session) != self.session:
            return
        self.p2p.emit('webcam-canceled',self.session)

    def accept(self, session):
        if int(session) != self.session:
            return
        
        self.prepare_window()
        self.p2p.emit('webcam-accepted', self.session, self.sender)
        
    def on_handoff(self, element, buffer, pad):
        try:
            frame, width, height = libmimic.encode(self.encoder, buffer.data)
            self.p2p.emit('webcam-frame-ready', self.session, frame, width, height)
        except Exception, e:
            print "Encode error", e
            print "Exception: ", type(e)
        return True

    def on_accept(self, p2puser, session):
        if int(session) != self.session:
            return
        
        if not HAVE_WEBCAM:
            self.conversation.appendOutputText(None, _('Your webcam is not supported, or you don\'t have one'), 'error')
            return
        self.prepare_send_window()
        self.webcam = WebcamDevice.WebcamDevice(self.on_handoff, self.daarea.window.xid, self.controller)
    


