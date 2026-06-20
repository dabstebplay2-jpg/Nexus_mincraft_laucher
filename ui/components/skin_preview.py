from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import QWidget


class SkinFaceWidget(QWidget):
    def __init__(self, size: int = 104, parent=None):
        super().__init__(parent)
        self._skin_path: str | None = None
        self._label = "OFF"
        self.setFixedSize(size, size)

    def set_skin(self, skin_path: str | None, label: str = "OFF") -> None:
        self._skin_path = skin_path
        self._label = label or "OFF"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#07111f"))

        skin_pix = None

        if self._skin_path and Path(self._skin_path).exists():
            pix = QPixmap(self._skin_path)
            if not pix.isNull() and pix.width() >= 64 and pix.height() >= 32:
                scale = max(1, pix.width() // 64)
                face = pix.copy(QRect(8 * scale, 8 * scale, 8 * scale, 8 * scale))
                face = face.scaled(
                    self.width() - 22,
                    self.height() - 22,
                    Qt.IgnoreAspectRatio,
                    Qt.FastTransformation,
                )
                skin_pix = face

        if skin_pix:
            x = (self.width() - skin_pix.width()) // 2
            y = (self.height() - skin_pix.height()) // 2
            painter.drawPixmap(x, y, skin_pix)
        else:
            self._draw_default_face(painter)

        pen = QPen(QColor("#24d46b"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(1, 1, self.width() - 3, self.height() - 3)

    def _draw_default_face(self, painter: QPainter) -> None:
        cell = max(7, self.width() // 9)
        start_x = (self.width() - cell * 7) // 2
        start_y = (self.height() - cell * 7) // 2

        green = QColor("#69d316")
        dark = QColor("#0c2516")
        shadow = QColor("#1d8f37")

        painter.fillRect(start_x, start_y, cell * 7, cell * 7, green)

        for x, y, c in [
            (1, 1, dark),
            (5, 1, dark),
            (2, 3, dark),
            (4, 3, dark),
            (1, 4, dark),
            (3, 4, dark),
            (5, 4, dark),
            (0, 6, shadow),
            (6, 6, shadow),
        ]:
            painter.fillRect(start_x + x * cell, start_y + y * cell, cell, cell, c)

        painter.setPen(QColor("#eafff1"))
        f = QFont()
        f.setPointSize(8)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignHCenter, self._label[:6])


class Skin3DPreviewWidget(QWidget):
    def __init__(self, width: int = 210, height: int = 250, parent=None):
        super().__init__(parent)
        self._skin_path: str | None = None
        self._label = "NEXUS"
        self.setMinimumSize(width, height)

    def set_skin(self, skin_path: str | None, label: str = "NEXUS") -> None:
        self._skin_path = skin_path
        self._label = label or "NEXUS"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#07100c"))

        skin = QPixmap(self._skin_path) if self._skin_path and Path(self._skin_path).exists() else QPixmap()
        scale = max(1, skin.width() // 64) if not skin.isNull() and skin.width() >= 64 else 1

        def part(rect, fallback):
            if skin.isNull() or skin.width() < 64 or skin.height() < 32:
                return QColor(fallback)
            x, y, w, h = rect
            pix = skin.copy(QRect(x * scale, y * scale, w * scale, h * scale))
            return pix

        cx = self.width() // 2
        top = 34
        self._draw_box(painter, cx - 34, top, 68, 68, part((8, 8, 8, 8), "#79c86a"))
        self._draw_box(painter, cx - 28, top + 72, 56, 82, part((20, 20, 8, 12), "#3f7b42"))
        self._draw_box(painter, cx - 84, top + 78, 44, 78, part((44, 20, 4, 12), "#5a9b50"))
        self._draw_box(painter, cx + 40, top + 78, 44, 78, part((36, 52, 4, 12), "#5a9b50"))
        self._draw_box(painter, cx - 32, top + 158, 28, 70, part((4, 20, 4, 12), "#315d36"))
        self._draw_box(painter, cx + 4, top + 158, 28, 70, part((20, 52, 4, 12), "#315d36"))

        painter.setPen(QColor("#dff5d7"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(0, self.height() - 24, self.width(), 18, Qt.AlignCenter, self._label[:18])

    def _draw_box(self, painter: QPainter, x: int, y: int, w: int, h: int, fill):
        depth = max(8, min(w, h) // 5)
        front = QRect(x, y + depth, w, h)
        top_poly = QPolygon([
            front.topLeft(),
            front.topRight(),
            front.topRight() + QPoint(depth, -depth),
            front.topLeft() + QPoint(depth, -depth),
        ])
        side_poly = QPolygon([
            front.topRight(),
            front.bottomRight(),
            front.bottomRight() + QPoint(depth, -depth),
            front.topRight() + QPoint(depth, -depth),
        ])

        if isinstance(fill, QPixmap):
            painter.drawPixmap(front, fill)
            base = QColor("#6fc35d")
        else:
            base = QColor(fill)
            painter.fillRect(front, base)

        top_color = QColor(base)
        top_color = top_color.lighter(118)
        side_color = QColor(base)
        side_color = side_color.darker(130)
        painter.setPen(QPen(QColor("#132018"), 1))
        painter.setBrush(top_color)
        painter.drawPolygon(top_poly)
        painter.setBrush(side_color)
        painter.drawPolygon(side_poly)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(front)
