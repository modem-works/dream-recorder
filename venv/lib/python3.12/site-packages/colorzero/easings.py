# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# The colorzero color library
#
# Copyright (c) 2018 Dave Jones <dave@waveform.org.uk>
#
# SPDX-License-Identifier: BSD-3-Clause

"Defines various easing functions for :meth:`Color.gradient`."


def linear(steps):
    "Linear easing function; yields *steps* values between 0.0 and 1.0"
    for t in range(steps):
        yield t / (steps - 1)


def ease_in(steps):
    "Quadratic ease-in function; yields *steps* values between 0.0 and 1.0"
    for t in linear(steps):
        yield t ** 2


def ease_out(steps):
    "Quadratic ease-out function; yields *steps* values between 0.0 and 1.0"
    for t in linear(steps):
        yield t * (2 - t)


def ease_in_out(steps):
    "Quadratic ease-in-out function; yields *steps* values between 0.0 and 1.0"
    for t in linear(steps):
        yield 2 * t * t if t < 0.5 else (4 - 2 * t) * t - 1
