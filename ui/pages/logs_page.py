
from pathlib import Path
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QTextEdit,QPushButton,QHBoxLayout
try: from core.logger import get_latest_log_path
except Exception: get_latest_log_path=lambda: Path('logs/latest.log')
class LogsPage(QWidget):
    def __init__(self):
        super().__init__(); l=QVBoxLayout(self); l.setContentsMargins(36,32,36,32); title=QLabel('Логи'); title.setObjectName('PageTitle'); self.text=QTextEdit(); self.text.setReadOnly(True); self.text.setObjectName('LogViewer'); b=QPushButton('Обновить'); b.setObjectName('PrimaryButton'); b.clicked.connect(self.refresh); l.addWidget(title); l.addWidget(b); l.addWidget(self.text); self.refresh()
    def refresh(self):
        try: p=Path(get_latest_log_path()); self.text.setPlainText(p.read_text(encoding='utf-8',errors='ignore') if p.exists() else 'Лог пока пуст.')
        except Exception as e: self.text.setPlainText(str(e))
