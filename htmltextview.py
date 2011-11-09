# -*- coding: utf-8 -*-

### Copyright (C) 2005 Gustavo J. A. M. Carneiro
###
### This library is free software; you can redistribute it and/or
### modify it under the terms of the GNU Lesser General Public
### License as published by the Free Software Foundation; either
### version 2.1 of the License, or (at your option) any later version.
###
### This library is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
### Lesser General Public License for more details.
###
### You should have received a copy of the GNU Lesser General Public
### License along with this library; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

'''
A gtk.TextView-based renderer for XHTML-IM, as described in:
  http://www.jabber.org/jeps/jep-0071.html
'''
import gobject
import pango
import gtk
import xml.sax, xml.sax.handler
import re
import warnings
import urllib
from cStringIO import StringIO
import operator
import desktop

import stock
import dialog

__all__ = ['HtmlTextView']

whitespace_rx = re.compile("\\s+")

if gtk.gdk.screen_height_mm():
    ## pixels = points * display_resolution
    display_resolution = 0.3514598*(gtk.gdk.screen_height() /
                        float(gtk.gdk.screen_height_mm()))
else:
    # inaccurate, but better than letting the universe implode
    display_resolution = 1


def _parse_css_color(color):
    '''_parse_css_color(css_color) -> gtk.gdk.Color'''
    if color.startswith("rgb(") and color.endswith(')'):
        r, g, b = [int(c)*257 for c in color[4:-1].split(',')]
        return gtk.gdk.Color(r, g, b)
    else: # there's some strange issue with colors starting with double #
        if color.startswith('##'): 
            color = '#0' + color.lstrip('#')
        return gtk.gdk.color_parse(color)


