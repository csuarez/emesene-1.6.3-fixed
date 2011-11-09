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

#    Ink drawing widgets from alencool

import pygtk
import gtk
import gtk.gdk
import cairo
import gobject
from math import pi

from pyisf import pyisf
from pyisf.drawing import *

#TODO: add button 'send' that encodes pixmap in isf and send to current conversation

class InkDraw(gtk.Window):
    def __init__(self, controller):
        gtk.Window.__init__(self)
        
        theme = gtk.icon_theme_get_default()
        theme.prepend_search_path('themes/default')
        #filename = 'pyisf/colors.isf'
        #data = open(filename, 'rb').read()
    
        self.set_size_request(400, 400)
        vbox = gtk.VBox()
        inkcanvas = InkCanvas(theme)
        inktoolbar = InkToolbar(theme, inkcanvas)
        vbox.pack_start(inktoolbar, expand = False)
        vbox.pack_start(inkcanvas)
        self.add(vbox)
        self.show_all()
        self.connect('delete_event', self.delete_event, inkcanvas)
    
        #inkcanvas.import_isf(data)
        
    def delete_event(self, *args):
        self.hide()

class ColorLabel(gtk.Widget):
    ''' Square shaped, color label '''   
    __gsignals__ = { 'size_request' : 'override', 'expose-event' : 'override' }
    
    _color = gtk.gdk.color_parse('#000000')
    _dimention = 20
    
    def __init__(self, color = gtk.gdk.color_parse('#000000')):
        gobject.GObject.__init__(self)
        gtk.Widget.__init__(self)
        self.set_flags(self.flags() | gtk.NO_WINDOW )       
        self._color = color

    def do_size_request(self,requisition):
        requisition.width = self._dimention
        requisition.height = self._dimention

    def do_expose_event(self, event):
        x , y, width, height = event.area
        dimention = min(width,height)
        y += (height /2) - (dimention /2)
        width, height = dimention, dimention
        ctx = event.window.cairo_create()
        ctx.translate(x, y) 
        ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)        
        ctx.rectangle(0, 0, width, height)
        ctx.clip_preserve()
        set_context_color(ctx, self._color)
        ctx.fill_preserve()
        ctx.set_line_width(1.0)
        set_context_color(ctx, gtk.gdk.color_parse('#000000'))
        ctx.stroke()

    def set_color(self, color=gtk.gdk.color_parse('#000000')):
        self._color = color
        self.queue_draw()
        
    def get_color(self): 
        return self._color

gobject.type_register(ColorLabel)

class ColumnContainer(gtk.Box):
    ''' Container that postions widgets into a given column number'''
    __gsignals__ = { 'size_request' : 'override','size_allocate' : 'override' }
    
    _cols = 1       # number of columns
    _cr_width = 0   # child requisition width
    _cr_height = 0  # child requisition height
    _vc_number = 0  # number of visual children
    
    def __init__(self, column_number=1):
        gtk.Box.__init__(self)
        if column_number < 1:
            self._cols = 1
        else:
            self._cols = column_number

    def update_child_info(self):
        visual_children_number = 0
        child_requisition_width = 0
        child_requisition_height = 0
        for child in self.get_children():
            if child.get_property('visible'):
                child_request_width, child_request_height = child.size_request()
                child_requisition_width = max(child_requisition_width, child_request_width)
                child_requisition_height = max(child_requisition_height, child_request_height)
                visual_children_number += 1
        self._cr_width = child_requisition_width
        self._cr_height = child_requisition_height
        self._vc_number = visual_children_number
                        
    def do_size_request(self, requisition):
        self.update_child_info()        
        width, height = 0, 0          
        if self._vc_number > 0:
            width = self._cr_width * self._cols
            if self._vc_number <= self._cols:    
                height = self._cr_height
            elif (self._vc_number % self._cols ) == 0 :
                height = self._cr_height * ( self._vc_number / self._cols)
            else:
                height = self._cr_height * (( self._vc_number / self._cols) + 1)
        requisition.width = width
        requisition.height = height

    def do_size_allocate(self, allocation):     
        width = allocation.width / self._cols
        height = self._cr_height
        x, y = allocation.x, allocation.y
        col_spaces_remaining = self._cols
        for child in self.get_children():
            child.size_allocate(gtk.gdk.Rectangle(x, y, width, height))
            col_spaces_remaining -= 1
            if col_spaces_remaining == 0:
                y += height
                x = allocation.x
                col_spaces_remaining = self._cols
            else:
                x += width
                
