import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindowUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindowUI()
    
    sys.exit(app.exec_())