class HtmlHandler:

    def __init__(self, textview, startiter, canResize):
        self.textbuf = textview.get_buffer()
        self.textview = textview
        self.iter = startiter
        self.text = ''
        self.styles = [] # a gtk.TextTag or None, for each span level
        self.list_counters = [] # stack (top at head) of list
                                # counters, or None for unordered list
        self.canResize = canResize
        
    def _parse_style_color(self, tag, value):
        color = _parse_css_color(value)
        tag.set_property("foreground-gdk", color)

    def _parse_style_background_color(self, tag, value):
        color = _parse_css_color(value)
        tag.set_property("background-gdk", color)
        if gtk.gtk_version >= (2, 8):
            tag.set_property("paragraph-background-gdk", color)


    if gtk.gtk_version >= (2, 8, 5) or gobject.pygtk_version >= (2, 8, 1):

        def _get_current_attributes(self):
            attrs = self.textview.get_default_attributes()
            self.iter.backward_char()
            self.iter.get_attributes(attrs)
            self.iter.forward_char()
            return attrs

    else:

        ## Workaround http://bugzilla.gnome.org/show_bug.cgi?id=317455
        def _get_current_style_attr(self, propname, comb_oper=None):
            tags = [tag for tag in self.styles if tag is not None]
            tags.reverse()
            is_set_name = propname + "-set"
            value = None
            for tag in tags:
                if tag.get_property(is_set_name):
                    if value is None:
                        value = tag.get_property(propname)
                        if comb_oper is None:
                            return value
                    else:
                        value = comb_oper(value, tag.get_property(propname))
            return value

        class _FakeAttrs(object):
            __slots__ = ("font", "font_scale")

        def _get_current_attributes(self):
            attrs = self._FakeAttrs()
            attrs.font_scale = self._get_current_style_attr("scale",
                                                            operator.mul)
            if attrs.font_scale is None:
                attrs.font_scale = 1.0
            attrs.font = self._get_current_style_attr("font-desc")
            if attrs.font is None:
                attrs.font = self.textview.style.font_desc
            return attrs


    def __parse_length_frac_size_allocate(self, textview, allocation,
                                          frac, callback, args):
        callback(allocation.width*frac, *args)

    def _parse_length(self, value, font_relative, callback, *args):
        '''Parse/calc length, converting to pixels, calls callback(length, *args)
        when the length is first computed or changes'''
        if value.endswith('%'):
            frac = float(value[:-1])/100
            if font_relative:
                attrs = self._get_current_attributes()
                font_size = attrs.font.get_size() / pango.SCALE
                callback(frac*display_resolution*font_size, *args)
            else:
                ## CSS says "Percentage values: refer to width of the closest
                ##           block-level ancestor"
                ## This is difficult/impossible to implement, so we use
                ## textview width instead; a reasonable approximation..
                alloc = self.textview.get_allocation()
                self.__parse_length_frac_size_allocate(self.textview, alloc,
                                                       frac, callback, args)
                self.textview.connect("size-allocate",
                                      self.__parse_length_frac_size_allocate,
                                      frac, callback, args)

        elif value.endswith('pt'): # points
            callback(float(value[:-2])*display_resolution, *args)

        elif value.endswith('em'): # ems, the height of the element's font
            attrs = self._get_current_attributes()
            font_size = attrs.font.get_size() / pango.SCALE
            callback(float(value[:-2])*display_resolution*font_size, *args)

        elif value.endswith('ex'): # x-height, ~ the height of the letter 'x'
            ## FIXME: figure out how to calculate this correctly
            ##        for now 'em' size is used as approximation
            attrs = self._get_current_attributes()
            font_size = attrs.font.get_size() / pango.SCALE
            callback(float(value[:-2])*display_resolution*font_size, *args)

        elif value.endswith('px'): # pixels
            callback(int(value[:-2]), *args)

        else:
            warnings.warn("Unable to parse length value '%s'" % value)

    def __parse_font_size_cb(length, tag):
        tag.set_property("size-points", length/display_resolution)
    __parse_font_size_cb = staticmethod(__parse_font_size_cb)

    def _parse_style_font_size(self, tag, value):
        try:
            scale = {
                "xx-small": pango.SCALE_XX_SMALL,
                "x-small": pango.SCALE_X_SMALL,
                "small": pango.SCALE_SMALL,
                "medium": pango.SCALE_MEDIUM,
                "large": pango.SCALE_LARGE,
                "x-large": pango.SCALE_X_LARGE,
                "xx-large": pango.SCALE_XX_LARGE,
                } [value]
        except KeyError:
            pass
        else:
            attrs = self._get_current_attributes()
            tag.set_property("scale", scale / attrs.font_scale)
            return
        if value == 'smaller':
            tag.set_property("scale", pango.SCALE_SMALL)
            return
        if value == 'larger':
            tag.set_property("scale", pango.SCALE_LARGE)
            return
        self._parse_length(value, True, self.__parse_font_size_cb, tag)

    def _parse_style_font_style(self, tag, value):
        try:
            style = {
                "normal": pango.STYLE_NORMAL,
                "italic": pango.STYLE_ITALIC,
                "oblique": pango.STYLE_OBLIQUE,
                } [value]
        except KeyError:
            warnings.warn("unknown font-style %s" % value)
        else:
            tag.set_property("style", style)

    def __frac_length_tag_cb(length, tag, propname):
        tag.set_property(propname, length)
    __frac_length_tag_cb = staticmethod(__frac_length_tag_cb)

    def _parse_style_margin_left(self, tag, value):
        self._parse_length(value, False, self.__frac_length_tag_cb,
                           tag, "left-margin")

    def _parse_style_margin_right(self, tag, value):
        self._parse_length(value, False, self.__frac_length_tag_cb,
                           tag, "right-margin")

    def _parse_style_font_weight(self, tag, value):
        ## TODO: missing 'bolder' and 'lighter'
        try:
            weight = {
                '100': pango.WEIGHT_ULTRALIGHT,
                '200': pango.WEIGHT_ULTRALIGHT,
                '300': pango.WEIGHT_LIGHT,
                '400': pango.WEIGHT_NORMAL,
                '500': pango.WEIGHT_NORMAL,
                '600': pango.WEIGHT_BOLD,
                '700': pango.WEIGHT_BOLD,
                '800': pango.WEIGHT_ULTRABOLD,
                '900': pango.WEIGHT_HEAVY,
                'normal': pango.WEIGHT_NORMAL,
                'bold': pango.WEIGHT_BOLD,
                } [value]
        except KeyError:
            warnings.warn("unknown font-style %s" % value)
        else:
            tag.set_property("weight", weight)

    def _parse_style_font_family(self, tag, value):
        tag.set_property("family", value)

    def _parse_style_text_align(self, tag, value):
        try:
            align = {
                'left': gtk.JUSTIFY_LEFT,
                'right': gtk.JUSTIFY_RIGHT,
                'center': gtk.JUSTIFY_CENTER,
                'justify': gtk.JUSTIFY_FILL,
                } [value]
        except KeyError:
            warnings.warn("Invalid text-align:%s requested" % value)
        else:
            tag.set_property("justification", align)

    def _parse_style_text_decoration(self, tag, value):
        tag.set_property("strikethrough", False)
        tag.set_property("underline", pango.UNDERLINE_NONE)

        for chunk in value.split(' '):
            if chunk == "underline":
                tag.set_property("underline", pango.UNDERLINE_SINGLE)
            elif chunk == "overline":
                warnings.warn("text-decoration:overline not implemented")
            elif chunk == "line-through":
                tag.set_property("strikethrough", True)
            elif value == "blink":
                warnings.warn("text-decoration:blink not implemented")
            else:
                warnings.warn("text-decoration:%s not implemented" % value)


    ## build a dictionary mapping styles to methods, for greater speed
    __style_methods = dict()
    for style in ["background-color", "color", "font-family", "font-size",
                  "font-style", "font-weight", "margin-left", "margin-right",
                  "text-align", "text-decoration"]:
        try:
            method = locals()["_parse_style_%s" % style.replace('-', '_')]
        except KeyError:
            warnings.warn("Style attribute '%s' not yet implemented" % style)
        else:
            __style_methods[style] = method
    del style
    ## --

    def _get_style_tags(self):
        return [tag for tag in self.styles if tag is not None]


    def _begin_span(self, style, tag=None):
        if style is None:
            self.styles.append(tag)
            return None
        if tag is None:
            tag = self.textbuf.create_tag()

        l = [item.split(':', 1) for item in style.split(';')]
        l = [ x for x in l if len( x ) == 2 ]
        for attr, val in l:
            attr = attr.strip().lower()
            # strip brake the font-family value
            # for example Sans Serif -> SansSerif
            val = val.lstrip().rstrip()
            try:
                method = self.__style_methods[attr]
            except KeyError:
                warnings.warn("Style attribute '%s' requested "
                              "but not yet implemented" % attr)
            else:
                method(self, tag, val)

        self.styles.append(tag)

    def _end_span(self):
        self.styles.pop(-1)

    def _insert_text(self, text):
        tags = self._get_style_tags()
        if tags:
            self.textbuf.insert_with_tags(self.iter, text, *tags)
        else:
            self.textbuf.insert(self.iter, text)

    def _flush_text(self):
        if not self.text: return
        self._insert_text(self.text.replace('\n', ''))
        self.text = ''

    def anchor_menu_copy_link(self, widget, href):
        clip = gtk.clipboard_get()
        clip.set_text(href)

    def anchor_menu_open_link(self, widget, href, type_):
        self.textview.emit("url-clicked", href, type_)

    def make_anchor_context_menu(self, event, href, type_):
        menu = gtk.Menu()

        menu_items = gtk.ImageMenuItem( _( "_Open link" ) )
        menu_items.set_image( gtk.image_new_from_stock( gtk.STOCK_NETWORK, gtk.ICON_SIZE_MENU ))
        menu.append(menu_items)
        menu_items.connect("activate", self.anchor_menu_open_link, href, type_)
        menu_items.show()

        menu_items = gtk.ImageMenuItem( _( "_Copy link location" ))
        menu_items.set_image( gtk.image_new_from_stock( gtk.STOCK_COPY, gtk.ICON_SIZE_MENU ))
        menu.append(menu_items)
        menu_items.connect("activate", self.anchor_menu_copy_link, href)
        menu_items.show()

        menu.popup(None, None, None, event.button, event.time)

    def _anchor_event(self, tag, textview, event, iter, href, type_):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.textview.emit("url-clicked", href, type_)
            return True
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.make_anchor_context_menu( event, href, type_)
            return True
        return False

    def _object_event( self, widget, event, attrs ):
        callbacks = self.textview.customObjectsCallbacks
        if attrs['type'] in callbacks and callbacks[attrs['type']][1]:
            callbacks[attrs['type']][1]( widget, event, attrs )

    def char_data(self, content):
        self.text += content

    def start_element(self, name, attrs):
        self._flush_text()
        try:
            style = attrs['style']
        except KeyError:
            style = None

        tag = None
        if name == 'a':
            tag = self.textbuf.create_tag()
            tag.set_property('foreground', self.textview.linkColor)
            tag.set_property('underline', pango.UNDERLINE_SINGLE)
            try:
                type_ = attrs['type']
            except KeyError:
                type_ = None
            tag.connect('event', self._anchor_event, attrs['href'], type_)
            tag.is_anchor = True

        self._begin_span(style, tag)

        if name == 'br':
            pass # handled in endElement
        elif name == 'p':
            if not self.iter.starts_line():
                self._insert_text("\n")
        elif name == 'div':
            if not self.iter.starts_line():
                self._insert_text("\n")
        elif name == 'span':
            pass
        elif name == 'ul':
            if not self.iter.starts_line():
                self._insert_text("\n")
            self.list_counters.insert(0, None)
        elif name == 'ol':
            if not self.iter.starts_line():
                self._insert_text("\n")
            self.list_counters.insert(0, 0)
        elif name == 'li':
            if self.list_counters[0] is None:
                li_head = unichr(0x2022)
            else:
                self.list_counters[0] += 1
                li_head = "%i." % self.list_counters[0]
            self.text = ' '*len(self.list_counters)*4 + li_head + ' '
        elif name == 'img':
            try:
                ## Max image size = 10 MB (to try to prevent DoS)
                mem = urllib.urlopen(attrs['src']).read(10*1024*1024)
                ## Caveat: GdkPixbuf is known not to be safe to load
                ## images from network... this program is now potentially
                ## hackable ;)
                loader = gtk.gdk.PixbufLoader()
                loader.write(mem); loader.close()

                anchor = self.textbuf.create_child_anchor(self.iter)
                img = AnimatedResizableImage(100, 100, self.canResize)
                img.set_tooltip(attrs['alt'])
                img.set_from_custom_animation(loader.get_animation())
                img.show()
                self.textview.add_child_at_anchor(img, anchor)
                self.textview.scrollLater()
                self.textview.emotes[anchor] = img
            
            except Exception, ex:
                pixbuf = None
                try:
                    alt = attrs['alt']
                except KeyError:
                    alt = "Broken image"

        elif name == 'object':
            anchor = self.textbuf.create_child_anchor(self.iter)
            customObj = self.textview.setCustomObject( attrs['class'], \
                    type=attrs['type'], alternate_text=str(attrs['data']))
            
            event_box = gtk.EventBox()
            event_box.add( customObj )
            event_box.connect( 'event', self._object_event, attrs.copy() )
            event_box.set_visible_window( False )
            event_box.set_above_child( True )
            event_box.set_events(gtk.gdk.ALL_EVENTS_MASK)
            event_box.show_all()
            self.textview.add_child_at_anchor(event_box, anchor)


        elif name == 'body':
            pass
        elif name == 'a':
            pass
        else:
            warnings.warn("Unhandled element '%s'" % name)

    def end_element(self, name):
        self._flush_text()
        if name == 'p':
            if not self.iter.starts_line():
                self._insert_text("\n")
        elif name == 'div':
            if not self.iter.starts_line():
                self._insert_text("\n")
        elif name == 'span':
            pass
        elif name == 'br':
            self._insert_text("\n")
        elif name == 'ul':
            self.list_counters.pop()
        elif name == 'ol':
            self.list_counters.pop()
        elif name == 'li':
            self._insert_text("\n")
        elif name == 'img':
            pass
        elif name == 'object':
            pass
        elif name == 'body':
            pass
        elif name == 'a':
            pass
        else:
            warnings.warn("Unhandled element '%s'" % name)
        self._end_span()

