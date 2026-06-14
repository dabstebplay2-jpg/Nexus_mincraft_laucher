
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QFrame,QGridLayout
PRESETS=[('⚡ FPS Boost','Оптимизация и больше FPS'),('🌄 Beautiful','Графика и шейдеры'),('🧱 Vanilla+','Удобства без перегруза'),('⚔ Survival','Выживание и приключения')]
class SmartBuilderPage(QWidget):
    def __init__(self):
        super().__init__(); l=QVBoxLayout(self); l.setContentsMargins(36,32,36,32); t=QLabel('Smart Builder'); t.setObjectName('PageTitle'); d=QLabel('Умный подбор модов и пресетов сборок.'); d.setObjectName('PageDescription'); l.addWidget(t); l.addWidget(d); grid=QGridLayout();
        for i,(a,b) in enumerate(PRESETS): grid.addWidget(self.card(a,b),i//2,i%2)
        l.addLayout(grid); l.addStretch()
    def card(self,a,b): c=QFrame(); c.setObjectName('Panel'); lay=QVBoxLayout(c); t=QLabel(a); t.setObjectName('PanelTitle'); d=QLabel(b); d.setObjectName('PanelText'); lay.addWidget(t); lay.addWidget(d); return c