gobject.type_register(ColumnContainer)

class DropdownWindow(gtk.Window):
    __gsignals__ = {
        'map-event' : 'override',
        'unmap-event' : 'override',
        'button-press-event' : 'override',
        'key-press-event' : 'override',
        }

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU)
        self.set_decorated(False)

    def do_map_event(self, event):
        self.grab_focus()
        self.grab_add()
        time = gtk.get_current_event_time()
        gtk.gdk.pointer_grab(self.window, True, gtk.gdk.BUTTON_PRESS_MASK, None, None, time)
        gtk.gdk.keyboard_grab(self.window, True, time)

    def do_unmap_event(self, event): 
        time = gtk.get_current_event_time()
        gtk.gdk.pointer_ungrab(time)
        gtk.gdk.keyboard_ungrab(time)
        self.grab_remove()

    def do_button_press_event(self, event):
        win_tuple = gtk.gdk.window_at_pointer()
        if (win_tuple is None) or not( win_tuple[0] == self.window) : self.hide()
        return True

    def do_key_press_event(self, event):
        if not gtk.Window.do_key_press_event(self, event) \
               and event.keyval == gtk.gdk.keyval_from_name("Escape"):
            self.hide()
            return True

gobject.type_register(DropdownWindow)

class ColorButton(gtk.ToggleButton):
    __gsignals__ = { 
        'color-set' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_PYOBJECT,)),
        'button-press-event' : 'override'
        }
    _color = gtk.gdk.Color(0,0,0)
    _tango_colors = [ \
        '#2e3436', '#babdb6', '#a40000', '#5c3566', '#204a87', '#4e9a06', '#8f5902', '#ce5c00', '#c4a000',
        '#555753', '#d3d7cf', '#cc0000', '#75507b', '#3465a4', '#73d216', '#c17d11', '#f57900', '#edd400',
        '#888a85', '#eeeeec', '#ef2929', '#ad7fa8', '#729fcf', '#8ae234', '#e9b96e', '#fcaf3e', '#fce94f']

    def __init__(self, widget):
        gtk.Button.__init__(self)
        self.add(widget)
        self.set_property("can-default", False)
        self.set_property("can-focus", False)
        self.set_border_width(0)
        self.set_relief(gtk.RELIEF_NONE)
        self._dropdown_win = DropdownWindow()
        self._dropdown_win.realize()
        self._dropdown_win.connect("map-event", self.__win_map)
        self._dropdown_win.connect("unmap-event", self.__win_unmap)

        container = ColumnContainer(9)
        hbox = gtk.HBox()
        for hex_color in self._tango_colors:       
            container.add(self.__create_button(hex_color))
        for hex_color in ('#000000','#ffffff'):
            hbox.pack_start(self.__create_button(hex_color), False, False)    
        vbox = gtk.VBox()
        vbox.pack_start(hbox, False, False)
        vbox.pack_start(container, False, False)
        self._dropdown_win.add(vbox)
        
    def __create_button(self, hex_color='#000000'):
        label = ColorLabel(gtk.gdk.color_parse(hex_color))
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.set_property("can-default", False)
        button.set_property("can-focus", False)                
        button.set_border_width(0)
        button.add(label)
        button.connect('clicked', self.__color_selected, label.get_color())    
        return button
        
    def __color_selected(self, widget, color):
        self._color = color
        self._dropdown_win.hide()
        self.emit('color-set', self._color)
    
    def __win_map(self, win, event): self.set_active(True)
    def __win_unmap(self, win, event): self.set_active(False)

    def __position(self, win):
        x, y = self.window.get_origin()
        alloc = self.allocation
        x, y = x + alloc.x, y + alloc.y
        width, height = win.get_size()
        if x + width > self.get_screen().get_width(): x += alloc.width - width
        if y + alloc.height + height > self.get_screen().get_height(): y -= height
        else: y += alloc.height
        win.move(x, y)
    
    def get_color(self): return self._color
    
    def do_button_press_event(self, event):
        if not self.get_active():
            self.__position(self._dropdown_win)
            self._dropdown_win.show_all()
            self._dropdown_win.present()
        return True        
gobject.type_register(ColorButton)

class GridType(object):
    Blank, Small, Medium, Large = range(4)
    