class AnimatedResizableImage(gtk.Image):
    def __init__(self, maxh=None, maxw=None, canResize=False):
        gtk.Image.__init__(self)    
        
        self.maxh = maxh
        self.maxw = maxw
        self.canResize = canResize
        self.edited_dimensions = False
        self.mustKill = False
        self.connect('destroy', self._must_destroy)
        
    def _must_destroy(self, *args):
        self.mustKill = True
        
    def set_tooltip(self, tooltiptext):
        self.set_property('has-tooltip', True)
        self.set_property('tooltip-text', tooltiptext)

    def set_from_filename(self, filename):
        animation = gtk.gdk.PixbufAnimation(filename)
        if animation.is_static_image():
            self._place_static(animation)
            return
        self._start_animation(animation)
        
    def set_from_custom_animation(self, animation):
        if animation.is_static_image():
            self._place_static(animation)
            return
        self._start_animation(animation)
          
    def _place_static(self, animation):
        self.h = animation.get_height()
        self.w = animation.get_width()
        ratio = float(self.w) / self.h
        while self.h > self.maxh or self.w > self.maxw:
            self.edited_dimensions = True
            if self.h < self.maxh:
                self.h -= 10
            else:
                self.h = self.maxh
            self.w = self.h * ratio
            
        if self.edited_dimensions and self.canResize:
            self.set_from_pixbuf(animation.get_static_image().scale_simple(\
                    int(self.w), self.h, gtk.gdk.INTERP_BILINEAR))    
        else:
            self.set_from_pixbuf(animation.get_static_image())    
            
    def _start_animation(self, animation):
        iteran = animation.get_iter()
        
        self.h = animation.get_height()
        self.w = animation.get_width()
        ratio = float(self.w) / self.h
        while self.h > self.maxh or self.w > self.maxw:
            self.edited_dimensions = True
            if self.h <= self.maxh:
                self.h -= 10
            else:
                self.h = self.maxh
            self.w = self.h * ratio  
        if not self.edited_dimensions or not self.canResize:
            self.set_from_animation(animation) # fallback to default handler
            return
         
        gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)
    
    def _advance(self, iteran):
        iteran.advance()
        if not self.mustKill:
            self.set_from_pixbuf(iteran.get_pixbuf().scale_simple(int(self.w), \
                    self.h, gtk.gdk.INTERP_NEAREST))
        else:
            return False # end the update game.
        
        gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)
        return False
  

