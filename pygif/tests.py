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

'''unit tests for pygif
requires netpbm tools (specifically "giftopnm")'''

import os
import unittest

import pygif

class CloneTests(unittest.TestCase):
    '''Tests that write a gif file based on an existing gif instance'''

    INPUT = 'vampire.gif'
    OUTPUT = 'unittest_clone.gif'
    
    def teststructure(self):
        '''structure: basic structure test, clones gif and encodes lzw'''
        gif = pygif.GifDecoder(open(self.INPUT, 'rb').read())

        enc = pygif.GifEncoder()
        enc.clone(gif)

        image = enc.new_image()
        image.codesize, image.lzwcode = enc.lzw_encode(gif.images[0].pixels)

        enc.write(self.OUTPUT)
        self.assert_(giftopnmtest(self.OUTPUT))

class RenderTests(unittest.TestCase):
    '''Tests that render gifs from scratch or user generated data'''
    
    INPUT = 'vampire.gif'
    OUTPUT = 'unittest_render.gif'
    
    def testgradient(self):
        '''gradient: outputs a 256 color greyscale gradient'''
        enc = pygif.GifEncoder()
        
        enc.header = 'GIF89a'
        enc.ls_width = 256
        enc.ls_height = 50
        
        enc.pallete = [(x, x, x) for x in range(256)]
        enc.global_color_table_size = len(enc.pallete)
        enc.color_table_flag = True
        enc.color_resolution = 7 # 256 colors
        enc.build_flags()
        
        pixels = [x for x in range(256)] * enc.ls_height

        image = enc.new_image()
        image.codesize, image.lzwcode = enc.lzw_encode(pixels)

        enc.write(self.OUTPUT)
        self.assert_(giftopnmtest(self.OUTPUT))


def giftopnmtest(path):
    '''runs giftopnm and returns True if it succeded'''
    return os.system("giftopnm " + path + " > /dev/null 2>&1") == 0

if __name__ == '__main__':
    unittest.main()