class GridButton(gtk.ToggleButton):
    __gsignals__ = { 
        'grid-type-set' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_PYOBJECT,)),
        'button-press-event' : 'override'
        }

    def __init__(self, button_icon, blank_icon, small_icon, medium_icon, large_icon, grid_type=GridType.Blank):
        gtk.Button.__init__(self)
        hbox = gtk.HBox()
        hbox.pack_start(button_icon)
        hbox.pack_start(gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_IN))
        self.add(hbox)
        self.set_property("can-default", False)
        self.set_property("can-focus", False)
        self.set_border_width(0)
        self.set_relief(gtk.RELIEF_NONE)
        self._grid_type = grid_type
        
        ### Grid Menu
        self._blank_item = self.__create_grid_item('Blank', blank_icon, GridType.Blank)
        self._small_item = self.__create_grid_item('Small grid', small_icon, GridType.Small)
        self._medium_item = self.__create_grid_item('Medium grid', medium_icon, GridType.Medium)
        self._large_item = self.__create_grid_item('Large grid', large_icon, GridType.Large)
        
        self._grid_menu = gtk.Menu()
        self._grid_menu.append(self._blank_item)
        self._grid_menu.append(gtk.SeparatorMenuItem())
        self._grid_menu.append(self._small_item)        
        self._grid_menu.append(self._medium_item)
        self._grid_menu.append(self._large_item)
        self._grid_menu.connect("unmap-event", self.__win_unmap)           
    
    def __create_grid_item(self, label, icon, grid_type):
        grid_item = gtk.ImageMenuItem(label)
        grid_item.set_image(icon)
        grid_item.connect('activate', self.__item_activate, grid_type)
        return grid_item
        
    def __item_activate(self, menuitem, grid_type):
        self._grid_type = grid_type
        self.emit('grid-type-set', self._grid_type)
        
    def __win_unmap(self, win, ev): self.set_active(False)
        
    def __menu_postion(self, menu):
        x, y = self.window.get_origin()
        alloc = self.allocation                
        x, y = x + alloc.x, y + alloc.y
        menu_allocation = menu.allocation
        width, height = menu_allocation.width, menu_allocation.height
        if x + width > self.get_screen().get_width(): x += alloc.width - width
        if y + alloc.height + height > self.get_screen().get_height(): y -= height
        else: y += alloc.height
        return (x,y, True)
        
    def do_button_press_event(self, event):
        if not self.get_active():
            self._grid_menu.popup(None, None, self.__menu_postion, event.button, event.time)
            self.set_active(True)
            self._grid_menu.show_all()
            if self._grid_type == GridType.Blank: self._grid_menu.select_item(self._blank_item)
            elif self._grid_type == GridType.Small: self._grid_menu.select_item(self._small_item)
            elif self._grid_type == GridType.Medium: self._grid_menu.select_item(self._medium_item)
            elif self._grid_type == GridType.Large: self._grid_menu.select_item(self._large_item)                    
        return True     
           
gobject.type_register(GridButton)


