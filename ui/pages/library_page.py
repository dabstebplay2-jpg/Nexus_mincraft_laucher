
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
class LibraryPage(QWidget):
    def __init__(self): super().__init__(); l=QVBoxLayout(self); l.setContentsMargins(36,32,36,32); t=QLabel('Библиотека'); t.setObjectName('PageTitle'); d=QLabel('Установленные моды по сборкам.'); d.setObjectName('PageDescription'); l.addWidget(t); l.addWidget(d); l.addStretch()
    def refresh(self): pass
