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

#-------------------
# Pipeline Scheme  |
#-------------------
#                                                                 <----------LOCAL WEBCAM OUTPUT----------->
#
#                                                                   ---> Queue1 ---> Colorspace1 ---> Sink
#                                                                  |
#       Source ---> Scale ---> VideoBalance ---> Filter ---> Tee --
#                                                                  |
#                                                                   ---> Queue2 ---> Colorspace2 ---> Sink2
#                                                                  
#                                                                 <----------REMOTE WEBCAM OUTPUT---------->
import pygst
pygst.require("0.10")
import gst
import os

class WebcamDevice:
    def __init__(self, handoff_cb, xid, controller):
        self.handoff_cb = handoff_cb
        self.xid = xid
        #Let's Create the pipeline for Gstreamer
        self.pipeline = gst.Pipeline("my")

        #Start creation of every element composing the pipeline
        self.source = gst.element_factory_make("v4l2src")
        self.source.set_property('device',"/dev/"+controller.config.user['webcamDevice'])
        self.scale = gst.element_factory_make("videoscale")        

        self.colourBalance = gst.element_factory_make('videobalance')
        self.colourBalance.set_property('brightness', controller.config.user['webcamBrightness'])
        self.colourBalance.set_property('contrast', controller.config.user['webcamContrast'])
        self.colourBalance.set_property('hue', controller.config.user['webcamHue'])
        self.colourBalance.set_property('saturation', controller.config.user['webcamSaturation'])

        self.caps = gst.Caps("video/x-raw-yuv, width=320, height=240, bpp=24, depth=24, framerate=30/1")

        self.filter = gst.element_factory_make("capsfilter", "filter")
        self.filter.set_property("caps", self.caps)

        self.tee = gst.element_factory_make("tee")

        self.q1 = gst.element_factory_make("queue")

        self.q2 = gst.element_factory_make("queue")

        self.csp = gst.element_factory_make("ffmpegcolorspace")

        self.csp2 = gst.element_factory_make("ffmpegcolorspace")

        self.fake = gst.element_factory_make("fakesink")
        if self.handoff_cb is not None:
            self.fake.set_property("signal-handoffs", True)
            self.fake.connect('handoff', self.handoff_cb)

        self.sink = gst.element_factory_make("autovideosink")

        #Add the elements to the pipeline
        self.pipeline.add(self.source)
        self.pipeline.add(self.scale)
        self.pipeline.add(self.colourBalance)
        self.pipeline.add(self.filter)
        self.pipeline.add(self.tee)
        self.pipeline.add(self.q1)
        self.pipeline.add(self.q2)
        self.pipeline.add(self.csp)
        self.pipeline.add(self.csp2)
        self.pipeline.add(self.fake)
        self.pipeline.add(self.sink)

        #Source -> Scale -> VideoBalance -> Tee -> Queue1 -> Colorspace -> Sink
        #IF THIS LINE WORKS, LEAVE IT        
        gst.element_link_many(self.source,self.scale,self.filter,self.csp,self.colourBalance,self.tee,self.q1,self.sink)
        #IF DOESN'T WORK REVERT WITH THIS ONE
        #gst.element_link_many(self.source,self.scale,self.filter,self.colourBalance,self.tee,self.q1,self.csp,self.sink)

        #Starting from the previous Tee let's add
        # Queue2 -> Colorspace2 -> Sink2
        gst.element_link_many(self.tee,self.q2,self.csp2)
        self.csp2.link(self.fake, gst.caps_from_string("video/x-raw-rgb"))

        
        #Let's get the bus and configure it
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect("sync-message::element", self.onmessage)

        #Ok, let's start the stream
        self.pipeline.set_state(gst.STATE_PLAYING)

    def onmessage(self, bus, message):
        if message.structure is None:
            return
        if message.structure.get_name() == "prepare-xwindow-id":
            message.src.set_property('force-aspect-ratio', True)
            message.src.set_xwindow_id(self.xid)

    def stop(self):
        self.pipeline.set_state(gst.STATE_READY)
        self.pipeline.set_state(gst.STATE_NULL)

    def setBrightness(self, val):
        ## Sets the brightness of the video.
        self.colourBalance.set_property('brightness', val)
	
    def setContrast(self, val):
        ## Sets the contrast of the video.
        self.colourBalance.set_property('contrast', val)
	
    def setHue(self, val):
        ## Sets the hue of the video.
        self.colourBalance.set_property('hue', val)
	
    def setSaturation(self, val):
        ## Sets the saturation of the video.
        self.colourBalance.set_property('saturation', val)

def list_devices():
    for device in os.listdir('/dev/'):
        if device.startswith('video'):
            try:
                source = gst.element_factory_make("v4l2src")
            except:
                print "Could not create gst element factory for v4l2src (missing plugin?)"
                continue

            try:
                source = gst.element_factory_make("v4l2src")
                source.set_property('device',"/dev/" + device)
                if source.get_property("device_name") is not None:
                    yield (device, source.get_property("device_name"))
            except Exception, e:
                print "Could not add /dev/%s to list" % device
                print "Reason:", str(e)
