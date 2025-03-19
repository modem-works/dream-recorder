# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# The colorzero color library
#
# Copyright (c) 2016-2021 Dave Jones <dave@waveform.org.uk>
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Defines all conversion functions used by colorzero to convert between the
various color systems implemented. References used in the development of these
routines are as follows:

* `Charles Poynton's Color FAQ`_
* `Bruce Lindbloom's Color Equations`_
* `RGB color space`_ article from Wikipedia
* `SRGB`_ article from Wikipedia
* `YUV`_ article from Wikipedia
* `YIQ`_ article from Wikipedia
* `HSL and HSV`_ article from Wikipedia
* `CIE 1931 color space`_ article from Wikipedia

.. _RGB color space: https://en.wikipedia.org/wiki/RGB_color_space
.. _SRGB: https://en.wikipedia.org/wiki/SRGB
.. _YUV: https://en.wikipedia.org/wiki/YUV
.. _YIQ: https://en.wikipedia.org/wiki/YIQ
.. _HSL and HSV: https://en.wikipedia.org/wiki/HSL_and_HSV
.. _CIE 1931 color space: https://en.wikipedia.org/wiki/CIE_1931_color_space
.. _Charles Poynton's Color FAQ: http://www.poynton.com/notes/colour_and_gamma/ColorFAQ.html
.. _Bruce Lindbloom's Color Equations: https://www.brucelindbloom.com/
"""

import colorsys
from collections import namedtuple
from fractions import Fraction

from .tables import NAMED_COLORS
from .types import RGB, YIQ, YUV, CMY, CMYK, HLS, HSV, XYZ, Luv, Lab

# Lots of the conversion functions use single character parameter names and
# variables internally; this is is normal and in keeping with most of the
# referenced sources
# pylint: disable=invalid-name


# Utility functions and constants ############################################

def clamp_float(v):
    "Clamp *v* to the range 0.0 to 1.0 inclusive"
    return max(0.0, min(1.0, v))


def clamp_bytes(v):
    "Clamp *v* to the range 0 to 255 inclusive"
    return max(0, min(255, v))


def to_srgb(c):
    "Convert a linear RGB value (0..1) to the sRGB color space"
    return 12.92 * c if c <= 0.0031308 else (1.055 * c ** (1 / 2.4) - 0.055)


def from_srgb(c):
    "Convert an RGB value from the sRGB color space to linear RGB"
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def xyz_to_uv(x, y, z):
    "Calculate the U, V values from an XYZ color"
    d = x + 15 * y + 3 * z
    return (0, 0) if d == 0 else (4 * x / d, 9 * y / d)


def matrix_mult(m, n):
    "Generator function that multiplies matrices *m* and *n*"
    return (
        sum(mval * nval for mval, nval in zip(mrow, n))
        for mrow in m
    )


class YUVCoefficients(namedtuple('YUVCoefficients', (
        'Wr', 'Wg', 'Wb',
        'Umax', 'Vmax', 'U', 'V',
        'Rv', 'Gu', 'Gv', 'Bu'))):
    "Represents coefficients for the BT.601 and BT.709 standards."
    def __new__(cls, Umax=0.436, Vmax=0.615, **kwargs):
        try:
            Wr = kwargs['Wr']
            Wb = kwargs['Wb']
        except KeyError as e:
            raise TypeError('YUVCoefficients() missing required keyword '
                            'argument: {e:s}'.format(e=e))
        Wg = (1 - Wr - Wb)
        U = Umax / (1 - Wb)
        V = Vmax / (1 - Wr)
        Rv = (1 - Wr) / Vmax
        Bu = (1 - Wb) / Umax
        Gu = (Wb * (1 - Wb)) / (Umax * Wg)
        Gv = (Wr * (1 - Wr)) / (Vmax * Wg)
        return super(YUVCoefficients, cls).__new__(cls,
                                                   Wr, Wg, Wb,
                                                   Umax, Vmax, U, V,
                                                   Rv, Gu, Gv, Bu)


BT601 = YUVCoefficients(Wr=0.299, Wb=0.114)
BT709 = YUVCoefficients(Wr=0.2126, Wb=0.0722)
SMPTE240M = YUVCoefficients(Wr=0.212, Wb=0.087)
# TODO define some API to use these in Color


# The standard illuminants in the CIE XYZ space
D50 = XYZ(0.966797, 1.0, 0.825188)
D65 = XYZ(0.95047, 1.0, 1.08883)
# TODO define some more of these and figure out some API to use them in Color
# TODO what about standard observers? color temperature?


# Conversion functions #######################################################

def rgb_to_yiq(r, g, b):
    "Convert a linear RGB color to YIQ"
    # Coefficients from Python 3.4+
    y = 0.30 * r + 0.59 * g + 0.11 * b
    i = 0.74 * (r - y) - 0.27 * (b - y)
    q = 0.48 * (r - y) + 0.41 * (b - y)
    return YIQ(y, i, q)


def yiq_to_rgb(y, i, q):
    "Convert a YIQ color to linear RGB"
    # Coefficients from Python 3.4+
    return RGB(
        clamp_float(y + 0.9468822170900693  * i + 0.6235565819861433 * q),
        clamp_float(y - 0.27478764629897834 * i - 0.6356910791873801 * q),
        clamp_float(y - 1.1085450346420322  * i + 1.7090069284064666 * q),
    )


def rgb_to_hls(r, g, b):
    "Convert a linear RGB color to HLS"
    return HLS(*colorsys.rgb_to_hls(r, g, b))


def hls_to_rgb(h, l, s):
    "Convert an HLS color to linear RGB"
    return RGB(*colorsys.hls_to_rgb(h, l, s))


def rgb_to_hsv(r, g, b):
    "Convert a linear RGB color to HSV"
    return HSV(*colorsys.rgb_to_hsv(r, g, b))


def hsv_to_rgb(h, s, v):
    "Convert an HSV color to linear RGB"
    return RGB(*colorsys.hsv_to_rgb(h, s, v))


def rgb_to_rgb_bytes(r, g, b):
    "Convert a linear RGB color to RGB888"
    return RGB(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def rgb_bytes_to_rgb(r, g, b):
    "Convert an RGB888 color to linear RGB"
    return RGB(r / 255, g / 255, b / 255)


def rgb_bytes_to_html(r, g, b):
    "Convert RGB888 to the HTML representation"
    return '#{0:02x}{1:02x}{2:02x}'.format(r, g, b)


def rgb_bytes_to_rgb24(r, g, b):
    "Convert RGB888 to RGB24"
    return (b << 16) | (g << 8) | r


def rgb24_to_rgb_bytes(n):
    "Convert RGB24 to RGB888"
    return RGB(n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF)


def html_to_rgb_bytes(html):
    "Convert the HTML color representation to RGB888"
    if html.startswith('#'):
        try:
            if len(html) == 7:
                return RGB(
                    int(html[1:3], base=16),
                    int(html[3:5], base=16),
                    int(html[5:7], base=16)
                )
            elif len(html) == 4:
                return RGB(
                    int(html[1:2], base=16) * 0x11,
                    int(html[2:3], base=16) * 0x11,
                    int(html[3:4], base=16) * 0x11
                )
        except ValueError:
            pass
    raise ValueError(
        '{:s} is not a valid HTML color specification'.format(html))


def name_to_html(name):
    "Convert a named color to the HTML representation"
    try:
        return NAMED_COLORS[name]
    except KeyError:
        raise ValueError('invalid color name {:s}'.format(name))


def rgb_to_rgb565(r, g, b):
    "Convert linear RGB to RGB565"
    return (
        (int(r * 0xF800) & 0xF800) |
        (int(g * 0x07E0) & 0x07E0) |
        (int(b * 0x001F) & 0x001F)
    )


def rgb565_to_rgb(rgb565):
    "Convert RGB565 to linear RGB"
    r = (rgb565 & 0xF800) / 0xF800
    g = (rgb565 & 0x07E0) / 0x07E0
    b = (rgb565 & 0x001F) / 0x001F
    return RGB(r, g, b)


def rgb_to_yuv(r, g, b, std=BT601):
    """
    Convert linear RGB to Y'CbCr using the specified coefficients (the default
    coefficients are from BT.601)
    """
    y = std.Wr * r + std.Wg * g + std.Wb * b
    return YUV(y, std.U * (b - y), std.V * (r - y))


def yuv_to_rgb(y, u, v, std=BT601):
    """
    Convert Y'CbCr to linear RGB using the specified coefficients (the default
    coefficients are from BT.601)
    """
    return RGB(
        clamp_float(y + std.Rv * v),
        clamp_float(y - std.Gu * u - std.Gv * v),
        clamp_float(y + std.Bu * u),
    )


def rgb_bytes_to_yuv_bytes(r, g, b):
    "Convert RGB888 to YUV444 bytes using studio swing from BT.601"
    # pylint: disable=bad-whitespace
    return YUV(
        (( 66 * r + 129 * g +  25 * b + 128) >> 8) + 16,
        ((-38 * r -  74 * g + 112 * b + 128) >> 8) + 128,
        ((112 * r -  94 * g -  18 * b + 128) >> 8) + 128,
    )


def yuv_bytes_to_rgb_bytes(y, u, v):
    "Convert YUV444 bytes to RGB888 using studio swing from BT.601"
    c = y - 16
    d = u - 128
    e = v - 128
    return RGB(
        clamp_bytes((298 * c + 409 * e + 128) >> 8),
        clamp_bytes((298 * c - 100 * d - 208 * e + 128) >> 8),
        clamp_bytes((298 * c + 516 * d + 128) >> 8),
    )


def rgb_to_cmy(r, g, b):
    "Convert linear RGB to CMY using the subtractive method"
    return CMY(1 - r, 1 - g, 1 - b)


def cmy_to_rgb(c, m, y):
    "Convert CMY to linear RGB using the subtractive method"
    return RGB(1 - c, 1 - m, 1 - y)


def cmy_to_cmyk(c, m, y):
    "Calculate the black component of CMY to convert to CMYK"
    k = min(c, m, y)
    if k == 1.0:
        return CMYK(0.0, 0.0, 0.0, 1.0)
    else:
        d = 1.0 - k
        return CMYK((c - k) / d, (m - k) / d, (y - k) / d, k)


def cmyk_to_cmy(c, m, y, k):
    "Remove the black component from CMYK to yield CMY"
    n = 1 - k
    return CMY(c * n + k, m * n + k, y * n + k)


def rgb_to_xyz(r, g, b):
    """
    Convert linear RGB to CIE XYZ representation. RGB is assumed to be sRGB and
    conversion uses D65 as reference white.
    """
    return XYZ(*matrix_mult(
        ((0.4124564, 0.3575761, 0.1804375),
         (0.2126729, 0.7151522, 0.0721750),
         (0.0193339, 0.1191920, 0.9503041)),
        (from_srgb(r), from_srgb(g), from_srgb(b))
    ))


def xyz_to_rgb(x, y, z):
    """
    Convert CIE XYZ representation to linear RGB. sRGB is used as the output
    color space, and D65 as reference white.
    """
    # pylint: disable=bad-whitespace
    m = matrix_mult(
        (( 3.2404542, -1.5371385, -0.4985314),
         (-0.9692660,  1.8760108,  0.0415560),
         ( 0.0556434, -0.2040259,  1.0572252)),
        (x, y, z)
    )
    return RGB(*(to_srgb(c) for c in m))


def luv_to_xyz(l, u, v, white=D65):
    "Convert CIE L*u*v* to CIE XYZ representation"
    if l == 0:
        return XYZ(0, 0, 0)
    uw, vw = xyz_to_uv(*white)
    u_prime = u / (13 * l) + uw
    v_prime = v / (13 * l) + vw
    y = white.y * (
        l * Fraction(3, 29) ** 3 if l <= 8 else
        ((l + 16) / 116) ** 3
    )
    return XYZ(
        y * (9 * u_prime) / (4 * v_prime),
        y,
        y * (12 - 3 * u_prime - 20 * v_prime) / (4 * v_prime),
    )


def xyz_to_luv(x, y, z, white=D65):
    "Convert CIE XYZ to CIE L*u*v* representation"
    uw, vw = xyz_to_uv(*white)
    u, v = xyz_to_uv(x, y, z)
    K = Fraction(29, 3) ** 3
    e = Fraction(6, 29) ** 3
    y_prime = y / white.y
    L = 116 * y_prime ** Fraction(1, 3) - 16 if y_prime > e else K * y_prime
    return Luv(
        L,
        13 * L * (u - uw),
        13 * L * (v - vw),
    )


def lab_to_xyz(l, a, b, white=D65):
    "Convert CIE L*a*b* to CIE XYZ representation"
    theta = Fraction(6, 29)
    fy = (l + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    xyz = (
        n ** 3 if n > theta else 3 * theta ** 2 * (n - Fraction(4, 29))
        for n in (fx, fy, fz)
    )
    return XYZ(*(n * m for n, m in zip(xyz, white)))


def xyz_to_lab(x, y, z, white=D65):
    "Convert CIE XYZ to CIE L*a*b* representation"
    theta = Fraction(6, 29)
    x, y, z = (n / m for n, m in zip((x, y, z), white))
    fx, fy, fz = (
        t ** Fraction(1, 3) if t > theta ** 3 else
        t / (3 * theta ** 2) + Fraction(4, 29)
        for t in (x, y, z)
    )
    return Lab(116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
