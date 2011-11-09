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
 * 
 * TODO:
 * - set useful exception messages
 */

#include <Python.h>
#include "py_libmimic.h"

/* init module */
PyMODINIT_FUNC 
initlibmimic(void) 
{
    PyObject* m;
    m = Py_InitModule("libmimic", LibmimicMethods);
}
static void close_decoder(void* ptr) {
    MimicDecoder* decoder;
    decoder = (MimicDecoder*)ptr;
    mimic_close(decoder->codec);
    free(decoder);
}
static PyObject* libmimic_new_decoder(PyObject *self, PyObject *args) {
    MimicDecoder* decoder;

    /* accept no arguments */
    if(!PyArg_ParseTuple(args, ""))
        return NULL;
    
    decoder = (MimicDecoder*)malloc(sizeof(MimicDecoder));
    if(!decoder) {
        PyErr_NoMemory();
        return NULL;
    }
    
    decoder->codec = mimic_open();
    decoder->is_init = 0;

    return PyCObject_FromVoidPtr(decoder, close_decoder);
}
static PyObject* libmimic_new_encoder(PyObject *self, PyObject *args) {
    MimicEncoder* encoder;
    unsigned char arg_resolution;
    MimicResEnum resolution;
    
    /* accept one argument, resolution: 0 = low, 1 = high */
    if(!PyArg_ParseTuple(args, "b", &arg_resolution))
        return NULL;
    
    encoder = (MimicEncoder*)malloc(sizeof(MimicEncoder));
    if(!encoder) {
        PyErr_NoMemory();
        return NULL;
    }
    
    encoder->codec = mimic_open();
    encoder->num_frames = 0;
    
    resolution = arg_resolution ? MIMIC_RES_HIGH : MIMIC_RES_LOW;
    mimic_encoder_init(encoder->codec, resolution);

    return PyCObject_FromVoidPtr(encoder, close_decoder);
}
static PyObject* libmimic_decode(PyObject *self, PyObject *args) {
    MimicDecoder* decoder;
    BYTE* output;
    unsigned int width, height, length;

    /* parameters */
    PyObject* pyobj = NULL;
    BYTE* input;
    int inputsize;

    if(!PyArg_ParseTuple(args, "Os#", &pyobj, &input, &inputsize))
        return NULL;
    
    decoder = PyCObject_AsVoidPtr(pyobj);
    if(!decoder) {
        /* TODO: ERROR */
        return NULL;
    }
    
    if (!decoder->is_init) {
        if (!mimic_decoder_init(decoder->codec, input + HEADER_SIZE)) {
            /* TODO: ERROR */
            return NULL;
        } else {
            decoder->is_init = 1;
        }
    }
    
    mimic_get_property(decoder->codec, "buffer_size", &length);
    mimic_get_property(decoder->codec, "width", &width);
    mimic_get_property(decoder->codec, "height", &height);
    
    output = (BYTE*)malloc(length);
    if(!output) {
        PyErr_NoMemory();
        return NULL;
    }
    
    if (!mimic_decode_frame(decoder->codec, input + HEADER_SIZE, output)) {
        /* TODO: ERROR */
        free(output);
        return NULL;
    }
    
    PyObject* val = Py_BuildValue("iis#", width, height, output, length);
    free(output);
    return val;
}

static PyObject* libmimic_encode(PyObject *self, PyObject *args) {
    MimicEncoder* encoder;
    BYTE* output;
    int length, width, height;

    /* parameters */
    PyObject* pyobj = NULL;
    BYTE* input;
    int inputsize;

    if(!PyArg_ParseTuple(args, "Os#", &pyobj, &input, &inputsize))
        return NULL;
    
    encoder = PyCObject_AsVoidPtr(pyobj);
    if(!encoder) {
        /* TODO: ERROR */
        return NULL;
    }
    
    mimic_get_property(encoder->codec, "buffer_size", &length);
    
    output = (BYTE*)malloc(length * 3);
    if(!output) {
        PyErr_NoMemory();
        return NULL;
    }
    
    if (!mimic_encode_frame(encoder->codec, input, output, &length, 
            encoder->num_frames % 10 == 0)) {
        /* TODO: ERROR */
        free(output);
        return NULL;
    }
    
    encoder->num_frames++;
    
    mimic_get_property(encoder->codec, "width", &width);
    mimic_get_property(encoder->codec, "height", &height);
    PyObject* val = Py_BuildValue("s#ii", output, length, width, height);
    free(output);
    
    return val;
}

