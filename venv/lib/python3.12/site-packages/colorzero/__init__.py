# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# The colorzero color library
#
# Copyright (c) 2016-2018 Dave Jones <dave@waveform.org.uk>
#
# SPDX-License-Identifier: BSD-3-Clause

"""
The colorzero package defines a number of classes for representation and
manipulation of colors. The primary class of interest to users is
:class:`Color`.  The other classes are used for manipulation of the attributes
on this class and are:

* :class:`Red`
* :class:`Green`
* :class:`Blue`
* :class:`Hue`
* :class:`Lightness`
* :class:`Saturation`
* :class:`Luma`
"""

from .color import Color
from .easings import linear, ease_in, ease_out, ease_in_out
from .deltae import euclid, cie1976, cie1994g, cie1994t, ciede2000
from .attr import Red, Green, Blue, Hue, Lightness, Saturation, Luma
from .types import RGB, HLS, HSV, CMY, CMYK, YUV, YIQ, XYZ, Luv, Lab
from .tables import NAMED_COLORS
