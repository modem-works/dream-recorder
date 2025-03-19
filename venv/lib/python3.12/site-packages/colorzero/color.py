# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# The colorzero color library
#
# Copyright (c) 2016-2021 Dave Jones <dave@waveform.org.uk>
#
# SPDX-License-Identifier: BSD-3-Clause

"Defines the main :class:`Color` class of the package."

import re

from . import conversions as cv, types, attr, deltae, tables, easings

# Lots of the methods below use single character parameter names (r for red, y
# for luma, etc.); this is is normal and in keeping with most of the referenced
# sources
# pylint: disable=invalid-name


class Color(types.RGB):
    """
    The Color class is a tuple which represents a color as linear red, green,
    and blue components.

    The class has a flexible constructor which allows you to create an instance
    from any built-in color system. There are also explicit constructors for
    every known system that can convert (directly or indirectly) to linear RGB.
    For example, an instance of :class:`Color` can be constructed in any of the
    following ways::

        >>> Color('#f00')
        <Color html='#ff0000' rgb=(1, 0, 0)>
        >>> Color('green')
        <Color html='#008000' rgb=(0.0, 0.501961, 0.0)>
        >>> Color(0, 0, 1)
        <Color html='#0000ff' rgb=(0, 0, 1)>
        >>> Color(h=0, s=1, v=0.5)
        <Color html='#800000' rgb=(0.5, 0, 0)>
        >>> Color(y=0.4, u=-0.05, v=0.615)
        <Color html='#ff104c' rgb=(1, 0.0626644, 0.298394)>

    The specific forms that the default constructor will accept are enumerated
    below:

    .. tabularcolumns:: |p{60mm}|p{70mm}|

    +------------------------------+------------------------------------------+
    | Style                        | Description                              |
    +==============================+==========================================+
    | Single scalar parameter      | Equivalent to calling                    |
    |                              | :meth:`Color.from_string`, or            |
    |                              | :meth:`Color.from_rgb24`.                |
    +------------------------------+------------------------------------------+
    | Three positional parameters  | Equivalent to calling                    |
    | or a 3-tuple with no field   | :meth:`Color.from_rgb` if all three      |
    | names                        | parameters are between 0.0 and 1.0, or   |
    |                              | :meth:`Color.from_rgb_bytes` otherwise.  |
    +------------------------------+                                          |
    | Three named parameters, or a |                                          |
    | 3-tuple with fields          |                                          |
    | "r", "g", "b"                |                                          |
    +------------------------------+                                          |
    | Three named parameters, or a |                                          |
    | 3-tuple with fields          |                                          |
    | "red", "green", "blue"       |                                          |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_yuv` if "y" is between |
    | "y", "u", "v"                | 0.0 and 1.0, "u" is between -0.436 and   |
    |                              | 0.436, and "v" is between -0.615 and     |
    |                              | 0.615, or :meth:`Color.from_yuv_bytes`   |
    |                              | otherwise.                               |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_yiq`.                  |
    | "y", "i", "q"                |                                          |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_hls`.                  |
    | "h", "l", "s"                |                                          |
    +------------------------------+                                          |
    | Three named parameters, or a |                                          |
    | 3-tuple with fields          |                                          |
    | "hue", "lightness",          |                                          |
    | "saturation"                 |                                          |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_hsv`                   |
    | "h", "s", "v"                |                                          |
    +------------------------------+                                          |
    | Three named parameters, or a |                                          |
    | 3-tuple with fields          |                                          |
    | "hue", "saturation", "value" |                                          |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_xyz`                   |
    | "x", "y", "z"                |                                          |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_lab`                   |
    | "l", "a", "b"                |                                          |
    +------------------------------+------------------------------------------+
    | Three named parameters, or a | Equivalent to calling                    |
    | 3-tuple with fields          | :meth:`Color.from_luv`                   |
    | "l", "u", "v"                |                                          |
    +------------------------------+------------------------------------------+

    If the constructor parameters do not conform to any of the variants in the
    table above, a :exc:`ValueError` will be raised.

    Internally, the color is *always* represented as 3 :class:`float` values
    corresponding to the red, green, and blue components of the color. These
    values take a value from 0.0 to 1.0 (least to full intensity). The class
    provides several attributes which can be used to convert one color system
    into another::

        >>> Color('#f00').hls
        HLS(h=0.0, l=0.5, s=1.0)
        >>> Color.from_string('green').hue
        Hue(deg=120.0)
        >>> Color.from_rgb_bytes(0, 0, 255).yuv
        YUV(y=0.114, u=0.436, v=-0.10001426533523537)

    As :class:`Color` derives from tuple, instances are immutable. While this
    provides the advantage that they can be used in a :class:`set` or as keys
    of a :class:`dict`, it does mean that colors themselves cannot be
    *directly* manipulated (e.g. by setting the red component).

    However, several auxilliary classes in the module provide the ability to
    perform simple transformations of colors via operators which produce a new
    :class:`Color` instance. For example, you can add, subtract, and multiply
    colors directly::

        >>> Color('red') + Color('blue')
        <Color html='#ff00ff' rgb=(1, 0, 1)>
        >>> Color('magenta') - Color('red')
        <Color html='#0000ff' rgb=(0, 0, 1)>

    Values are clipped to ensure the resulting color is still valid::

        >>> Color('#ff00ff') + Color('#ff0000')
        <Color html='#ff00ff' rgb=(1, 0, 1)>

    You can wrap numbers in constructors like :class:`Red` (or obtain elements
    of existing colors), then add, subtract, or multiply them with a
    :class:`Color`::

        >>> Color('red') - Red(0.5)
        <Color html='#800000' rgb=(0.5, 0, 0)>
        >>> Color('green') + Color('grey').red
        <Color html='#808000' rgb=(0.501961, 0.501961, 0)>

    You can even manipulate non-primary attributes like hue, saturation, and
    lightness with standard addition, subtraction or multiplication operators::

        >>> Color.from_hls(0.5, 0.5, 1.0)
        <Color html='#00ffff' rgb=(0, 1, 1)>
        >>> Color.from_hls(0.5, 0.5, 1.0) * Lightness(0.8)
        <Color html='#00cccc' rgb=(0, 0.8, 0.8)>
        >>> (Color.from_hls(0.5, 0.5, 1.0) * Lightness(0.8)).hls
        HLS(h=0.5, l=0.4, s=1.0)

    In the last example above, a :class:`Color` instance is constructed from
    HLS (hue, lightness, saturation) values with a lightness of 0.5. This is
    multiplied by a :class:`Lightness` a value of 0.8 which constructs a new
    :class:`Color` with the same hue and saturation, but a lightness of 0.4
    (0.8 × 0.5).

    If an instance is converted to a string (with :func:`str`) it will return a
    string containing the 7-character HTML code for the color (e.g. "#ff0000"
    for red). As can be seen in the examples above, a similar representation is
    included for the output of :func:`repr`. The output of :func:`repr` can
    be customized by assigning values to :attr:`Color.repr_style`.

    .. _RGB: https://en.wikipedia.org/wiki/RGB_color_space
    .. _Y'UV: https://en.wikipedia.org/wiki/YUV
    .. _Y'IQ: https://en.wikipedia.org/wiki/YIQ
    .. _HLS: https://en.wikipedia.org/wiki/HSL_and_HSV
    .. _HSV: https://en.wikipedia.org/wiki/HSL_and_HSV

    .. attribute:: red

        Return the red value as a :class:`Red` instance

    .. attribute:: green

        Return the green value as a :class:`Green` instance

    .. attribute:: blue

        Return the blue value as a :class:`Blue` instance

    .. attribute:: repr_style

        Specifies the style of output returned when using :func:`repr` against
        a :class:`Color` instance. This is an attribute of the class, not of
        instances. For example::

            >>> Color('#f00')
            <Color html='#ff0000' rgb=(1, 0, 0)>
            >>> Color.repr_style = 'html'
            >>> Color('#f00')
            Color('#ff0000')

        The following values are valid:

        * 'default' - The style shown above
        * 'term16m' - Similar to the default style, but instead of the HTML
          style being included, a swatch previewing the color is output. Note
          that the terminal must support `24-bit color ANSI codes`_ for this to
          work.
        * 'term256' - Similar to 'termtrue', but uses the closest color that
          can be found in the standard 256-color xterm palette. Note that the
          terminal must support `8-bit color ANSI codes`_ for this to work.
        * 'html' - Outputs a valid :class:`Color` constructor using the HTML
          style, e.g. ``Color('#ff99bb')``
        * 'rgb' - Outputs a valid :class:`Color` constructor using the floating
          point RGB values, e.g. ``Color(1, 0.25, 0)``
    """
    # pylint: disable=too-many-public-methods

    __slots__ = ()

    repr_style = 'default'

    def __new__(cls, *args, **kwargs):
        def from_rgb(r, g, b):
            "Determine whether bytes or floats are being passed for RGB"
            if 0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0:
                return cls.from_rgb(r, g, b)
            else:
                return cls.from_rgb_bytes(r, g, b)

        def from_yuv(y, u, v):
            "Determine whether bytes or floats are being passed for YUV"
            if (
                    0.0 <= y <= 1.0 and
                    abs(u) <= cv.BT601.Umax and
                    abs(v) <= cv.BT601.Vmax):
                return cls.from_yuv(y, u, v)
            else:
                return cls.from_yuv_bytes(y, u, v)

        if kwargs:
            try:
                # Yes, lambdas are fine here
                # pylint: disable=unnecessary-lambda
                return {
                    frozenset('rgb'): from_rgb,
                    frozenset('yuv'): from_yuv,
                    frozenset('yiq'): cls.from_yiq,
                    frozenset('hls'): cls.from_hls,
                    frozenset('hsv'): cls.from_hsv,
                    frozenset('xyz'): cls.from_xyz,
                    frozenset('lab'): cls.from_lab,
                    frozenset('luv'): cls.from_luv,
                    frozenset('cmy'): cls.from_cmy,
                    frozenset('cmyk'): cls.from_cmyk,
                    frozenset(('red', 'green', 'blue')):
                        lambda red, green, blue:
                        from_rgb(red, green, blue),
                    frozenset(('cyan', 'magenta', 'yellow')):
                        lambda cyan, magenta, yellow:
                        cls.from_cmy(cyan, magenta, yellow),
                    frozenset(('cyan', 'magenta', 'yellow', 'black')):
                        lambda cyan, magenta, yellow, black:
                        cls.from_cmyk(cyan, magenta, yellow, black),
                    frozenset(('hue', 'lightness', 'saturation')):
                        lambda hue, lightness, saturation:
                        cls.from_hls(hue, lightness, saturation),
                    frozenset(('hue', 'saturation', 'value')):
                        lambda hue, saturation, value:
                        cls.from_hsv(hue, saturation, value),
                    }[frozenset(kwargs.keys())](**kwargs)
            except KeyError:
                pass
        else:
            if len(args) == 1:
                if isinstance(args[0], bytes):
                    spec = args[0].decode('ascii')
                else:
                    spec = args[0]
                if isinstance(spec, str):
                    return cls.from_string(spec)
                elif isinstance(spec, tuple):
                    try:
                        return cls(**spec._asdict())
                    except AttributeError:
                        if len(spec) == 3:
                            return from_rgb(*spec)
                elif isinstance(spec, int):
                    return cls.from_rgb24(spec)
            elif len(args) == 3:
                r, g, b = args
                return from_rgb(r, g, b)
        raise ValueError('Unable to construct Color from provided arguments')

    @classmethod
    def from_string(cls, s):
        """
        Construct a :class:`Color` from a 4 or 7 character CSS-like
        representation (e.g. "#f00" or "#ff0000" for red), or from one of the
        named colors (e.g. "green" or "wheat") from the `CSS standard`_. Any
        other string format will result in a :exc:`ValueError`.

        .. _CSS standard: http://www.w3.org/TR/css3-color/#svg-color
        """
        if s[:1] != '#':
            s = cv.name_to_html(s)
        return cls.from_rgb_bytes(*cv.html_to_rgb_bytes(s))

    @classmethod
    def from_rgb(cls, r, g, b):
        """
        Construct a :class:`Color` from three linear `RGB`_ float values
        between 0.0 and 1.0.
        """
        return super().__new__(cls,
                               cv.clamp_float(r),
                               cv.clamp_float(g),
                               cv.clamp_float(b))

    @classmethod
    def from_rgb24(cls, n):
        """
        Construct a :class:`Color` from an unsigned 24-bit integer number
        of the form 0x00BBGGRR.
        """
        return cls.from_rgb_bytes(*cv.rgb24_to_rgb_bytes(n))

    @classmethod
    def from_rgb565(cls, n):
        """
        Construct a :class:`Color` from an unsigned 16-bit integer number
        in RGB565 format.
        """
        return cls.from_rgb(*cv.rgb565_to_rgb(n))

    @classmethod
    def from_rgb_bytes(cls, r, g, b):
        """
        Construct a :class:`Color` from three `RGB`_ byte values between 0 and
        255.

        .. _RGB: https://en.wikipedia.org/wiki/RGB_color_space
        """
        return cls.from_rgb(*cv.rgb_bytes_to_rgb(r, g, b))

    @classmethod
    def from_yuv(cls, y, u, v):
        """
        Construct a :class:`Color` from three `Y'UV`_ float values. The Y value
        may be between 0.0 and 1.0. U may be between -0.436 and 0.436, while
        V may be between -0.615 and 0.615.

        .. _Y'UV: https://en.wikipedia.org/wiki/YUV
        """
        return cls.from_rgb(*cv.yuv_to_rgb(y, u, v))

    @classmethod
    def from_yuv_bytes(cls, y, u, v):
        """
        Construct a :class:`Color` from three `Y'UV`_ byte values between 0 and
        255. The U and V values are biased by 128 to prevent negative values as
        is typical in video applications. The Y value is biased by 16 for the
        same purpose.

        .. _Y'UV: https://en.wikipedia.org/wiki/YUV
        """
        return cls.from_rgb_bytes(*cv.yuv_bytes_to_rgb_bytes(y, u, v))

    @classmethod
    def from_yiq(cls, y, i, q):
        """
        Construct a :class:`Color` from three `Y'IQ`_ float values. Y' can be
        between 0.0 and 1.0, while I and Q can be between -1.0 and 1.0.

        .. _Y'IQ: https://en.wikipedia.org/wiki/YIQ
        """
        return cls.from_rgb(*cv.yiq_to_rgb(y, i, q))

    @classmethod
    def from_hls(cls, h, l, s):
        """
        Construct a :class:`Color` from `HLS`_ (hue, lightness, saturation)
        floats between 0.0 and 1.0.

        .. _HLS: https://en.wikipedia.org/wiki/HSL_and_HSV
        """
        return cls.from_rgb(*cv.hls_to_rgb(h, l, s))

    @classmethod
    def from_hsv(cls, h, s, v):
        """
        Construct a :class:`Color` from `HSV`_ (hue, saturation, value) floats
        between 0.0 and 1.0.

        .. _HSV: https://en.wikipedia.org/wiki/HSL_and_HSV
        """
        return cls.from_rgb(*cv.hsv_to_rgb(h, s, v))

    @classmethod
    def from_cmy(cls, c, m, y):
        """
        Construct a :class:`Color` from `CMY`_ (cyan, magenta, yellow) floats
        between 0.0 and 1.0.

        .. note::

            This conversion uses the basic subtractive method which is not
            accurate for color reproduction on print devices. See the `Color
            FAQ`_ for more information.

        .. _Color FAQ: http://poynton.ca/notes/colour_and_gamma/ColorFAQ.html#RTFToC24
        .. _CMY: https://en.wikipedia.org/wiki/CMYK_color_model
        """
        return cls.from_rgb(*cv.cmy_to_rgb(c, m, y))

    @classmethod
    def from_cmyk(cls, c, m, y, k):
        """
        Construct a :class:`Color` from `CMYK`_ (cyan, magenta, yellow, black)
        floats between 0.0 and 1.0.

        .. note::

            This conversion uses the basic subtractive method which is not
            accurate for color reproduction on print devices. See the `Color
            FAQ`_ for more information.

        .. _Color FAQ: http://poynton.ca/notes/colour_and_gamma/ColorFAQ.html#RTFToC24
        .. _CMYK: https://en.wikipedia.org/wiki/CMYK_color_model
        """
        return cls.from_cmy(*cv.cmyk_to_cmy(c, m, y, k))

    @classmethod
    def from_xyz(cls, x, y, z):
        """
        Construct a :class:`Color` from (X, Y, Z) float values representing
        a color in the `CIE 1931 color space`_. The conversion assumes the
        sRGB working space with reference white D65.

        .. _CIE 1931 color space: https://en.wikipedia.org/wiki/CIE_1931_color_space
        """
        return cls.from_rgb(*cv.xyz_to_rgb(x, y, z))

    @classmethod
    def from_lab(cls, l, a, b):
        """
        Construct a :class:`Color` from (L*, a*, b*) float values representing
        a color in the `CIE Lab color space`_. The conversion assumes the
        sRGB working space with reference white D65.

        .. _CIE Lab color space: https://en.wikipedia.org/wiki/Lab_color_space
        """
        return cls.from_xyz(*cv.lab_to_xyz(l, a, b))

    @classmethod
    def from_luv(cls, l, u, v):
        """
        Construct a :class:`Color` from (L*, u*, v*) float values representing
        a color in the `CIE Luv color space`_. The conversion assumes the sRGB
        working space with reference white D65.

        .. _CIE Luv color space: https://en.wikipedia.org/wiki/CIELUV
        """
        return cls.from_xyz(*cv.luv_to_xyz(l, u, v))

    def __add__(self, other):
        if isinstance(other, types.RGB):
            return Color.from_rgb(self.r + other.r,
                                  self.g + other.g,
                                  self.b + other.b)
        elif isinstance(other, (attr.Red, attr.Green, attr.Blue)):
            r, g, b = self
            return Color.from_rgb(
                r + other if isinstance(other, attr.Red) else r,
                g + other if isinstance(other, attr.Green) else g,
                b + other if isinstance(other, attr.Blue) else b,
            )
        elif isinstance(other, (attr.Hue, attr.Lightness, attr.Saturation)):
            h, l, s = self.hls
            return Color.from_hls(
                h + other if isinstance(other, attr.Hue) else h,
                l + other if isinstance(other, attr.Lightness) else l,
                s + other if isinstance(other, attr.Saturation) else s,
            )
        elif isinstance(other, attr.Luma):
            y, u, v = self.yuv
            return Color.from_yuv(y + other, u, v)
        return NotImplemented

    def __radd__(self, other):
        # Addition is commutative
        if isinstance(other, (types.RGB,
                              attr.Red, attr.Green, attr.Blue,
                              attr.Hue, attr.Lightness, attr.Saturation,
                              attr.Luma)):
            return self.__add__(other)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, types.RGB):
            return Color.from_rgb(self.r - other.r,
                                  self.g - other.g,
                                  self.b - other.b)
        elif isinstance(other, (attr.Red, attr.Green, attr.Blue)):
            r, g, b = self.rgb
            return Color.from_rgb(
                r - other if isinstance(other, attr.Red) else r,
                g - other if isinstance(other, attr.Green) else g,
                b - other if isinstance(other, attr.Blue) else b,
            )
        elif isinstance(other, (attr.Hue, attr.Lightness, attr.Saturation)):
            h, l, s = self.hls
            return Color.from_hls(
                h - other if isinstance(other, attr.Hue) else h,
                l - other if isinstance(other, attr.Lightness) else l,
                s - other if isinstance(other, attr.Saturation) else s,
            )
        elif isinstance(other, attr.Luma):
            y, u, v = self.yuv
            return Color.from_yuv(y - other, u, v)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (attr.Red, attr.Green, attr.Blue)):
            r, g, b = self.rgb
            return Color.from_rgb(
                other - r if isinstance(other, attr.Red) else 0.0,
                other - g if isinstance(other, attr.Green) else 0.0,
                other - b if isinstance(other, attr.Blue) else 0.0,
            )
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, types.RGB):
            return Color.from_rgb(self.r * other.r,
                                  self.g * other.g,
                                  self.b * other.b)
        elif isinstance(other, (attr.Red, attr.Green, attr.Blue)):
            r, g, b = self
            return Color.from_rgb(
                r * other if isinstance(other, attr.Red) else r,
                g * other if isinstance(other, attr.Green) else g,
                b * other if isinstance(other, attr.Blue) else b,
            )
        elif isinstance(other, (attr.Hue, attr.Lightness, attr.Saturation)):
            h, l, s = self.hls
            return Color.from_hls(
                h * other if isinstance(other, attr.Hue) else h,
                l * other if isinstance(other, attr.Lightness) else l,
                s * other if isinstance(other, attr.Saturation) else s,
            )
        elif isinstance(other, attr.Luma):
            y, u, v = self.yuv
            return Color.from_yuv(y * other, u, v)
        return NotImplemented

    def __rmul__(self, other):
        # Multiplication is commutative
        if isinstance(other, (types.RGB,
                              attr.Red, attr.Green, attr.Blue,
                              attr.Hue, attr.Lightness, attr.Saturation,
                              attr.Luma)):
            return self.__mul__(other)
        return NotImplemented

    _format_re = re.compile(
        r'^('
        r'(?P<html>html)|'
        r'(?P<css>css(?P<cssfmt>rgb|hsl)?)|'
        r'(?P<back>[fb])?(?P<term>0|8|256|16[mM])?'
        r')$')
    def __format__(self, format_spec):
        m = Color._format_re.match(format_spec)
        if not m:
            raise ValueError(
                'Invalid format {:r} for Color'.format(format_spec))
        if m.group('html'):
            return self.html
        elif m.group('css'):
            return self._format_css(m.group('cssfmt'))
        else:
            return self._format_term(m.group('back'), m.group('term'))

    def _format_css(self, cssfmt):
        return {
            None:  lambda self: 'rgb({0:d}, {1:d}, {2:d})'.format(
                *self.rgb_bytes),
            'rgb': lambda self: 'rgb({0:d}, {1:d}, {2:d})'.format(
                *self.rgb_bytes),
            'hsl': lambda self: 'hsl({0:g}deg, {1:g}%, {2:g}%)'.format(
                self.hls.hue.deg, self.hls.saturation * 100,
                self.hls.lightness * 100),
        }[cssfmt](self)

    def _format_term(self, back, term):
        if term == '0':
            args = ({
                None: 0,
                'f':  39,
                'b':  49,
            }[back],)
        elif term in (None, '8'):
            table = tables.DOS_COLORS
            if back == 'b':
                code = 40
                table = {
                    k: (bold, index)
                    for k, (bold, index) in table.items()
                    if not bold
                }
            else:
                code = 30
            try:
                bold, index = table[self.rgb_bytes]
            except KeyError:
                bold, index = sorted(
                    (self.difference(Color.from_rgb_bytes(*color)), bold, index)
                    for color, (bold, index) in table.items()
                )[0][1:]
            args = (1,) if bold else ()
            args += (code + index,)
        elif term == '256':
            code = 48 if back == 'b' else 38
            try:
                index = tables.XTERM_COLORS[self.rgb_bytes]
            except KeyError:
                index = sorted(
                    (self.difference(Color.from_rgb_bytes(*color)), index)
                    for color, index in tables.XTERM_COLORS.items()
                )[0][1]
            args = (48 if back == 'b' else 38, 5, index)
        elif term.lower() == '16m':
            args = (48 if back == 'b' else 38, 2) + self.rgb_bytes
        else:
            assert False  # pragma: no cover
        return '\x1b[' + ';'.join(str(i) for i in args) + 'm'

    def __str__(self):
        return self.html

    def __repr__(self):
        try:
            return {
                'default': '<Color html={self.html!r} '
                           'rgb=({self.r:g}, {self.g:g}, {self.b:g})>',
                'term16m': '<Color {self:16m}###{self:0} '
                           'rgb=({self.r:g}, {self.g:g}, {self.b:g})>',
                'term256': '<Color {self:256}###{self:0} '
                           'rgb=({self.r:g}, {self.g:g}, {self.b:g})>',
                'html':    'Color({self.html!r})',
                'rgb':     'Color({self.r:g}, {self.g:g}, {self.b:g})',
            }[Color.repr_style].format(self=self)
        except KeyError:
            raise ValueError(
                'invalid repr_style value: {}'.format(Color.repr_style))

    @property
    def html(self):
        """
        Returns the color as a string in HTML #RRGGBB format.
        """
        return cv.rgb_bytes_to_html(*self.rgb_bytes)

    @property
    def rgb(self):
        """
        Return a simple 3-tuple of (r, g, b) float values in the range 0.0 <= n
        <= 1.0.

        .. note::

            The :class:`Color` class can already be treated as such a 3-tuple
            but for the cases where you want a straight
            :func:`~collections.namedtuple` this property is available.
        """
        return types.RGB(*self)

    @property
    def rgb565(self):
        """
        Returns an unsigned 16-bit integer number representing the color in
        the RGB565 encoding.
        """
        return cv.rgb_to_rgb565(*self)

    @property
    def rgb_bytes(self):
        """
        Returns a 3-tuple of (red, green, blue) byte values.
        """
        return cv.rgb_to_rgb_bytes(*self)

    @property
    def yuv(self):
        """
        Returns a 3-tuple of (y, u, v) float values; Y values can be between
        0.0 and 1.0, U values are between -0.436 and 0.436, and V values are
        between -0.615 and 0.615.
        """
        return cv.rgb_to_yuv(*self)

    @property
    def yuv_bytes(self):
        """
        Returns a 3-tuple of (y, u, v) byte values. Y values are biased by 16
        in the result to prevent negatives. U and V values are biased by 128
        for the same purpose.
        """
        return cv.rgb_bytes_to_yuv_bytes(*self.rgb_bytes)

    @property
    def yiq(self):
        """
        Returns a 3-tuple of (y, i, q) float values; y values can be between
        0.0 and 1.0, whilst i and q values can be between -1.0 and 1.0.
        """
        return cv.rgb_to_yiq(*self)

    @property
    def xyz(self):
        """
        Returns a 3-tuple of (X, Y, Z) float values representing the color in
        the `CIE 1931 color space`_. The conversion assumes the sRGB working
        space, with reference white D65.

        .. _CIE 1931 color space: https://en.wikipedia.org/wiki/CIE_1931_color_space
        """
        return cv.rgb_to_xyz(*self)

    @property
    def lab(self):
        """
        Returns a 3-tuple of (L*, a*, b*) float values representing the color
        in the `CIE Lab color space`_ with the `D65 standard illuminant`_.

        .. _CIE Lab color space: https://en.wikipedia.org/wiki/Lab_color_space
        .. _D65 standard illuminant: https://en.wikipedia.org/wiki/Illuminant_D65
        """
        return cv.xyz_to_lab(*self.xyz)

    @property
    def luv(self):
        """
        Returns a 3-tuple of (L*, u*, v*) float values representing the color
        in the `CIE Luv color space`_ with the `D65 standard illuminant`_.

        .. _CIE Luv color space: https://en.wikipedia.org/wiki/CIELUV
        """
        return cv.xyz_to_luv(*self.xyz)

    @property
    def hls(self):
        """
        Returns a 3-tuple of (hue, lightness, saturation) float values (between
        0.0 and 1.0).
        """
        return cv.rgb_to_hls(*self)

    @property
    def hsv(self):
        """
        Returns a 3-tuple of (hue, saturation, value) float values (between 0.0
        and 1.0).
        """
        return cv.rgb_to_hsv(*self)

    @property
    def cmy(self):
        """
        Returns a 3-tuple of (cyan, magenta, yellow) float values (between 0.0
        and 1.0).

        .. note::

            This conversion uses the basic subtractive method which is not
            accurate for color reproduction on print devices. See the `Color
            FAQ`_ for more information.

        .. _Color FAQ: http://poynton.ca/notes/colour_and_gamma/ColorFAQ.html#RTFToC24
        """
        return cv.rgb_to_cmy(*self)

    @property
    def cmyk(self):
        """
        Returns a 4-tuple of (cyan, magenta, yellow, black) float values
        (between 0.0 and 1.0).

        .. note::

            This conversion uses the basic subtractive method which is not
            accurate for color reproduction on print devices. See the `Color
            FAQ`_ for more information.

        .. _Color FAQ: http://poynton.ca/notes/colour_and_gamma/ColorFAQ.html#RTFToC24
        """
        return cv.cmy_to_cmyk(*self.cmy)

    @property
    def hue(self):
        """
        Returns the hue of the color as a :class:`Hue` instance which can be
        used in operations with other :class:`Color` instances.
        """
        return attr.Hue(self.hls[0])

    @property
    def lightness(self):
        """
        Returns the lightness of the color as a :class:`Lightness` instance
        which can be used in operations with other :class:`Color` instances.
        """
        return attr.Lightness(self.hls[1])

    @property
    def saturation(self):
        """
        Returns the saturation of the color as a :class:`Saturation` instance
        which can be used in operations with other :class:`Color` instances.
        """
        return attr.Saturation(self.hls[2])

    @property
    def luma(self):
        """
        Returns the `luma`_ of the color as a :class:`Luma` instance which can
        be used in operations with other :class:`Color` instances.

        .. _luma: https://en.wikipedia.org/wiki/Luma_(video)
        """
        return attr.Luma(self.yuv[0])

    def difference(self, other, method='euclid'):
        """
        Determines the difference between this color and *other* using the
        specified *method*.

        :param Color other:
            The color to compare this color to.

        :param str method:
            The algorithm to use in the comparison. Valid values are:

            * 'euclid' - This is the default method. Calculate the `Euclidian
              distance`_. This is by far the fastest method, but also the least
              accurate in terms of human perception.
            * 'cie1976' - Use the `CIE 1976`_ formula for calculating the
              difference between two colors in CIE Lab space.
            * 'cie1994g' - Use the `CIE 1994`_ formula with the "graphic arts"
              bias for calculating the difference.
            * 'cie1994t' - Use the `CIE 1994`_ forumula with the "textiles"
              bias for calculating the difference.
            * 'ciede2000' - Use the `CIEDE 2000`_ formula for calculating the
              difference.

        :returns:
            A :class:`float` indicating how different the two colors are. Note
            that the Euclidian distance will be significantly different to the
            other calculations; effectively this just measures the distance
            between the two colors by treating them as coordinates in a three
            dimensional Euclidian space. All other methods are means of
            calculating a `Delta E`_ value in which 2.3 is considered a
            `just-noticeable difference`_ (JND).

        For example::

            >>> Color('red').difference(Color('red'))
            0.0
            >>> Color('red').difference(Color('red'), method='cie1976')
            0.0
            >>> Color('red').difference(Color('#900'))
            0.4
            >>> Color('red').difference(Color('#900'), method='cie1976')
            40.17063087142142
            >>> Color('red').difference(Color('#900'), method='ciede2000')
            21.078146289272155
            >>> Color('red').difference(Color('blue'))
            1.4142135623730951
            >>> Color('red').difference(Color('blue'), method='cie1976')
            176.31403908880046

        .. note::

            Instead of using this method, you may wish to simply use the
            various difference functions (:func:`euclid`, :func:`cie1976`,
            etc.) directly.

        .. _Delta E: https://en.wikipedia.org/wiki/Color_difference
        .. _just-noticeable difference: https://en.wikipedia.org/wiki/Just-noticeable_difference
        .. _Euclidian distance: https://en.wikipedia.org/wiki/Euclidean_distance
        .. _CIE 1976: https://en.wikipedia.org/wiki/Color_difference#CIE76
        .. _CIE 1994: https://en.wikipedia.org/wiki/Color_difference#CIE94
        .. _CIEDE 2000: https://en.wikipedia.org/wiki/Color_difference#CIEDE2000
        """
        if isinstance(method, bytes):
            method = method.decode('ascii')
        try:
            fn = getattr(deltae, method)
        except AttributeError:
            raise ValueError('invalid method: {}'.format(method))
        else:
            if method.startswith('cie'):
                return fn(self.lab, other.lab)
            else:
                return fn(self, other)

    def gradient(self, other, steps=10, easing=easings.linear):
        """
        Returns a generator which fades between this color and *other* in the
        specified number of *steps*.

        :param Color other:
            The color that will end the gradient (with the color the method is
            called upon starting the gradient)

        :param int steps:
            The unqiue number of colors to include in the generated gradient.
            Defaults to 10 if unspecified.

        :param callable easing:
            A function which controls the speed of the progression. If
            specified, if must be a function which takes a single parameter,
            the number of *steps*, and yields a sequence of values between 0.0
            (representing the start of the gradient) and 1.0 (representing the
            end). The default is :func:`linear`.

        :return:
            A generator yielding *steps* :class:`Color` instances which fade
            from this color to *other*.

        For example::

            >>> Color.repr_style = 'html'
            >>> print('\\n'.join(
            ... repr(c) for c in
            ... Color('red').gradient(Color('green'))
            ... ))
            Color('#ff0000')
            Color('#e30e00')
            Color('#c61c00')
            Color('#aa2b00')
            Color('#8e3900')
            Color('#714700')
            Color('#555500')
            Color('#396400')
            Color('#1c7200')
            Color('#008000')

        .. versionadded:: 1.1
        """
        if steps < 2:
            raise ValueError('steps must be >= 2')
        # NOTE: Can't simply subtract self from other here, as the result will
        # be clamped and we want the actual result.
        delta = types.RGB(*(
            other_i - self_i
            for self_i, other_i in zip(self, other)
        ))
        for t in easing(steps):
            yield self + types.RGB(*(delta_i * t for delta_i in delta))