class InkCanvas(gtk.DrawingArea):

    __gsignals__ = {
        'expose_event' : 'override',
        'motion_notify_event' : 'override',
        'button_press_event' : 'override',
        'button_release_event' : 'override',
        'realize': 'override',
        'configure-event': 'override',
        }

    _history = []
    _paths = []     
    _tool_type = ToolType.Paintbrush
    _stroke_size = 8
    _stroke_color = gtk.gdk.Color(0, 0, 0)
    _grid_type = GridType.Blank  
    _grid_size = {
        GridType.Blank:     -1,
        GridType.Small:     10,
        GridType.Medium:    20,
        GridType.Large:     30,
        }    
    _pointer_surface = None
    _cached_grid_surface = None
    _cached_painting_surface = None
    _tool_type_to_surface = {}
    _is_pressed = False
    _intermediate_path = None

    
    def __init__(self, theme):
        gtk.DrawingArea.__init__(self)
        self.set_events( 
            gtk.gdk.EXPOSURE_MASK       | gtk.gdk.LEAVE_NOTIFY_MASK     | gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK   | gtk.gdk.POINTER_MOTION_HINT_MASK) 

        self._pointer_surface = image_surface_from_pixbuf(theme.load_icon('cursor-mouse', 48, 0))
        self._tool_type_to_surface = {
            ToolType.Paintbrush: image_surface_from_pixbuf(theme.load_icon('tool-paintbrush', 48, 0)),
            ToolType.Eraser: image_surface_from_pixbuf(theme.load_icon('tool-eraser', 48, 0)), 
            }
        
    def set_tool_type(self, tool_type=ToolType.Paintbrush):
        self._tool_type = tool_type
        self.__update_cursor()
        
    def set_stroke_size(self, stroke_size= 10):
        if stroke_size < 1:
            self._stroke_size = 1
        else:
            self._stroke_size = stroke_size
        self.__update_cursor()

    def set_stroke_color(self, color = gtk.gdk.Color(0, 0, 0)):
        self._stroke_color = color
    
    def get_stroke_color(self):
        return self._stroke_color
    
    def set_grid_type(self, grid_type):
        self._grid_type = grid_type
        self.__update_grid_surface(self.allocation.width, self.allocation.height)
        self.queue_draw()
    
    def get_grid_type(self):
        return self._grid_type
   
    def undo(self):
        if len(self._paths) > 0:
            self._history.append(self._paths.pop())
            self._cached_painting_surface = self.__build_paths_surface()
            self.queue_draw()
                    
    def redo(self):
        if len(self._history) > 0:
            self._paths.append(self._history.pop())
            self._cached_painting_surface = self.__build_paths_surface()
            self.queue_draw()

    def clear_canvas(self):
        self._cached_painting_surface = None
        self._paths=[]
        self._history = []
        self.queue_draw()
        
    def build_pixbuf(self):
        surface = self.__build_paths_surface()
        return gtk.gdk.pixbuf_new_from_data(
            surface.get_data(), 
            gtk.gdk.COLORSPACE_RGB, True, 8, 
            surface.get_width(), surface.get_height(), 
            surface.get_stride())
            
    def build_isf(self):
        enc = pyisf.IsfEncoder(self._paths)
        return enc
        
    def import_isf(self, data, debug=False):
        dec = pyisf.IsfDecoder(data,True)
        if debug:
            dec.print_info()
        self._paths = dec.paths
        self._cached_painting_surface = self.__build_paths_surface()
        self.queue_draw()

    def do_button_press_event(self, event):
        if event.button == 1:
            self._is_pressed = True
            self._history = []
            draw_attr = DrawAttributes(self._stroke_color, self._stroke_size, self._tool_type)
            path = BrushPath(Point(event.x, event.y), draw_attr)
            self._paths.append(path)
            rec = path.get_intermediate_rectangle()
            self._intermediate_path = path
            self.queue_draw_area(rec.x, rec.y, rec.width, rec.height)
        return True
        
    def do_motion_notify_event(self, event):
        x,y =  event.get_coords()
        if self._is_pressed:
            path = self._paths[-1]
            path.add(Point(x,y))
            rec = path.get_intermediate_rectangle()
            self.queue_draw_area(rec.x, rec.y, rec.width, rec.height)
        return True

    def do_button_release_event(self, event):
        if self._is_pressed:
            self._is_pressed = False
            self._intermediate_path = None
            self.__update_cached_painting_surface(self._paths[-1])
        return True

    def do_expose_event(self, event):
        x , y, width, height = event.area
        ctx = event.window.cairo_create()      
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        cr.translate(-x, -y)
        if self._cached_painting_surface:
            cr.set_source_surface(self._cached_painting_surface,0,0)        
            cr.paint()
        if self._intermediate_path:
            self._intermediate_path.draw(cr,0,0)
        self.__draw_grid(cr, x, y)
        self.__draw_canvas(cr, x,y, width, height)
        ctx.set_source_surface(surface,x,y)
        ctx.paint()
        return False

    def do_realize(self):
        gtk.DrawingArea.do_realize(self)
        self.__update_cursor()
        
    def do_configure_event(self, event):
        self.__update_grid_surface(event.width, event.height)
      
    def __draw_grid(self, ctx, x,y):
        if self._cached_grid_surface is not None:
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_DEST_OVER)            
            ctx.set_source_surface(self._cached_grid_surface, 0, 0)
            ctx.paint()
            ctx.restore()

    def __draw_canvas(self, ctx, x,y, width, height, color = gtk.gdk.color_parse('#ffffff')):
        ctx.save()
        set_context_color(ctx, color)
        ctx.set_operator(cairo.OPERATOR_DEST_OVER)
        ctx.paint()
        ctx.restore()

    def __update_cached_painting_surface(self, path):

        if not self._cached_painting_surface:
            self._cached_painting_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        
        surface_width = self._cached_painting_surface.get_width()
        surface_height = self._cached_painting_surface.get_height()
        rec = path.get_path_rectangle() 
    
        combined = rec.union( gtk.gdk.Rectangle(0,0,surface_width,surface_height))        
        if (surface_width < combined.width) or (surface_height < combined.height):
            self._cached_painting_surface = resize_image_surface(
                self._cached_painting_surface, combined.width, combined.height)
        ctx = cairo.Context(self._cached_painting_surface)
        path.draw(ctx)
        self.queue_draw_area(rec.x, rec.y, rec.width, rec.height)
                
    def __update_grid_surface(self, width, height, color = gtk.gdk.color_parse('#C0C0C0')):
        self._cached_grid_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(self._cached_grid_surface)        
        space = self._grid_size[self._grid_type]
        if space < 1: return
        x, y = 0,0
        position = x + space
        end = x + width
        ctx.save()
        set_context_color(ctx, color)
        ctx.set_line_width(1)
        position = x + space
        end = x + width
        while position < end:
            ctx.move_to(position, y)
            ctx.line_to(position, y + height)
            position += space
        position = y + space
        end = y + height
        while position < end:
            ctx.move_to(x, position )
            ctx.line_to(x + width, position)
            position += space
        ctx.stroke()
        ctx.restore()

    def __build_paths_surface(self):
        rec = gtk.gdk.Rectangle()
        for path in self._paths:
            rec = rec.union(path.get_path_rectangle())
        width = max(1, rec.width)
        height = max(1, rec.height)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        for path in self._paths:
            path.draw(ctx)
        return surface

    def __update_cursor(self):
        indicator_surface = self._tool_type_to_surface[self._tool_type]
        radius = int(self._stroke_size/2.0)
        shift = radius +1
        cursor_width = int(radius + max(self._pointer_surface.get_width(),  indicator_surface.get_width()))
        cursor_height = int(radius + max(self._pointer_surface.get_height(), indicator_surface.get_height()))                    
        cursor_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, cursor_width, cursor_height)
        ctx = cairo.Context(cursor_surface)
        ctx.save()
        ctx.set_line_width(1.0), ctx.set_source_rgb(0,0,0), ctx.set_dash([1,1],0)
        ctx.arc(shift,shift,radius, 0, 2 * pi), ctx.stroke()
        ctx.set_source_surface(self._pointer_surface, shift, shift), ctx.paint()
        ctx.set_source_surface(indicator_surface, shift, shift), ctx.paint()
        ctx.restore()
        pixbuf = gtk.gdk.pixbuf_new_from_data(
            cursor_surface.get_data(), 
            gtk.gdk.COLORSPACE_RGB, True, 8, 
            cursor_surface.get_width(), cursor_surface.get_height(), 
            cursor_surface.get_stride())
        cursor = gtk.gdk.Cursor(self.window.get_display(), pixbuf, shift, shift)
        self.window.set_cursor(cursor)

