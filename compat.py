"""
Compatibility shim for ft.padding / ft.border APIs removed in Flet 0.85+.
Apply in main.py before any UI imports:

    from compat import FletPaddingCompat, FletBorderCompat
    ft.padding = FletPaddingCompat()
    ft.border = FletBorderCompat()
"""
import flet as ft


class FletPaddingCompat:
    """Emulates the old ft.padding namespace with .only() and .symmetric() helpers."""

    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return ft.Padding(left=left, top=top, right=right, bottom=bottom)

    @staticmethod
    def symmetric(horizontal=0, vertical=0):
        return ft.Padding(left=horizontal, right=horizontal, top=vertical, bottom=vertical)

    @staticmethod
    def all(value=0):
        return ft.Padding(left=value, top=value, right=value, bottom=value)


class FletBorderCompat:
    """Emulates the old ft.border namespace with .all() and .only() helpers."""

    @staticmethod
    def all(width=1, color=None):
        side = ft.BorderSide(width=width, color=color)
        return ft.Border(left=side, top=side, right=side, bottom=side)

    @staticmethod
    def only(left=None, top=None, right=None, bottom=None):
        def _side(s):
            if s is None:
                return ft.BorderSide(width=0)
            if isinstance(s, ft.BorderSide):
                return s
            return ft.BorderSide(width=s)
        return ft.Border(left=_side(left), top=_side(top), right=_side(right), bottom=_side(bottom))


class FletBorderRadiusCompat:
    """Emulates the old ft.border_radius namespace with .only() and .all() helpers."""

    @staticmethod
    def only(top_left=0, top_right=0, bottom_left=0, bottom_right=0):
        return ft.BorderRadius(
            top_left=top_left,
            top_right=top_right,
            bottom_left=bottom_left,
            bottom_right=bottom_right,
        )

    @staticmethod
    def all(value=0):
        return ft.BorderRadius(
            top_left=value, top_right=value,
            bottom_left=value, bottom_right=value,
        )


class FletMarginCompat:
    """Emulates the old ft.margin namespace with .only(), .symmetric() and .all() helpers."""

    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return ft.Margin(left=left, top=top, right=right, bottom=bottom)

    @staticmethod
    def symmetric(horizontal=0, vertical=0):
        return ft.Margin(left=horizontal, right=horizontal, top=vertical, bottom=vertical)

    @staticmethod
    def all(value=0):
        return ft.Margin(left=value, top=value, right=value, bottom=value)
