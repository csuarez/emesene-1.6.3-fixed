# -*- coding: utf-8 -*-
#
#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

'''Converts a gtk.gdk.Pixbuf into a GifEncoder instance'''

import pygif

import StringIO
import gtk

def convert(pixbuf, enc=None):
    '''Parses gtk.gdk.Pixbuf pixels and returns a GifEncoder instance'''

    if enc is None:
        enc = pygif.GifEncoder()

    enc.ls_width = pixbuf.get_width()
    enc.ls_height = pixbuf.get_height()
    bpp = pixbuf.get_n_channels()
    assert pixbuf.get_bits_per_sample() == 8
    
    # we have two palletes
    # the "definitive", tuple based pallete
    # and a quick search string pallete
    enc.pallete = []
    string_pallete = []

    raw_pixels = StringIO.StringIO(pixbuf.get_pixels())
    out_pixels = []

    while True:
        rgb = raw_pixels.read(bpp)
        if len(rgb) != bpp:
            break
        
        red, green, blue = ord(rgb[0]), ord(rgb[1]), ord(rgb[2])
        # uncomment the following to have ASCII art debug :P
        #sys.stdout.write(hex(red)[2])
        
        if rgb not in string_pallete:
            index = len(enc.pallete)
            string_pallete.append(rgb)
            enc.pallete.append((red, green, blue))
        else:
            index = string_pallete.index(rgb)

        out_pixels.append(index)
    del string_pallete

    enc.global_color_table_size = len(enc.pallete)
    enc.color_table_flag = True
    enc.color_resolution = 7 # 256 colors
    enc.build_flags()
    
    image = enc.new_image()
    image.codesize, image.lzwcode = enc.lzw_encode(out_pixels)
    return enc

def main():
    '''runs a simple test with vampire.gif'''
    pixbuf = gtk.gdk.pixbuf_new_from_file("vampire.gif")
    enc = convert(pixbuf)
    enc.write("vampire_pixbuf.gif")

if __name__ == '__main__':
    main()
