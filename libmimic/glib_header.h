/* This file contains definitions and macro's copied from GLIB.
 *
 * GLIB is Copyright (C) 1995-1997  Peter Mattis, Spencer Kimball and Josh MacDonald
 *
 * GLIB is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * GLIB is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef GLIB_HEADER_H
#define GLIB_HEADER_H

#include <stdlib.h>


/* from glibconfig.h */
typedef signed char gint8;
typedef unsigned char guint8;
typedef signed short gint16;
typedef unsigned short guint16;
typedef signed int gint32;
typedef unsigned int guint32;

typedef signed int gssize;
typedef unsigned int gsize;

/* THIS WILL FAIL ON BIG-ENDIAN SYSTEMS */
#define GUINT16_TO_LE(val)	((guint16) (val))
#define GUINT32_TO_LE(val)	((guint32) (val))

/* from glib/gtypes.h */
typedef char   gchar;
typedef short  gshort;
typedef long   glong;
typedef int    gint;
typedef gint   gboolean;

typedef unsigned char   guchar;
typedef unsigned short  gushort;
typedef unsigned long   gulong;
typedef unsigned int    guint;

typedef float   gfloat;
typedef double  gdouble;

typedef void* gpointer;
typedef const void *gconstpointer;

#define G_LN10  2.3025850929940456840179914546843642076011014886288

#define GUINT16_FROM_LE(val)	(GUINT16_TO_LE (val))
#define GUINT32_FROM_LE(val)	(GUINT32_TO_LE (val))

/* from glib/gmacros.h */
#ifndef	FALSE
#define	FALSE	(0)
#endif

#ifndef	TRUE
#define	TRUE	(!FALSE)
#endif

#undef	MAX
#define MAX(a, b)  (((a) > (b)) ? (a) : (b))

#undef	MIN
#define MIN(a, b)  (((a) < (b)) ? (a) : (b))

#define G_GNUC_MALLOC    			\
  __attribute__((__malloc__))

/* ourselves */
#define g_malloc    malloc
#define g_malloc0   malloc
#define g_free      free

/* from glib/gmem.h */
#define g_new(struct_type, n_structs)		\
    ((struct_type *) g_malloc (((gsize) sizeof (struct_type)) * ((gsize) (n_structs))))
#define g_new0(struct_type, n_structs)		\
    ((struct_type *) g_malloc0 (((gsize) sizeof (struct_type)) * ((gsize) (n_structs))))

#endif /* GLIB_HEADER_H */

