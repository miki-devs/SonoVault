import requests
from PyQt5.QtCore import QObject, pyqtSignal

API_KEY = "e687df0dc527187f3b7488d380ccb2df" 
BASE_URL = "http://ws.audioscrobbler.com/2.0/"

def obtenerMetadatosCancion(artista, cancion):
    parametrosPlayload = {
        "method": "track.getinfo",
        "track": cancion,
        "artist": artista,
        "autocorrect": 1,
        "api_key": API_KEY,
        "format": "json"
    }
    
    try:
        respuesta = requests.get(BASE_URL, params=parametrosPlayload)
        
        respuesta.raise_for_status()
        
        datosJSON = respuesta.json()
        
        if "error" in datosJSON:
            print(f"Hubo un problema con el consumo de la API: {datosJSON.get('message', 'Error desconocido')}")
            return None
        
        if "track" not in datosJSON:
            print("Respuesta de API inesperada, no se encontró 'track'")
            return None
        
        infoCancion = datosJSON["track"]
        
        nombreCancion = infoCancion.get("name", "Título Desconocido")
        
        nombreArtista = "Artista Desconocido"
        if infoCancion.get("artist"):
            nombreArtista = infoCancion["artist"].get("name", "Artista Desconocido")
            
        bioArtistaResumida = obtenerMetadatosArtista(nombreArtista) or ""
        
        albumCancion = "Álbum Desconocido"
        urlPortadaAlbum = None
        if infoCancion.get("album"):
            albumInfo = infoCancion["album"]
            albumCancion = albumInfo.get("title", "Álbum Desconocido")
            
            if albumInfo.get("image"):
                listaImagenes = albumInfo["image"]
                for tamanioPortada in listaImagenes:
                    if tamanioPortada.get('size') == 'extralarge' and tamanioPortada.get('#text'):
                        urlPortadaAlbum = tamanioPortada['#text']
                        break
        
        generoPrincipalCancion = "Género Desconocido"
        if infoCancion.get("toptags") and infoCancion["toptags"].get("tag"):
            listaTags = infoCancion["toptags"]["tag"]
            
            if isinstance(listaTags, list) and len(listaTags) > 0:
                generoPrincipalCancion = listaTags[0].get("name", "Género").capitalize()
            elif isinstance(listaTags, dict):
                 generoPrincipalCancion = listaTags.get("name", "Género").capitalize()
        
        infoCancionYArtista = {
                    "nombreCancion": nombreCancion,
                    "nombreArtista": nombreArtista,
                    "albumCancion": albumCancion,
                    "urlPortadaAlbum": urlPortadaAlbum,
                    "generoPrincipalCancion": generoPrincipalCancion,
                    "bioArtistaResumida": bioArtistaResumida
                }
               
        return infoCancionYArtista
    except requests.exceptions.RequestException as error:
        print(f"Error de conexión con Last.fm: {error}")
        return None
    except (KeyError, IndexError, TypeError) as error:
        print(f"Error procesando JSON (track.getinfo): {error}")
        return None

def obtenerMetadatosArtista(artista):
    parametrosPlayload = {
        "method": "artist.getInfo",
        "artist": artista,
        "api_key": API_KEY,
        "format": "json",
        "autocorrect": 1,
        "lang": "es"
    }
    
    try:
        respuesta = requests.get(BASE_URL, params=parametrosPlayload)
        
        respuesta.raise_for_status()
        
        datosJSON = respuesta.json()
        
        if "error" in datosJSON:
            print(f"API Error (artist.getInfo): {datosJSON.get('message', 'Error desconocido')}")
            return None
        
        if "artist" not in datosJSON:
            print("Respuesta de API inesperada, no se encontró 'artist'")
            return None
        
        infoArtista = datosJSON["artist"]
        
        bioArtistaResumida = ""
        if infoArtista.get("bio"):
            bioArtistaResumida = infoArtista["bio"].get("summary", "")
        
        return bioArtistaResumida
    except requests.exceptions.RequestException as error:
        print(f"Error de conexión (artist.getInfo): {error}")
        return None
    except (KeyError, IndexError, TypeError) as error:
        print(f"Error procesando JSON (artist.getInfo): {error}")
        return None
        

class ImageDownloader(QObject):
    imagenDescargada = pyqtSignal(bytes)
    
    def __init__(self, url):
        super().__init__()
        
        self.url = url
        
    def descargarImagen(self):
        try:
            respuesta = requests.get(self.url)
            respuesta.raise_for_status()
            
            datosImagen = respuesta.content
            
            self.imagenDescargada.emit(datosImagen)
        except Exception as error:
            print(f"Error al descargar imagen: {error}")