gobject.type_register(InkCanvas)

class InkToolbar(gtk.Toolbar):
    def __init__(self, theme, ink_canvas):
        gtk.Toolbar.__init__(self)
        self._inkcanvas = ink_canvas

        ### paint button
        paint_image = gtk.Image()
        paint_image.set_from_pixbuf(theme.load_icon('paintbrush', 48, 0))
        paint_button = gtk.RadioToolButton()
        paint_button.set_icon_widget(paint_image)
        paint_button.set_label('Paintbrush')
        paint_button.connect('clicked', self.__set_paint)
        
        ### eraser button
        erase_image = gtk.Image()
        erase_image.set_from_pixbuf(theme.load_icon('eraser', 48, 0))
        erase_button = gtk.RadioToolButton(paint_button)
        erase_button.set_icon_widget(erase_image)
        erase_button.set_label('Eraser')
        erase_button.connect('clicked', self.__set_eraser)

        ### Color select
        self._color_label = ColorLabel(self._inkcanvas.get_stroke_color())
        hbox = gtk.HBox()        
        hbox.pack_start(self._color_label)
        hbox.pack_start(gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_IN))
        color_button = gtk.ToolItem()
        color_button_t = ColorButton(hbox)
        color_button_t.connect('color-set', self.__color_set, paint_button)
        color_button.add(color_button_t)
        
        ### clear button
        imgclear = gtk.Image()
        imgclear.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_LARGE_TOOLBAR )
        clear = gtk.ToolButton(imgclear)
        clear.set_label('Clear')
        clear.connect( 'clicked', self.__clear_canvas )
        
        
        main_img = gtk.Image()
        main_img.set_from_pixbuf(theme.load_icon('medium_grid', 48, 0))
        blank_img = gtk.Image()
        blank_img.set_from_pixbuf(theme.load_icon('no_grid', 48, 0) )
        small_img = gtk.Image()
        small_img.set_from_pixbuf(theme.load_icon('small_grid', 48, 0))
        medium_img = gtk.Image()
        medium_img.set_from_pixbuf(theme.load_icon('medium_grid', 48, 0))
        large_img = gtk.Image()
        large_img.set_from_pixbuf(theme.load_icon('large_grid', 48, 0))
        
        ### grid button
        grid_button_t = GridButton(
            main_img, blank_img, small_img, medium_img, large_img,
            self._inkcanvas.get_grid_type())
        grid_button_t.connect( 'grid-type-set', self.__set_grid_type)
        grid_button = gtk.ToolItem()
        grid_button.add(grid_button_t)

        ### undo Button
        undo_button = gtk.ToolButton()
        undo_button.set_stock_id(gtk.STOCK_UNDO)
        undo_button.connect("clicked", self.__undo)

        ### redo Button
        redo_button = gtk.ToolButton()
        redo_button.set_stock_id(gtk.STOCK_REDO)
        redo_button.connect("clicked", self.__redo)
        
        ### size Slider
        brushsmall_t = gtk.Image()
        brushsmall_t.set_from_pixbuf(theme.load_icon('brush-small', 48, 0))
        brushsmall = gtk.ToolItem()
        brushsmall.add(brushsmall_t)
        
        brushlarge_t = gtk.Image()
        brushlarge_t.set_from_pixbuf(theme.load_icon('brush-large', 48, 0))
        brushlarge = gtk.ToolItem()
        brushlarge.add(brushlarge_t)
        
        brush_slider_t = gtk.HScale(gtk.Adjustment(value=8, lower=1, upper=20, step_incr=0.5, page_incr=1, page_size=0))
        brush_slider_t.set_size_request(130, -1)
        brush_slider_t.set_value_pos(gtk.POS_RIGHT)
        brush_slider_t.set_digits(0)
        brush_slider_t.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        brush_slider_t.connect("value-changed", self.__set_size)
        brush_slider = gtk.ToolItem()
        brush_slider.add(brush_slider_t)
                
        ### toolbar
        self.set_show_arrow(True)
        self.insert(color_button, -1)
        self.insert(gtk.SeparatorToolItem(), -1)
        self.insert(paint_button, -1)
        self.insert(erase_button, -1)
        self.insert(gtk.SeparatorToolItem(), -1)
        self.insert(undo_button, -1)
        self.insert(redo_button, -1)
        self.insert(gtk.SeparatorToolItem(), -1)
        self.insert(clear, -1)
        self.insert(gtk.SeparatorToolItem(), -1)
        self.insert(grid_button, -1)
        self.insert(gtk.SeparatorToolItem(), -1)
        self.insert(brushsmall, -1)
        self.insert(brush_slider, -1)
        self.insert(brushlarge, -1)

    def __color_set(self, widget, color, paint_button):
        print color.to_string()
        self._color_label.set_color(color)
        self._inkcanvas.set_stroke_color(color)
        self._inkcanvas.set_tool_type(ToolType.Paintbrush)
        paint_button.set_active(True)

    def __set_paint(self, widget=None):
        self._inkcanvas.set_tool_type(ToolType.Paintbrush)

    def __set_eraser(self, widget=None):
        self._inkcanvas.set_tool_type(ToolType.Eraser)

    def __clear_canvas(self, widget):
        self._inkcanvas.clear_canvas()

    def __set_grid_type(self, widget, grid_type):
        self._inkcanvas.set_grid_type(grid_type)

    def __undo(self, widget):
        self._inkcanvas.undo()
        
    def __redo(self, widget):
        self._inkcanvas.redo()
 
    def __set_size(self, range_widget):
        self._inkcanvas.set_stroke_size(range_widget.get_value())

gobject.type_register(InkToolbar)
