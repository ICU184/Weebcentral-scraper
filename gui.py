import sys
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PySide6.QtCore import Signal, QObject, Qt, QTimer
import weebcentral_scraper

class EmittingStream(QObject):
    textWritten = Signal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WeebCentral Manager")
        self.resize(650, 450)

        # Redirect stdout and stderr to the GUI text area
        sys.stdout = EmittingStream()
        sys.stdout.textWritten.connect(self.normalOutputWritten)
        sys.stderr = sys.stdout

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Output Text Area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        # Use a generic monospace font
        self.text_area.setStyleSheet("font-family: monospace; font-size: 13px;")
        layout.addWidget(self.text_area)

        # Input Area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter a new WeebCentral Series URL here...")
        input_layout.addWidget(self.url_input)

        self.btn_add = QPushButton("Add && Download")
        self.btn_add.clicked.connect(self.add_and_download)
        input_layout.addWidget(self.btn_add)
        
        layout.addLayout(input_layout)

        # Bulk Update
        self.btn_bulk = QPushButton("Update All Missing Chapters (from manga_list.txt)")
        self.btn_bulk.clicked.connect(self.bulk_update)
        layout.addWidget(self.btn_bulk)

        print("Welcome to WeebCentral Manager!")
        print("Ready.\n")

    def normalOutputWritten(self, text):
        cursor = self.text_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.text_area.setTextCursor(cursor)
        self.text_area.ensureCursorVisible()

    def add_and_download(self):
        url = self.url_input.text().strip()
        if not url:
            print("Please enter a URL first.")
            return
        
        # Disable buttons while running
        self.set_buttons_enabled(False)
        self.url_input.clear()
        
        threading.Thread(target=self.run_scraper, args=(url,), daemon=True).start()

    def bulk_update(self):
        self.set_buttons_enabled(False)
        threading.Thread(target=self.run_bulk, daemon=True).start()

    def run_scraper(self, url):
        try:
            weebcentral_scraper.run_scraper_gui(url)
        except Exception as e:
            print(f"Error: {e}")
        # Enable buttons on main thread
        QTimer.singleShot(0, lambda: self.set_buttons_enabled(True))

    def run_bulk(self):
        try:
            weebcentral_scraper.run_bulk_mode()
        except Exception as e:
            print(f"Error: {e}")
        # Enable buttons on main thread
        QTimer.singleShot(0, lambda: self.set_buttons_enabled(True))

    def set_buttons_enabled(self, enabled):
        self.btn_add.setEnabled(enabled)
        self.btn_bulk.setEnabled(enabled)
        self.url_input.setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Needs to be called once so the working directory is set to where the app is
    try:
        import os
        base_path = weebcentral_scraper.get_base_path()
        os.chdir(base_path)
    except Exception:
        pass

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
