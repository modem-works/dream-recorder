# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# The colorzero color library
#
# Copyright (c) 2018 Dave Jones <dave@waveform.org.uk>
#
# SPDX-License-Identifier: BSD-3-Clause

"Defines the various algorithms for :meth:`Color.difference`."

from math import sqrt, atan2, degrees, radians, sin, cos, exp

# Lots of the delta-e functions use single character parameter names and
# variables internally; this is is normal and in keeping with most of the
# referenced sources
# pylint: disable=invalid-name


def euclid(color1, color2):
    """
    Calculates color difference as a simple `Euclidean distance`_ by treating
    the three components as spatial dimensions.

    .. note::

        This function will return considerably different values to the other
        difference functions. In particular, the maximum "difference" will be
        :math:`\\sqrt{3}` which is much smaller than the output of the CIE
        functions.

    .. _Euclidean distance: https://en.wikipedia.org/wiki/Euclidean_distance
    """
    return sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(color1, color2)))


def cie1976(color1, color2):
    """
    Calculates color difference according to the `CIE 1976`_ formula.
    Effectively this is the Euclidean formula, but with CIE L*a*b* components
    instead of RGB.

    .. _CIE 1976: https://en.wikipedia.org/wiki/Color_difference#CIE76
    """
    return sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(color1, color2)))


def cie1994(color1, color2, method):
    """
    Calculates color difference according to the `CIE 1994`_ formula. The
    *method* can be either "cie1994g" for the "graphical" biases, or "cie1994t"
    for the "textile" biases. The CIE1994 is also basically the Euclidean
    formula (with biases) but in CIE L*C*H* space.

    .. _CIE 1994: https://en.wikipedia.org/wiki/Color_difference#CIE94
    """
    C1 = sqrt(color1.a ** 2 + color1.b ** 2)
    C2 = sqrt(color2.a ** 2 + color2.b ** 2)

    dL = color1.l - color2.l
    dC = C1 - C2
    # Don't bother with the sqrt here as due to limited float precision
    # we can wind up with a domain error (because the value is ever so
    # slightly negative - try it with black'n'white for an example), and we're
    # just going to square the result in the final equation anyway
    dH2 = (color1.a - color2.a) ** 2 + (color1.b - color2.b) ** 2 - dC ** 2

    kL, K1, K2 = {
        'cie1994g': (1, 0.045, 0.015),
        'cie1994t': (2, 0.048, 0.014),
    }[method]
    SC = 1 + K1 * C1
    SH = 1 + K2 * C1
    return sqrt(
        (dL / kL) ** 2 +
        (dC / SC) ** 2 +
        (dH2 / SH ** 2)
    )


def cie1994g(color1, color2):
    """
    Calculates color difference according to the `CIE 1994`_ formula with the
    "textile" bias. See :func:`cie1994` for further information.

    .. _CIE 1994: https://en.wikipedia.org/wiki/Color_difference#CIE94
    """
    return cie1994(color1, color2, 'cie1994g')


def cie1994t(color1, color2):
    """
    Calculates color difference according to the `CIE 1994`_ formula with the
    "graphics" bias. See :func:`cie1994` for further information.

    .. _CIE 1994: https://en.wikipedia.org/wiki/Color_difference#CIE94
    """
    return cie1994(color1, color2, 'cie1994t')


def ciede2000(color1, color2):
    """
    Calculates color difference according to the `CIEDE 2000`_ formula. This is
    the most accurate algorithm currently implemented but also the most complex
    and slowest. Like CIE1994 it is largely based in CIE L*C*h* space, but with
    several modifications to account for perceptual uniformity flaws.

    .. _CIEDE 2000: https://en.wikipedia.org/wiki/Color_difference#CIEDE2000
    """
    # See WP article and Sharma 2005 for important implementation notes:
    # http://www.ece.rochester.edu/~gsharma/ciede2000/ciede2000noteCRNA.pdf
    #
    # Yes, there's lots of locals; but this is easiest to understand as it's a
    # near straight translation of the math
    # pylint: disable=too-many-locals

    C_ = (
        sqrt(color1.a ** 2 + color1.b ** 2) +
        sqrt(color2.a ** 2 + color2.b ** 2)
    ) / 2

    G = (1 - sqrt(C_ ** 7 / (C_ ** 7 + 25 ** 7))) / 2
    a1_prime = (1 + G) * color1.a
    a2_prime = (1 + G) * color2.a

    C1_prime = sqrt(a1_prime ** 2 + color1.b ** 2)
    C2_prime = sqrt(a2_prime ** 2 + color2.b ** 2)
    L_ = (color1.l + color2.l) / 2
    C_ = (C1_prime + C2_prime) / 2

    h1 = (
        0.0 if color1.b == a1_prime == 0 else
        degrees(atan2(color1.b, a1_prime)) % 360
    )
    h2 = (
        0.0 if color2.b == a2_prime == 0 else
        degrees(atan2(color2.b, a2_prime)) % 360
    )
    if C1_prime * C2_prime == 0.0:
        dh = 0.0
        h_ = h1 + h2
    elif abs(h1 - h2) <= 180:
        dh = h2 - h1
        h_ = (h1 + h2) / 2
    else:
        if h2 > h1:
            dh = h2 - h1 - 360
        else:
            dh = h2 - h1 + 360
        if h1 + h2 >= 360:
            h_ = (h1 + h2 - 360) / 2
        else:
            h_ = (h1 + h2 + 360) / 2

    dL = color2.l - color1.l
    dC = C2_prime - C1_prime
    dH = 2 * sqrt(C1_prime * C2_prime) * sin(radians(dh / 2))

    T = (
        1 -
        0.17 * cos(radians(h_ - 30)) +
        0.24 * cos(radians(2 * h_)) +
        0.32 * cos(radians(3 * h_ + 6)) -
        0.20 * cos(radians(4 * h_ - 63))
    )
    SL = 1 + (0.015 * (L_ - 50) ** 2) / sqrt(20 + (L_ - 50) ** 2)
    SC = 1 + 0.045 * C_
    SH = 1 + 0.015 * C_ * T
    RT = (
        -2 * sqrt(C_ ** 7 / (C_ ** 7 + 25 ** 7)) *
        sin(radians(60 * exp(-(((h_ - 275) / 25) ** 2))))
    )

    return sqrt(
        (dL / SL) ** 2 +
        (dC / SC) ** 2 +
        (dH / SH) ** 2 +
        RT * (dC / SC) * (dH / SH)
    )