class CustomEmoticonObject(object):
    def __init__(self, textview):
        self.imgs = []
        self.textview = textview
        self.pixbuf = None
        self.path = None
        
    def setNewImg(self, path=None, alttext=None, canResize = False):
        img = AnimatedResizableImage(100, 100, canResize)
        img.set_tooltip(alttext)
        img.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        img.show()
        self.imgs.append(img)

        if path:
            self.setImgPath(path)

        self.updateImgs()
        return img
        
    def setImgPath( self, path ):
        self.path = path
        try:
            self.pixbuf = gtk.gdk.PixbufAnimation(path)
        except:
            pass

    def updateImgs( self ):
        if self.pixbuf is not None:
            self.textview.scrollLater()
            for img in self.imgs:
                img.set_from_custom_animation(self.pixbuf)

    def getImgs( self ):
        return self.imgs

class WinkObject(object):
    def __init__(self, textview):
        self.imgs = []
        self.textview = textview
        self.pixbuf = None
        self.path = None

    def setNewImg(self, path=None):
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        img.show()
        self.imgs.append(img)

        if path:
            self.setImgPath(path)

        self.updateImgs()
        return img

    def setImgPath( self, path ):
        self.path = path
        try:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file( path )
        except:
            pass

    def updateImgs( self ):
        if self.pixbuf is not None:
            self.textview.scrollLater()
            for img in self.imgs:
                img.set_from_pixbuf(self.pixbuf)

    def getImgs( self ):
        return self.imgs


