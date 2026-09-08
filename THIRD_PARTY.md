# Third-party boundaries

The MIT license covers this harness's original code, documentation, and original examples. It does not relicense Aseprite, Skia, downloaded dependencies, or supplied reference art.

Aseprite and build dependencies are fetched into ignored `vendor/` directories. Their own license files govern them. Do not include the downloaded source trees or locally compiled application in a harness release. Consult the exact checked-out Aseprite `EULA.txt` and license files before distributing any Aseprite material.

Reference images remain subject to their own terms. Record source, creator (when known), permitted use, and whether AI-generated in the asset brief. Do not assume that making a pixel rendition changes those terms.

Pillow is a Python runtime dependency installed separately by pip. Its own
license applies; it is not vendored into the project. Development tools are also
installed separately and are not relicensed by this repository.

## Aseprite integration and distribution

Reviewed 8 September 2026 against the [Aseprite EULA](https://github.com/aseprite/aseprite/blob/main/EULA.txt),
[official FAQ](https://www.aseprite.org/faq/#licensing--commercial), and
[documented scripting interface](https://www.aseprite.org/docs/scripting/).
This project invokes a separately installed Aseprite through its CLI and Lua API.
It does not distribute the Aseprite application, source checkout, or build dependencies.
The FAQ permits personal and commercial artwork, including artwork made with a
self-compiled version. The EULA restricts redistribution of the application;
users must obtain and use their own copy under its terms. The optional build
recipe is for the user's own local build, not for redistributing Aseprite.
These integration boundaries support publishing this harness separately under MIT;
they are not a legal guarantee or clearance of third-party reference assets.

## Normal-layer compositing notices

The compatibility arithmetic in `pixelart/renderer.py` follows Aseprite's
`rgba_blender_normal` and Pixman's `MUL_UN8`. These components have separate
permissive licenses; the application EULA does not replace their notices.
The following upstream notices are retained for this adaptation.

### Aseprite Document Library (MIT)

Source: [blend_funcs.cpp](https://github.com/aseprite/aseprite/blob/56757b5fc5f00cf5833fb68d5e864ba7f91059a3/src/doc/blend_funcs.cpp).
File attribution: Copyright (c) 2019-2025 Igara Studio S.A.;
Copyright (c) 2001-2017 David Capello.
The accompanying `src/doc/LICENSE.txt` follows:

```text
Copyright (c) 2018-present Igara Studio S.A.
Copyright (c) 2001-2018 David Capello

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

```

### Pixman (MIT)

The accompanying `third_party/pixman/COPYING` follows:

```text
The following is the MIT license, agreed upon by most contributors.
Copyright holders of new code should use this license statement where
possible. They may also add themselves to the list below.

/*
 * Copyright 1987, 1988, 1989, 1998  The Open Group
 * Copyright 1987, 1988, 1989 Digital Equipment Corporation
 * Copyright 1999, 2004, 2008 Keith Packard
 * Copyright 2000 SuSE, Inc.
 * Copyright 2000 Keith Packard, member of The XFree86 Project, Inc.
 * Copyright 2004, 2005, 2007, 2008, 2009, 2010 Red Hat, Inc.
 * Copyright 2004 Nicholas Miell
 * Copyright 2005 Lars Knoll & Zack Rusin, Trolltech
 * Copyright 2005 Trolltech AS
 * Copyright 2007 Luca Barbato
 * Copyright 2008 Aaron Plattner, NVIDIA Corporation
 * Copyright 2008 Rodrigo Kumpera
 * Copyright 2008 André Tupinambá
 * Copyright 2008 Mozilla Corporation
 * Copyright 2008 Frederic Plourde
 * Copyright 2009, Oracle and/or its affiliates. All rights reserved.
 * Copyright 2009, 2010 Nokia Corporation
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice (including the next
 * paragraph) shall be included in all copies or substantial portions of the
 * Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

```
