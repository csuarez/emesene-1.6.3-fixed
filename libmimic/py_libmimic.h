/*
 * This file is part of emesene.
 * 
 * Emesene is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *      
 * Emesene is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *      
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 */

#ifndef _LIBMIMIC_PYLIBMIMIC_H
#define _LIBMIMIC_PYLIBMIMIC_H

#include <Python.h>
#include "mimic.h"

#define HEADER_SIZE 24

typedef unsigned char BYTE;
typedef unsigned short WORD;
typedef unsigned int DWORD;

typedef struct MimicDecoder {
	MimCtx* codec;
	unsigned char is_init;
} MimicDecoder;

typedef struct MimicEncoder {
	MimCtx* codec;
	unsigned int num_frames;
} MimicEncoder;

PyMODINIT_FUNC initlibmimic(void);

static PyObject* libmimic_new_decoder(PyObject* self, PyObject* args);
static PyObject* libmimic_new_encoder(PyObject* self, PyObject* args);

static PyObject* libmimic_decode(PyObject* self, PyObject* args);
static PyObject* libmimic_encode(PyObject* self, PyObject* args);

/* method table */
static PyMethodDef LibmimicMethods[] = {
    {"new_decoder", libmimic_new_decoder, METH_VARARGS, "New decoder"},
    {"new_encoder", libmimic_new_encoder, METH_VARARGS, "New encoder"},
    {"decode", libmimic_decode, METH_VARARGS, "Decode a frame"},
    {"encode", libmimic_encode, METH_VARARGS, "Encode a frame"},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

#endif /* _LIBMIMIC_PYLIBMIMIC_H */