class HtmlTextView(gtk.TextView):
    __gtype_name__ = 'HtmlTextView'
    __gsignals__ = {
        'url-clicked': (gobject.SIGNAL_RUN_LAST, None, (str, str)), # href, type
    }

    def __init__(self, controller=None, buff=None, scrolledwin=None ):
        gtk.TextView.__init__(self, buff)
        self.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.set_editable(False)
        self.set_pixels_above_lines(2)
        self.set_pixels_below_lines(2)

        self._last_mark = None
        self._changed_cursor = False
        self.linkColor = "#0000FF"

        self.connect_after('copy-clipboard', self._on_copy_clipboard)
        self.emotes = {}

        self.connect("motion-notify-event", self.__motion_notify_event)
        self.connect("leave-notify-event", self.__leave_event)
        self.connect("enter-notify-event", self.__motion_notify_event)
        self.connect("url-clicked", self.on_link_clicked)
        if scrolledwin:
            scrolledwin.connect("expose-event", lambda x, y: self.queue_draw())

        self.controller = controller
        self.canResize = controller.config.user['canResizeEmoticons']
        
        self.customObjects = {}
        self.customObjectsCallbacks = {
            'application/x-emesene-emoticon': (self.customEmoticon,
                                                     self.customEmoticonEvent),
            'application/x-emesene-ink': (self.ink, None),
            'application/x-emesene-wink': (self.wink, None),
        }
    
    def customEmoticon(self, textview, id, path=None, alttext=None):
        if id in self.customObjects:
            return self.customObjects[id].setNewImg(path, alttext, self.canResize)
        else:
            customEmoticon = CustomEmoticonObject(textview)
            self.customObjects.update({id: customEmoticon})
            return customEmoticon.setNewImg(path, alttext, self.canResize)

    def wink(self, textview, id, path=None, alttext=None):
        if id in self.customObjects:
            return self.customObjects[id].setNewImg(path)
        else:
            wink = WinkObject(textview)
            self.customObjects.update({id: wink})
            return wink.setNewImg(path)

    def customEmoticonEvent(self, img, event, attrs):
        if not attrs['class'] in self.customObjects:
            return
        path = self.customObjects[attrs['class']].path
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            if path:
                menu = gtk.Menu()
                menu_items = gtk.ImageMenuItem(_('_Save as...'))
                menu_items.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE,
                    gtk.ICON_SIZE_MENU))
                menu.append(menu_items)
                menu_items.connect('activate', self.customEmoticonSave, path,
                    attrs['data'])
                menu_items.show()
                menu.popup(None, None, None, event.button, event.time)

    def customEmoticonSave( self, widget , path , shortcut ):
        def _on_ce_edit_cb(response, text=''):
            '''method called when the edition is done'''

            if response == stock.ACCEPT:
                if text:
                    success, msg = self.controller.customEmoticons.create(\
                        text, path, 1)

                    if not success:
                        dialog.error(msg)
                else:
                    dialog.error(_("Empty shortcut"))

        window = dialog.entry_window(_("New shortcut"), shortcut,
            _on_ce_edit_cb, _("Shortcut"))
        window.show()

    def ink( self, textview, id, path=None, alttext=None):
        img = gtk.Image()
        img.set_from_pixbuf( gtk.gdk.pixbuf_new_from_file( id ) )
        img.show()
        return img

    def setCustomObject(self, id, path=None, type=None, alternate_text=None):
        if type in self.customObjectsCallbacks:
            return self.customObjectsCallbacks[type][0](self, id, path, alternate_text)

    def getCustomObjects(self):
        return self.customObjects

    def on_link_clicked(self, view, url, type_):
        desktop.open(url)

    def __leave_event(self, widget, event):
        if self._changed_cursor:
            window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
            window.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._changed_cursor = False

    def __motion_notify_event(self, widget, event):
        x, y, _ = widget.window.get_pointer()
        x, y = widget.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, x, y)
        tags = widget.get_iter_at_location(x, y).get_tags()
        for tag in tags:
            if getattr(tag, 'is_anchor', False):
                is_over_anchor = True
                break
        else:
            is_over_anchor = False
        if not self._changed_cursor and is_over_anchor:
            window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
            window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
            self._changed_cursor = True
        elif self._changed_cursor and not is_over_anchor:
            window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
            window.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._changed_cursor = False
        return False

    def set_background(self, pixbuf):
        '''Sets a background pixbuf to this htmltextview
        If you are using this textview inside a ScrolledWindow, remember to
        pass the "scrolledwin" param to the constructor'''

        # converts the pixbuf to a server side pixmap
        pixmap = pixbuf.render_pixmap_and_mask()[0]

        # gets the text window
        textwnd = self.get_window(gtk.TEXT_WINDOW_TEXT)

        # sets background pixmap
        style = self.get_style()
        style.bg_pixmap[gtk.STATE_NORMAL] = pixmap
        style.set_background(textwnd, gtk.STATE_NORMAL)

        # this works too, but it doesn't apply background under scrollbars
        #textwnd.set_back_pixmap(pixmap, False)

    def display_html(self, htmlu):

        #####################################################################
        # handle WLM's fucking special chars, otherwise htmltextview breaks #
        # let me know if you find other fucking unicode shit crap           #
        #####################################################################
        html = htmlu.\
                replace('\x02', '<span style="font-weight: bold;">').\
                replace('\x1f', '<span style="text-decoration:underline">').\
                replace('\x0f', '').\
                replace('\x03', '').\
                replace('\x04', '').\
                replace('\x08', '')

        buffer = self.get_buffer()
        eob = buffer.get_end_iter()
        parser = xml.parsers.expat.ParserCreate()
        handler = HtmlHandler(self, eob, self.canResize)
        parser.StartElementHandler = handler.start_element
        parser.EndElementHandler = handler.end_element
        parser.CharacterDataHandler = handler.char_data
        parser.Parse(html)
        
        if not eob.starts_line():
            buffer.insert(eob, "\n")

    def scrollToBottom(self, force=False):
        if not force and self.isScrollLocked():
            return False
        textbuffer = self.get_buffer()
        textiter = textbuffer.get_end_iter()
        mark = textbuffer.create_mark("end", textiter, False)
        self._last_mark = mark
        self.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
        textbuffer.place_cursor(textiter)
        return False

    def isScrollLocked(self):
        textiter = self.get_buffer().get_end_iter()
        if self._last_mark:
            rect = self.get_visible_rect()
            pos = rect.y + rect.height
            if (pos + 25) < self.get_iter_location(textiter).y:
                return True
        return False

    def scrollLater(self):
        if not self.isScrollLocked():
            # very ugly but quite effective.
            gobject.timeout_add(200, self.scrollToBottom, True)

    def _on_copy_clipboard(self, textview):
        ''' replaces the copied text with a new text with the
        alt text of the images selected at copying '''
        buffer = textview.get_buffer()
        if buffer.get_has_selection():
            iterStart, iterEnd = buffer.get_selection_bounds()
            if iterStart.get_offset() > iterEnd.get_offset():
                temp = start.copy()
                iterStart = iterEnd.copy()
                iterEnd = temp.copy() #set the right begining

            text = buffer.get_slice(iterStart, iterEnd)

            #TODO: magic string '\xef\xbf\xbc', object replacement special char
            while iterStart.forward_search('\xef\xbf\xbc', \
                             gtk.TEXT_SEARCH_VISIBLE_ONLY):

                iterPos, iterEnd = iterStart.forward_search('\xef\xbf\xbc', \
                                  gtk.TEXT_SEARCH_VISIBLE_ONLY)
                anchor = iterPos.get_child_anchor()
                if anchor and anchor.get_widgets():
                    widget = anchor.get_widgets()[0]
                    if isinstance(widget, gtk.EventBox):
                        alt = anchor.get_widgets()[0].child.get_tooltip_text()
                    else:
                        alt = anchor.get_widgets()[0].get_tooltip_text()
                elif anchor is None:
                    alt = ''
                
                text = text.replace('\xef\xbf\xbc', alt, 1)

                iterStart = iterEnd

            clipboard = gtk.clipboard_get()
            clipboard.set_text(text)
            clipboard.store()

    def clear(self):
        self.get_buffer().set_text('')
        self.emotes = {}
            
