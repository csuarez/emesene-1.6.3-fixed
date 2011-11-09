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

import pygtk
import gtk
import gtk.gdk
import cairo


''' A set of useful cairo related methods '''    
def set_context_color(context, color = gtk.gdk.color_parse('#000000')):
    r = float(color.red) / 65535
    g = float(color.green) / 65535
    b = float(color.blue) / 65535
    context.set_source_rgb(r,g,b)
    
def image_surface_from_pixbuf( pixbuf=None):
    if pixbuf is not None:
        return cairo.ImageSurface.create_for_data(
            pixbuf.get_pixels_array(), 
            cairo.FORMAT_ARGB32,
            pixbuf.get_width(),
            pixbuf.get_height(), 
            pixbuf.get_rowstride())
    else:
        return cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)

def resize_image_surface(surface, new_width, new_height):
    new_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, new_width, new_height)
    cr = cairo.Context(new_surface)
    cr.set_source_surface(surface, 0, 0)
    cr.paint()
    return new_surface
    
class ToolType(object):
    Paintbrush, Eraser = range(2)

class Point(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        if (self.x == other.x) and (self.y == other.y):
            return True
        else:
            return False

        
class DrawAttributes( object ):
    def __init__( self, color=gtk.gdk.Color(0, 0, 0), stroke_size=8, tool_type=ToolType.Paintbrush ):
        self.color = color
        self.stroke_size = stroke_size
        self.tool_type = tool_type

class BrushPath(object):
    """ represents a single brush path and has the ability to draw itself """
    def __init__(self, start_point, draw_attr):
        self._points = []
        self._stroke_size = draw_attr.stroke_size
        self._shift = int((draw_attr.stroke_size/2) + 1)
        self._color = draw_attr.color
        self._tool_type = draw_attr.tool_type
        if self._tool_type == ToolType.Paintbrush:
            self._operator = cairo.OPERATOR_OVER
        else: # self._tool_type == ToolType.Eraser
            self._operator = cairo.OPERATOR_CLEAR
        self._path_rectangle = gtk.gdk.Rectangle()
        self._intermediate_rectangle = gtk.gdk.Rectangle() 
        self.add(start_point)

    def add(self, point):
        self._points.append(point)                    
        #--- update path rectangle
        i_rec = self.__create_point_rectangle(point)
        self._path_rectangle = self._path_rectangle.union(i_rec)
        
        #... update intermediate rectangle            
        i_points = self._points[-2:len(self._points)]
        for pnt in i_points[0:len(i_points)-1]:
            z_rec = self.__create_point_rectangle(pnt)                
            i_rec = i_rec.union(z_rec)
        self._intermediate_rectangle = i_rec

    def get_path_rectangle(self):
            return self._path_rectangle
    def get_intermediate_rectangle(self):
            return self._intermediate_rectangle

    def draw(self, ctx, x=0, y=0):
        points = self._points
        if not points: return
        ctx.save()
        ctx.set_operator(self._operator)
        ctx.translate(x,y)
        x, y, width, height = self._path_rectangle
        ctx.rectangle(x,y, width, height)
        ctx.clip()
        ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)   
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        set_context_color(ctx, self._color)
        ctx.set_line_width(self._stroke_size)
        ctx.move_to(points[0].x, points[0].y)
        for point in points[1:len(points)]:
            ctx.line_to(point.x, point.y)
        if len(points) == 1:
            ctx.line_to(points[0].x, points[0].y)
        ctx.stroke()
        ctx.restore()
        
    def print_info(self):
        for pt in self._points:
            print pt.x, pt.y
                
    def __create_point_rectangle(self, point):
        return gtk.gdk.Rectangle( 
            int(point.x - self._shift), int(point.y - self._shift), 
            int(self._shift * 2), int(self._shift * 2))   

