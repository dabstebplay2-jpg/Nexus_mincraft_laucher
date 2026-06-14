import logging
import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from core.logger import setup_logging
from core.network_manager import disable_proxy_for_launcher, log_proxy_environment


def show_fatal_error(error: BaseException):
    message = QMessageBox()
    message.setIcon(QMessageBox.Critical)
    message.setWindowTitle("Nexus Launcher — ошибка запуска")
    message.setText("Не удалось запустить Nexus Launcher.")
    message.setInformativeText(str(error))
    message.setDetailedText(traceback.format_exc())
    message.exec()


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Checking proxy environment before cleanup")
        log_proxy_environment()

        disable_proxy_for_launcher()

        logger.info("Checking proxy environment after cleanup")
        log_proxy_environment()

        from app.window import MainWindow

        logger.info("Creating QApplication")
        app = QApplication(sys.argv)

        logger.info("Creating main window")
        window = MainWindow()
        window.show()

        logger.info("Application event loop started")
        exit_code = app.exec()

        logger.info("Application closed with code %s", exit_code)
        sys.exit(exit_code)

    except Exception as error:
        logger.exception("Fatal application error")

        try:
            app = QApplication.instance() or QApplication(sys.argv)
            show_fatal_error(error)
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