if __name__ == '__main__':
    sw = gtk.ScrolledWindow()
    htmlview = HtmlTextView(scrolledwin=sw)
    def url_cb(view, url, type_):
        print "url-clicked", url, type_
    htmlview.connect("url-clicked", url_cb)

    #~ htmlview.display_html('<div><span style="color: red; text-decoration:underline">Hello</span><br/>\n'
                          #~ '  <img src="http://images.slashdot.org/topics/topicsoftware.gif"/><br/>\n'
                          #~ '  <span style="font-size: 500%; font-family: serif">World</span>\n'
                          #~ '</div>\n')
    #~ htmlview.display_html("<br/>")
    #~ htmlview.display_html("""
      #~ <p style='font-size:large'>
        #~ <span style='font-style: italic'>O<span style='font-size:larger'>M</span>G</span>,
        #~ I&apos;m <span style='color:green'>green</span>
        #~ with <span style='font-weight: bold'>envy</span>!
      #~ </p>
        #~ """)
    #~ htmlview.display_html("<br/>")
    #~ htmlview.display_html("""
    #~ <body xmlns='http://www.w3.org/1999/xhtml'>
      #~ <p>As Emerson said in his essay <span style='font-style: italic; background-color:cyan'>Self-Reliance</span>:</p>
      #~ <p style='margin-left: 5px; margin-right: 2%'>
        #~ &quot;A foolish consistency is the hobgoblin of little minds.&quot;
      #~ </p>
    #~ </body>
        #~ """)
    #~ htmlview.display_html("<br/>")
    #~ htmlview.display_html("""
    #~ <body xmlns='http://www.w3.org/1999/xhtml'>
      #~ <p style='text-align:center'>Hey, are you licensed to <a href='http://www.jabber.org/'>Jabber</a>?</p>
      #~ <p style='text-align:right'><img src='http://www.jabber.org/images/psa-license.jpg'
              #~ alt='A License to Jabber'
              #~ height='261'
              #~ width='537'/></p>
    #~ </body>
        #~ """)

    #~ htmlview.display_html("""
    #~ <body xmlns='http://www.w3.org/1999/xhtml'>
      #~ <ul style='background-color:rgb(120,140,100)'>
       #~ <li> One </li>
       #~ <li> Two </li>
       #~ <li> Three </li>
      #~ </ul>
    #~ </body>
        #~ """)
    #~ htmlview.display_html("""
    #~ <body xmlns='http://www.w3.org/1999/xhtml'>
      #~ <ol>
       #~ <li> One </li>
       #~ <li> Two </li>
       #~ <li> Three </li>
      #~ </ol>
    #~ </body>
        #~ """)
    htmlview.display_html('<body>If you are reading this, you may be ' \
        'interested in that useless text that came with htmltextview. ' \
        'Try uncommenting the code above this line.</body>')

    htmlview.show()

    sw.set_property("hscrollbar-policy", gtk.POLICY_AUTOMATIC)
    sw.set_property("vscrollbar-policy", gtk.POLICY_AUTOMATIC)
    sw.set_property("border-width", 0)
    sw.add(htmlview)
    sw.show()
    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    frame.show()
    frame.add( sw )
    w = gtk.Window()
    w.add(frame)
    w.set_default_size(400, 300)
    w.show_all()

    # set background
    #pixbuf = gtk.gdk.pixbuf_new_from_file("Auto.jpg")
    #htmlview.set_background(pixbuf)

    w.connect("destroy", lambda w: gtk.main_quit())
    gtk.main()
