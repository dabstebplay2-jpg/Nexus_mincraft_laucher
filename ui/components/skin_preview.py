from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
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
        cell = max(3, min(self.width(), self.height()) // 9)
        start_x = (self.width() - cell * 7) // 2
        start_y = (self.height() - cell * 7) // 2

        base = QColor("#6f8d66")
        dark = QColor("#18251c")
        shadow = QColor("#405d45")

        painter.fillRect(start_x, start_y, cell * 7, cell * 7, base)

        for x, y, c in [
            (1, 1, shadow),
            (5, 1, shadow),
            (2, 3, dark),
            (3, 3, dark),
            (4, 3, dark),
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
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#07100c"))

        skin = QPixmap(self._skin_path) if self._skin_path and Path(self._skin_path).exists() else QPixmap()
        scale = max(1, skin.width() // 64) if not skin.isNull() and skin.width() >= 64 else 1

        if skin.isNull() or skin.width() < 64 or skin.height() < 32:
            self._draw_empty_model(painter)
            return

        def part(rect):
            x, y, w, h = rect
            return skin.copy(QRect(x * scale, y * scale, w * scale, h * scale))

        def draw_part(rect: QRect, base_rect, overlay_rect=None):
            base = part(base_rect)
            painter.drawPixmap(rect, base)
            if overlay_rect and skin.height() >= 64 * scale:
                overlay = part(overlay_rect)
                painter.drawPixmap(rect, overlay)

        cx = self.width() // 2
        px = max(4, min(8, (self.width() - 24) // 16, (self.height() - 42) // 32))
        model_height = 32 * px
        top = max(10, (self.height() - model_height - 22) // 2)

        head = QRect(cx - 4 * px, top, 8 * px, 8 * px)
        body = QRect(cx - 4 * px, top + 8 * px, 8 * px, 12 * px)
        left_arm = QRect(cx - 8 * px, top + 8 * px, 4 * px, 12 * px)
        right_arm = QRect(cx + 4 * px, top + 8 * px, 4 * px, 12 * px)
        left_leg = QRect(cx - 4 * px, top + 20 * px, 4 * px, 12 * px)
        right_leg = QRect(cx, top + 20 * px, 4 * px, 12 * px)

        draw_part(head, (8, 8, 8, 8), (40, 8, 8, 8))
        draw_part(body, (20, 20, 8, 12), (20, 36, 8, 12))
        draw_part(left_arm, (44, 20, 4, 12), (44, 36, 4, 12))
        draw_part(right_arm, (36, 52, 4, 12), (52, 52, 4, 12))
        draw_part(left_leg, (4, 20, 4, 12), (4, 36, 4, 12))
        draw_part(right_leg, (20, 52, 4, 12), (4, 52, 4, 12))

        pen = QPen(QColor("#1c2a20"))
        pen.setWidth(1)
        painter.setPen(pen)
        for rect in (head, body, left_arm, right_arm, left_leg, right_leg):
            painter.drawRect(rect.adjusted(0, 0, -1, -1))

        painter.setPen(QColor("#dff5d7"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(0, self.height() - 22, self.width(), 18, Qt.AlignCenter, self._label[:18])

    def _draw_empty_model(self, painter: QPainter) -> None:
        cx = self.width() // 2
        px = max(4, min(8, (self.width() - 24) // 16, (self.height() - 42) // 32))
        model_height = 32 * px
        top = max(10, (self.height() - model_height - 22) // 2)
        colors = {
            "head": QColor("#6f8d66"),
            "body": QColor("#405d45"),
            "limb": QColor("#33483a"),
        }
        for rect, color in [
            (QRect(cx - 4 * px, top, 8 * px, 8 * px), colors["head"]),
            (QRect(cx - 4 * px, top + 8 * px, 8 * px, 12 * px), colors["body"]),
            (QRect(cx - 8 * px, top + 8 * px, 4 * px, 12 * px), colors["limb"]),
            (QRect(cx + 4 * px, top + 8 * px, 4 * px, 12 * px), colors["limb"]),
            (QRect(cx - 4 * px, top + 20 * px, 4 * px, 12 * px), colors["limb"]),
            (QRect(cx, top + 20 * px, 4 * px, 12 * px), colors["limb"]),
        ]:
            painter.fillRect(rect, color)
            painter.setPen(QPen(QColor("#18251c"), 1))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))

        painter.setPen(QColor("#dff5d7"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(0, self.height() - 22, self.width(), 18, Qt.AlignCenter, "Скин не выбран")
