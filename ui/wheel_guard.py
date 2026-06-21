from __future__ import annotations

from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QAbstractSlider, QAbstractSpinBox, QComboBox, QScrollArea


class NoWheelValueChangeFilter(QObject):
    """Prevent accidental value changes while scrolling launcher pages."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(
            obj,
            (QAbstractSlider, QAbstractSpinBox, QComboBox),
        ):
            scroll_area = self._nearest_scroll_area(obj)
            if scroll_area:
                self._scroll_parent(scroll_area, event)
            return True
        return super().eventFilter(obj, event)

    def _nearest_scroll_area(self, widget):
        parent = widget.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return parent
            parent = parent.parent()
        return None

    def _scroll_parent(self, scroll_area: QScrollArea, event):
        bar = scroll_area.verticalScrollBar()
        if not bar:
            return

        pixel_delta = event.pixelDelta()
        angle_delta = event.angleDelta()

        if not pixel_delta.isNull():
            delta = pixel_delta.y()
        else:
            delta = angle_delta.y() / 8

        if not delta:
            return

        bar.setValue(bar.value() - int(delta))


_wheel_filter: NoWheelValueChangeFilter | None = None


def install_no_wheel_value_changes(app):
    global _wheel_filter
    if _wheel_filter is None:
        _wheel_filter = NoWheelValueChangeFilter(app)
        app.installEventFilter(_wheel_filter)
    return _wheel_filter
