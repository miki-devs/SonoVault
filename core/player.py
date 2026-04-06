from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class Player(QMediaPlayer):
    def __init__(self):
        super().__init__()
        
    def cargarCancion(self, rutaArchivo):
        url = QUrl.fromLocalFile(rutaArchivo)
        self.setMedia(QMediaContent(url))
    
    def reproducirYPausar(self):
        if self.state() == QMediaPlayer.PlayingState: # type: ignore
            self.pause()
        else:
            self.play()
    