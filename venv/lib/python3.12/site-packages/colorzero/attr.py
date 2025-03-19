# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# The colorzero color library
#
# Copyright (c) 2016-2021 Dave Jones <dave@waveform.org.uk>
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Defines the classes for manipulating the attributes of the :class:`Color`
class through the standard binary operators.
"""

from math import pi


class Red(float):
    """
    Represents the red component of a :class:`Color` for use in
    transformations. Instances of this class can be constructed directly with a
    float value, or by querying the :attr:`Color.red` attribute. Addition,
    subtraction, and multiplication are supported with :class:`Color`
    instances. For example::

        >>> Color.from_rgb(0, 0, 0) + Red(0.5)
        <Color html='#800000' rgb=(0.5, 0, 0)>
        >>> Color('#f00') - Color('#900').red
        <Color html='#660000' rgb=(0.4, 0, 0)>
        >>> (Red(0.1) * Color('red')).red
        Red(0.1)
    """

    def __repr__(self):
        return "Red({:g})".format(self)


class Green(float):
    """
    Represents the green component of a :class:`Color` for use in
    transformations.  Instances of this class can be constructed directly with
    a float value, or by querying the :attr:`Color.green` attribute. Addition,
    subtraction, and multiplication are supported with :class:`Color`
    instances. For example::

        >>> Color(0, 0, 0) + Green(0.1)
        <Color html='#001a00' rgb=(0, 0.1, 0)>
        >>> Color.from_yuv(1, -0.4, -0.6) - Green(1)
        <Color html='#510030' rgb=(0.316098, 0, 0.187156)>
        >>> (Green(0.5) * Color('white')).rgb
        RGB(r=1.0, g=0.5, b=1.0)
    """

    def __repr__(self):
        return "Green({:g})".format(self)


class Blue(float):
    """
    Represents the blue component of a :class:`Color` for use in
    transformations.  Instances of this class can be constructed directly with
    a float value, or by querying the :attr:`Color.blue` attribute. Addition,
    subtraction, and multiplication are supported with :class:`Color`
    instances. For example::

        >>> Color(0, 0, 0) + Blue(0.2)
        <Color html='#000033' rgb=(0, 0, 0.2)>
        >>> Color.from_hls(0.5, 0.5, 1.0) - Blue(1)
        <Color html='#00ff00' rgb=(0, 1, 0)>
        >>> Blue(0.9) * Color('white')
        <Color html='#ffffe6' rgb=(1, 1, 0.9)>
    """

    def __repr__(self):
        return "Blue({:g})".format(self)


class Hue(float):
    """
    Represents the hue of a :class:`Color` for use in transformations.
    Instances of this class can be constructed directly with a float value in
    the range [0.0, 1.0) representing an angle around the `HSL hue wheel`_. As
    this is a circular mapping, 0.0 and 1.0 effectively mean the same thing,
    i.e.  out of range values will be normalized into the range [0.0, 1.0).

    The class can also be constructed with the keyword arguments ``deg`` or
    ``rad`` if you wish to specify the hue value in degrees or radians instead,
    respectively. Instances can also be constructed by querying the
    :attr:`Color.hue` attribute.

    Addition, subtraction, and multiplication are supported with :class:`Color`
    instances. For example::

        >>> Color(1, 0, 0).hls
        HLS(h=0.0, l=0.5, s=1.0)
        >>> (Color(1, 0, 0) + Hue(deg=180)).hls
        HLS(h=0.5, l=0.5, s=1.0)

    Note that whilst multiplication by a :class:`Hue` doesn't make much sense,
    it is still supported. However, the circular nature of a hue value can lead
    to suprising effects. In particular, since 1.0 is equivalent to 0.0 the
    following may be observed::

        >>> (Hue(1.0) * Color.from_hls(0.5, 0.5, 1.0)).hls
        HLS(h=0.0, l=0.5, s=1.0)

    .. _HSL hue wheel: https://en.wikipedia.org/wiki/Hue
    """

    def __new__(cls, n=None, deg=None, rad=None):
        if n is not None:
            return super().__new__(cls, n % 1.0)
        elif deg is not None:
            return super().__new__(cls, (deg / 360.0) % 1.0)
        elif rad is not None:
            return super().__new__(cls, (rad / (2 * pi)) % 1.0)
        else:
            raise ValueError('You must specify a value, or deg or rad')

    def __repr__(self):
        return "Hue(deg={self.deg:g})".format(self=self)

    @property
    def deg(self):
        """
        Returns the hue as a value in degrees with the range 0.0 <= n < 360.0.
        """
        return self * 360.0

    @property
    def rad(self):
        """
        Returns the hue as a value in radians with the range 0.0 <= n < 2π.
        """
        return self * 2 * pi


class Lightness(float):
    """
    Represents the lightness of a :class:`Color` for use in transformations.
    Instances of this class can be constructed directly with a float value, or
    by querying the :attr:`Color.lightness` attribute. Addition, subtraction,
    and multiplication are supported with :class:`Color` instances. For
    example::

        >>> Color(0, 0, 0) + Lightness(0.1)
        <Color html='#1a1a1a' rgb=(0.1, 0.1, 0.1)>
        >>> Color.from_rgb_bytes(0x80, 0x80, 0) - Lightness(0.2)
        <Color html='#1a1a00' rgb=(0.101961, 0.101961, 0)>
        >>> Lightness(0.9) * Color('wheat')
        <Color html='#f0ce8e' rgb=(0.94145, 0.806785, 0.555021)>
    """

    def __repr__(self):
        return "Lightness({:g})".format(self)


class Saturation(float):
    """
    Represents the saturation of a :class:`Color` for use in transformations.
    Instances of this class can be constructed directly with a float value, or
    by querying the :attr:`Color.saturation` attribute. Addition, subtraction,
    and multiplication are supported with :class:`Color` instances. For
    example::

        >>> Color(0.9, 0.9, 0.6) + Saturation(0.1)
        <Color html='#ecec93' rgb=(0.925, 0.925, 0.575)>
        >>> Color('red') - Saturation(1)
        <Color html='#808080' rgb=(0.5, 0.5, 0.5)>
        >>> Saturation(0.5) * Color('wheat')
        <Color html='#e4d9c3' rgb=(0.896078, 0.85098, 0.766667)>
    """

    def __repr__(self):
        return "Saturation({:g})".format(self)


class Luma(float):
    """
    Represents the luma of a :class:`Color` for use in transformations.
    Instances of this class can be constructed directly with a float value, or
    by querying the :attr:`Color.yuv.y` attribute. Addition, subtraction, and
    multiplication are supported with :class:`Color` instances. For example::

        >>> Color(0, 0, 0) + Luma(0.1)
        <Color html='#1a1a1a' rgb=(0.1, 0.1, 0.1)>
        >>> Color('red') * Luma(0.5)
        <Color html='#d90000' rgb=(0.8505, 0, 0)>
    """

    def __repr__(self):
        return "Luma({:g})".format(self)
