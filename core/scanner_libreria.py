import os
import mutagen
from PyQt5.QtCore import QObject, pyqtSignal

class ScannerWorker (QObject):
    
    cancionEncontrada = pyqtSignal(dict)
    escaneoFinalizado = pyqtSignal(list)
    
    
    def __init__(self, rutaCarpeta):
        super().__init__()
        
        self.rutaCarpeta = rutaCarpeta
        
        self.detenerEscaneo = False
        
    def detener(self):
        self.detenerEscaneo = True
        
    def recorrerBibliotecaDeCanciones(self):
        cancionesEncontradas = []
        print("Comenzando escaneo de archivos...")
        
        for rutaActual, subcarpetas, archivos in os.walk(self.rutaCarpeta):
            if self.detenerEscaneo:
                print("Escaneo detenido por el usuario")
                break
                
            for nombreArchivo in archivos:
                if self.detenerEscaneo:
                    break
                    
                if nombreArchivo.lower().endswith((".mp3", ".flac", ".wav", ".ogg", ".m4a", ".wma", ".aac")):
                    rutaCompletaCancion = os.path.join(rutaActual, nombreArchivo)
                    
                    try:
                        
                        audio = mutagen.File(rutaCompletaCancion, easy=True)
                        
                        if audio:
                            duracion = int(audio.info.length) if hasattr(audio.info, 'length') else 0
                            
                            datosCancion = {
                                "titulo": audio.get("title", [nombreArchivo])[0],
                                "artista": audio.get("artist", ["Desconocido"])[0],
                                "album": audio.get("album", ["Desconocido"])[0],
                                "duracion_segundos": duracion,
                                "ruta_archivo": rutaCompletaCancion
                            }
                            
                            self.cancionEncontrada.emit(datosCancion)
                            cancionesEncontradas.append(datosCancion)
                    except Exception as errorEncontrado:
                        print(f"Error leyendo {nombreArchivo}: {errorEncontrado}")
                        continue
        
        print(f"Encontradas {len(cancionesEncontradas)} canciones")
        self.escaneoFinalizado.emit(cancionesEncontradas)