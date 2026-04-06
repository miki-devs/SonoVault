import os
import random
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QSplitter, QLabel, QStackedWidget, QListWidget,
    QMessageBox, QFileDialog, QSlider, QListWidgetItem, QApplication)
from PyQt5.QtGui import QIcon, QColor, QPixmap
from PyQt5.QtCore import Qt, QThread
from core.player import Player
from core.scanner_libreria import ScannerWorker
from core.cliente_api import obtenerMetadatosCancion, ImageDownloader
from database.db_manager import DatabaseManager

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.reproductor = Player()

        databasePath = os.path.join("database", "sonovault.db")
        self.managerDB = DatabaseManager(databasePath)
        
        if not self.managerDB.crearTablas():
            QMessageBox.warning(self, "Error", "No se pudieron crear las tablas de la base de datos")
        
        self.hiloEscaner = None
        self.trabajadorEscaner = None
        self.hiloDescarga = None
        self.trabajadorDescarga = None
        
        self.datosCancionesActuales = []
        self.datosArtistasActuales = []
        self.datosAlbumesActuales = []
        self.datosFavoritosActuales = []
        self.cancionActual = None
        self.enReproduccion = False
        self.colaReproduccion = []
        self.indiceCancionActual = -1
        self.duracionActual = None 
        self.duracionTotal = None
        #self.bioArtistaActual = None
        
        self.setUpUI()
        
        dimensionesPantalla = QApplication.primaryScreen().availableGeometry() # type: ignore
        
        anchoVentana = int(dimensionesPantalla.width() * 0.50)
        altoVentana = int(dimensionesPantalla.height() * 0.75)
        
        self.setFixedSize(anchoVentana, altoVentana)
        
        self.conectarSignalsYSlots()
        
        self.show()
        
        self.cargarEstilos("ui/styles.qss")
        
    def setUpUI(self):
        self.setWindowTitle("SonoVault")
        self.setWindowIcon(QIcon("assets/icons/turntable.svg"))
        
        widgetPrincipal = QWidget()
        layoutPrincipal = QVBoxLayout()
        widgetPrincipal.setLayout(layoutPrincipal)
        self.setCentralWidget(widgetPrincipal)
        
        barraSuperior = self.crearBarraSuperior()
        zonaCentral = self.crearZonaCentral()
        barraInferior = self.crearBarraInferior()
        
        layoutPrincipal.addWidget(barraSuperior)
        layoutPrincipal.addWidget(zonaCentral)
        layoutPrincipal.addWidget(barraInferior)
        
        layoutPrincipal.setStretchFactor(barraSuperior, 1)
        layoutPrincipal.setStretchFactor(zonaCentral, 7)
        layoutPrincipal.setStretchFactor(barraInferior, 2)
    
    def crearBarraSuperior(self):
        barraSuperior = QWidget()
        layoutBarraSuperior = QHBoxLayout()
        
        self.botonElegirBiblioteca = QPushButton("")
        self.botonElegirBiblioteca.setToolTip("Elegir biblioteca de música")
        self. botonElegirBiblioteca.setIcon(QIcon("assets/icons/folder-open.svg"))
        self.botonElegirBiblioteca.setFixedWidth(35)
        layoutBarraSuperior.addWidget(self.botonElegirBiblioteca)
        
        self.barraDeBusqueda = QLineEdit()
        self.barraDeBusqueda.setPlaceholderText("Buscar en la biblioteca (canción, álbum, artista, playlist)...")
        layoutBarraSuperior.addWidget(self.barraDeBusqueda)
        
        self.botonBuscar = QPushButton("")
        self.botonBuscar.setToolTip("Buscar")
        self.botonBuscar.setIcon(QIcon("assets/icons/search.svg"))
        self.botonElegirBiblioteca.setFixedWidth(35)
        layoutBarraSuperior.addWidget(self.botonBuscar)
        
        self.botonFiltrarBusqueda = QPushButton("")
        self.botonFiltrarBusqueda.setToolTip("Filtrar búsqueda")
        self.botonFiltrarBusqueda.setIcon(QIcon("assets/icons/sliders-horizontal.svg"))
        self.botonElegirBiblioteca.setFixedWidth(35)
        layoutBarraSuperior.addWidget(self.botonFiltrarBusqueda)
        
        barraSuperior.setLayout(layoutBarraSuperior)
        return barraSuperior
    
    def crearZonaCentral(self):
        panelesCentrales = QSplitter(Qt.Horizontal) # type: ignore
        
        
        panelIzquierdo = QWidget()
        panelIzquierdoLayout = QVBoxLayout()
        panelIzquierdo.setMaximumWidth(220)
        layoutLabelMiMusica = QHBoxLayout()
        iconoMiMusica = QLabel()
        iconoMiMusica.setPixmap(QIcon("assets/icons/disc-3.svg").pixmap(16, 16))
        labelMiMusica = QLabel("MI MÚSICA")
        layoutLabelMiMusica.addWidget(iconoMiMusica)
        layoutLabelMiMusica.addWidget(labelMiMusica)
        layoutLabelMiMusica.addStretch()
        panelIzquierdoLayout.addLayout(layoutLabelMiMusica)
        
        iconoCanciones = QIcon("assets/icons/audio-lines.svg")
        self.botonCanciones = QPushButton("Canciones")
        self.botonCanciones.setIcon(iconoCanciones)
        panelIzquierdoLayout.addWidget(self.botonCanciones)
        
        iconoAlbumes = QIcon("assets/icons/disc-album.svg")
        self.botonAlbumes = QPushButton("Albumes")
        self.botonAlbumes.setIcon(iconoAlbumes)
        panelIzquierdoLayout.addWidget(self.botonAlbumes)
        
        iconoArtistas = QIcon("assets/icons/mic-vocal.svg")
        self.botonArtistas = QPushButton("Artistas")
        self.botonArtistas.setIcon(iconoArtistas)
        panelIzquierdoLayout.addWidget(self.botonArtistas)
        
        iconoPlaylists = QIcon("assets/icons/list-music.svg")
        self.botonPlaylists = QPushButton("Playlists")
        self.botonPlaylists.setIcon(iconoPlaylists)
        panelIzquierdoLayout.addWidget(self.botonPlaylists)
        
        iconoFavoritos = QIcon("assets/icons/heart-solid.svg")
        self.botonFavoritos = QPushButton("Favoritos")
        self.botonFavoritos.setIcon(iconoFavoritos)
        panelIzquierdoLayout.addWidget(self.botonFavoritos)
        
        panelIzquierdoLayout.addStretch(1)
        panelIzquierdo.setLayout(panelIzquierdoLayout)
        
        
        self.paginas = QStackedWidget()
        paginaInicial = QWidget()
        layoutPaginaInicial = QVBoxLayout()
        mensajePaginaInicial = QLabel("Selecciona una opción del panel izquierdo para mostrar su contenido...")
        mensajePaginaInicial.setAlignment(Qt.AlignCenter) # type: ignore
        layoutPaginaInicial.addWidget(mensajePaginaInicial)
        paginaInicial.setLayout(layoutPaginaInicial)
        
        self.listaCanciones = QListWidget()
        self.listaAlbumes = QListWidget()
        self.listaArtistas = QListWidget()
        self.listaPlaylists = QListWidget()
        self.listaFavoritos = QListWidget()
        self.listaColaReproduccion = QListWidget()
        
        self.paginas.addWidget(paginaInicial)
        self.paginas.addWidget(self.listaCanciones)
        self.paginas.addWidget(self.listaAlbumes)
        self.paginas.addWidget(self.listaArtistas)
        self.paginas.addWidget(self.listaPlaylists)
        self.paginas.addWidget(self.listaFavoritos)
        self.paginas.addWidget(self.listaColaReproduccion)
        
        self.paginas.setCurrentIndex(0)
        
        panelesCentrales.addWidget(panelIzquierdo)
        panelesCentrales.addWidget(self.paginas)
        panelesCentrales.setSizes([250, 750])
        
        return panelesCentrales
        
    def crearBarraInferior(self):
        barraInferior = QWidget()
        
        barraInferiorLayout = QHBoxLayout()
        barraInferior.setLayout(barraInferiorLayout)
        barraInferior.setMinimumHeight(100)
        
        self.infoCancion = QWidget()
        layoutDisplayImagenYCancion = QHBoxLayout()
        layoutDisplayImagenYCancion.setAlignment(Qt.AlignVCenter) # type: ignore
        
        layoutCancionArtista = QVBoxLayout()
        
        infoCancionYArtistaWidget = QWidget()
        infoCancionYArtistaWidget.setLayout(layoutCancionArtista)
        
        self.imagenCancion = QLabel()
        self.imagenCancion.setFixedSize(125, 125)
        self.imagenCancion.setScaledContents(True)
        self.imagenCancion.setPixmap(QPixmap("assets/icons/turntable.svg"))
        self.tituloCancion = QLabel("Selecciona una canción")
        self.artistaCancion = QLabel("Artista")
        self.albumCancion = QLabel("Álbum")
        self.generoCancion = QLabel("Género")
        
        layoutCancionArtista.addWidget(self.tituloCancion)
        layoutCancionArtista.addWidget(self.artistaCancion)
        layoutCancionArtista.addWidget(self.albumCancion)
        layoutCancionArtista.addWidget(self.albumCancion)
        
        layoutDisplayImagenYCancion.addWidget(self.imagenCancion)
        layoutDisplayImagenYCancion.addWidget(infoCancionYArtistaWidget)
        self.infoCancion.setLayout(layoutDisplayImagenYCancion)
        
        
        self.controlesReproduccion = QWidget()
        layoutReproduccion = QVBoxLayout()
        
        self.progresoWidget = QWidget()
        layoutProgreso = QHBoxLayout()
        self.progresoWidget.setLayout(layoutProgreso)
        
        self.barraProgresoCancion = QSlider(Qt.Horizontal) # type: ignore
        self.barraProgresoCancion.setMinimum(0)
        self.barraProgresoCancion.setMaximum(100)
        
        self.duracionActual = QLabel("0:00") 
        self.duracionActual.setMinimumWidth(35)
        self.duracionActual.setAlignment(Qt.AlignCenter) # type: ignore
        
        self.duracionTotal = QLabel("0:00")
        self.duracionTotal.setMinimumWidth(35)
        self.duracionTotal.setAlignment(Qt.AlignCenter) # type: ignore
        
        layoutProgreso.addWidget(self.duracionActual)
        layoutProgreso.addWidget(self.barraProgresoCancion)
        layoutProgreso.addWidget(self.duracionTotal)
        
        self.botonesReproduccion = QWidget()
        layoutBotonesReproduccion = QHBoxLayout()
        self.botonesReproduccion.setLayout(layoutBotonesReproduccion)
        
        iconoAleatorio = QIcon("assets/icons/shuffle.svg")
        self.botonAleatorio = QPushButton()
        self.botonAleatorio.setToolTip("Aleatorio")
        self.botonAleatorio.setIcon(iconoAleatorio)
        
        iconoCancionPrevia = QIcon("assets/icons/chevron-first.svg")
        self.botonCancionPrevia = QPushButton()
        self.botonCancionPrevia.setToolTip("Canción previa")
        self.botonCancionPrevia.setIcon(iconoCancionPrevia)
        
        self.iconoReproducir = QIcon("assets/icons/play.svg")
        self.iconoPausar = QIcon("assets/icons/pause.svg")
        self.botonReproducirYPausar = QPushButton()
        self.botonReproducirYPausar.setToolTip("Reproducir/Pausar")
        self.botonReproducirYPausar.setCheckable(True)
        self.botonReproducirYPausar.setIcon(self.iconoReproducir)
        self.botonReproducirYPausar.toggled.connect(self.actualizarIconoReproduccion)
        
        iconoCancionSiguiente = QIcon("assets/icons/chevron-last.svg")
        self.botonCancionSiguiente = QPushButton()
        self.botonCancionSiguiente.setToolTip("Canción siguiente")
        self.botonCancionSiguiente.setIcon(iconoCancionSiguiente)
        
        layoutBotonesReproduccion.addStretch()
        layoutBotonesReproduccion.addWidget(self.botonAleatorio)
        layoutBotonesReproduccion.addWidget(self.botonCancionPrevia)
        layoutBotonesReproduccion.addWidget(self.botonReproducirYPausar)
        layoutBotonesReproduccion.addWidget(self.botonCancionSiguiente)
        layoutBotonesReproduccion.addStretch()

        layoutReproduccion.addWidget(self.progresoWidget)
        layoutReproduccion.addWidget(self.botonesReproduccion)
        self.controlesReproduccion.setLayout(layoutReproduccion)
        
        
        controlesAdicionales = QWidget()
        layoutControlesAdicionales = QHBoxLayout()
        controlesAdicionales.setLayout(layoutControlesAdicionales)
        
        self.botonFavorito = QPushButton()
        self.iconoFavorito = QIcon("assets/icons/heart-solid.svg")
        self.iconoNoFavorito = QIcon("assets/icons/heart.svg")
        self.botonFavorito.setToolTip("Agregar a favoritos")
        self.botonFavorito.setCheckable(True)
        self.botonFavorito.setIcon(self.iconoNoFavorito)
        self.botonFavorito.toggled.connect(self.actualizarIconoFavorito)
        
        self.botonMostrarLetra = QPushButton()
        self.botonMostrarLetra.setToolTip("Mostrar la letra de la canción")
        self.botonMostrarLetra.setIcon(QIcon("assets/icons/captions.svg"))
        
        self.botonColaDeReproduccion = QPushButton()
        self.botonColaDeReproduccion.setToolTip("Ver cola de reproducción")
        self.botonColaDeReproduccion.setIcon(QIcon("assets/icons/list-video.svg"))
        
        layoutControlesAdicionales.addStretch()
        layoutControlesAdicionales.addWidget(self.botonFavorito)
        layoutControlesAdicionales.addWidget(self.botonMostrarLetra)
        layoutControlesAdicionales.addWidget(self.botonColaDeReproduccion)
        layoutControlesAdicionales.addStretch()
        
        
        controlVolumen = QWidget()
        layoutControlVolumen = QHBoxLayout()
        controlVolumen.setLayout(layoutControlVolumen)
        self.iconoVolumen = QLabel()
        self.iconoVolumen.setPixmap(QIcon("assets/icons/volume-2.svg").pixmap(20, 20))
        self.sliderVolumen = QSlider(Qt.Horizontal) # type: ignore
        self.sliderVolumen.setMaximumWidth(100)
        self.sliderVolumen.setValue(50)
        
        
        layoutControlVolumen.addWidget(self.iconoVolumen)
        layoutControlVolumen.addWidget(self.sliderVolumen)
        layoutControlVolumen.setStretchFactor(self.iconoVolumen, 1)
        layoutControlVolumen.setStretchFactor(self.sliderVolumen, 4)
        layoutControlesAdicionales.addWidget(controlVolumen)
        
        
        barraInferiorLayout.addWidget(self.infoCancion)
        barraInferiorLayout.addWidget(self.controlesReproduccion)
        barraInferiorLayout.addWidget(controlesAdicionales)
        barraInferiorLayout.setStretchFactor(self.infoCancion, 4)
        barraInferiorLayout.setStretchFactor(self.controlesReproduccion, 3)
        barraInferiorLayout.setStretchFactor(controlesAdicionales, 3)
        
        return barraInferior
    
    def actualizarIconoFavorito(self, clickeado):
        if clickeado:
            self.botonFavorito.setIcon(self.iconoFavorito)
        else:
            self.botonFavorito.setIcon(self.iconoNoFavorito)
            
    def actualizarIconoReproduccion(self, estado):
        if estado == QMediaPlayer.PlayingState: # type: ignore
            self.botonReproducirYPausar.setIcon(self.iconoPausar)
            self.botonReproducirYPausar.setChecked(True)
        else:
            self.botonReproducirYPausar.setIcon(self.iconoReproducir)
            self.botonReproducirYPausar.setChecked(False)
            
    def actualizarPosicionSlider(self, posicion):
        self.barraProgresoCancion.blockSignals(True)
        self.barraProgresoCancion.setValue(posicion)
        self.barraProgresoCancion.blockSignals(False)

        totalSegundos = posicion // 1000
        
        minutos = totalSegundos // 60
        segundos = totalSegundos % 60
        duracionFormateada = f"{minutos}:{segundos:02d}"
        self.duracionActual.setText(duracionFormateada) # type: ignore

    def actualizarRangoSlider(self, duracion):
        self.barraProgresoCancion.setMaximum(duracion)
            
        if duracion > 0:
            totalSegundos = duracion // 1000
            minutos = totalSegundos // 60
            segundos = totalSegundos % 60
            
            duracionFormateada = f"{minutos}:{segundos:02d}"

            self.duracionTotal.setText(duracionFormateada) # type: ignore
        else:
            self.duracionTotal.setText("0:00") # type: ignore
            self.duracionActual.setText("0:00") # type: ignore
            
    def elegirBiblioteca(self):
        self.carpetaSeleccionada = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de música")
        
        if not self.carpetaSeleccionada:
            return
        
        print(f"Carpeta seleccionada: {self.carpetaSeleccionada}")
        print("Iniciando escaneo...")
        
        if self.hiloEscaner and self.hiloEscaner.isRunning():
            print("Deteniendo hilo anterior...")
            if self.trabajadorEscaner:
                self.trabajadorEscaner.detener()
            self.hiloEscaner.quit()
            self.hiloEscaner.wait(1000)
        
        self.hiloEscaner = QThread()
        self.trabajadorEscaner = ScannerWorker(self.carpetaSeleccionada)
        self.trabajadorEscaner.moveToThread(self.hiloEscaner)
        
        self.hiloEscaner.started.connect(self.trabajadorEscaner.recorrerBibliotecaDeCanciones)
        self.trabajadorEscaner.cancionEncontrada.connect(self.managerDB.agregarCancion)
        self.trabajadorEscaner.escaneoFinalizado.connect(self.procesarCancionesEnLote)
        self.trabajadorEscaner.escaneoFinalizado.connect(self.hiloEscaner.quit)
        self.trabajadorEscaner.escaneoFinalizado.connect(self.trabajadorEscaner.deleteLater)
        self.hiloEscaner.finished.connect(self.trabajadorEscaner.deleteLater)
        self.hiloEscaner.finished.connect(self.hiloEscaner.deleteLater)
        self.hiloEscaner.finished.connect(self.limpiarHiloEscaner)
        
        self.hiloEscaner.start()
        self.botonElegirBiblioteca.setEnabled(False)

    def limpiarHiloEscaner(self):
        self.hiloEscaner = None
        print("Hilo de escaneo limpiado correctamente")
        
    def limpiarHiloDescarga(self):
        print("Limpiando hilo de descarga...")
        self.hiloDescarga = None
        self.trabajadorDescarga = None
    
    def finalizarEscaneo(self):
        print("Proceso completado")
        self.botonElegirBiblioteca.setEnabled(True)
        QMessageBox.information(self, "Escaneo completado", "Se ha actualizado tu biblioteca de musica")
        
    def procesarCancionesEnLote(self, listaCancionesEncontradas):
        print(f"Escaneo completado. Se procesaron {len(listaCancionesEncontradas)} canciones")
        self.finalizarEscaneo()
        
    def conectarSignalsYSlots(self):
        self.botonElegirBiblioteca.clicked.connect(self.elegirBiblioteca)
        self.botonBuscar.clicked.connect(self.buscarEnBiblioteca)
        #self.botonFiltrarBusqueda.clicked.connect(self.filtrarBusqueda)
        self.botonCanciones.clicked.connect(self.mostrarCanciones)
        self.botonAlbumes.clicked.connect(self.mostrarAlbumes)
        self.botonArtistas.clicked.connect(self.mostrarArtistas)
        self.botonPlaylists.clicked.connect(self.mostrarPlaylists)
        self.botonFavoritos.clicked.connect(self.mostrarFavoritos)
        self.botonAleatorio.clicked.connect(self.reproducirAleatoriamente)
        self.botonCancionPrevia.clicked.connect(self.reproducirCancionPrevia)
        self.botonReproducirYPausar.clicked.connect(self.reproductor.reproducirYPausar)
        self.reproductor.stateChanged.connect(self.actualizarIconoReproduccion)
        self.botonCancionSiguiente.clicked.connect(self.reproducirCancionSiguiente)
        self.botonFavorito.clicked.connect(self.agregarAFavoritos)
        self.botonFavorito.toggled.connect(self.actualizarIconoFavorito)
        #self.botonMostrarLetra.clicked.connect(self.mostrarLetra)
        self.botonColaDeReproduccion.clicked.connect(self.mostrarColaDeReproduccion)
        self.listaCanciones.doubleClicked.connect(self.reproducirCancionSeleccionada)
        self.listaFavoritos.doubleClicked.connect(self.reproducirCancionSeleccionada)
        self.sliderVolumen.valueChanged.connect(self.reproductor.setVolume)
        self.barraProgresoCancion.sliderMoved.connect(self.reproductor.setPosition)
        self.reproductor.positionChanged.connect(self.actualizarPosicionSlider)
        self.reproductor.durationChanged.connect(self.actualizarRangoSlider)
        
    def buscarEnBiblioteca(self):
        textoBusqueda = self.barraDeBusqueda.text()
        print(f"Buscando: {textoBusqueda} en tu música")
        
        textoBusqueda = textoBusqueda.strip()
        
        if not textoBusqueda:
            print("La búsqueda no contiene texto alguno. No se buscará nada.")
            return
        
        resultados = self.managerDB.buscarCanciones(textoBusqueda)
        
        if resultados is None:
            self.listaCanciones.clear()
            self.listaCanciones.addItem("Error al realizar la búsqueda")
            self.listaCanciones.addItem("Problema de conexión con la base de datos")
            print("Error en la búsqueda - problema de BD")
            return
        
        self.datosCancionesActuales = resultados
        
        self.listaCanciones.clear()

        if not resultados:
            self.listaCanciones.addItem(f"No se encontraron canciones para '{textoBusqueda}'")
        else:
            for cancion in resultados:
                minutos = (cancion["duracion_segundos"] // 60)
                segundos = (cancion["duracion_segundos"] % 60)
                duracionFormateada = f"{minutos}:{segundos:02d}"
                
                tituloArtistaDuracion = f"{cancion['titulo_cancion']} - {cancion['artista']} - {duracionFormateada}"
                self.listaCanciones.addItem(tituloArtistaDuracion)

            self.paginas.setCurrentWidget(self.listaCanciones)
            print(f"{len(resultados)} canciones encontradas para '{textoBusqueda}'")            
        
    def mostrarCanciones(self):
        canciones = self.managerDB.obtenerTodasLasCanciones()
        
        if canciones is None:
            self.listaCanciones.clear()
            self.listaCanciones.addItem("Error al cargar canciones")
            self.listaCanciones.addItem("Problema de conexión con la base de datos")
            print("Error al cargar canciones")
            return
        
        self.datosCancionesActuales = canciones
        
        self.listaCanciones.clear()
        
        if not canciones:
            self.listaCanciones.addItem("No hay canciones en tu biblioteca")
            self.listaCanciones.addItem("")
            self.listaCanciones.addItem("Haz clic en 'Elegir biblioteca' para agregar música")
            print("No hay canciones en la biblioteca")
        else:
            for cancion in canciones:
                minutosCancion = (cancion["duracion_segundos"] // 60)
                segundosCancion = (cancion["duracion_segundos"] % 60)
                duracionFormateada = f"{minutosCancion}:{segundosCancion:02d}"
                datosCancionTexto = f"{cancion['titulo_cancion']} - {cancion['artista']} - {duracionFormateada}"
                self.listaCanciones.addItem(datosCancionTexto)

            self.paginas.setCurrentWidget(self.listaCanciones)
            print(f"Se agregaron {self.listaCanciones.count()} canciones")
        
    def mostrarAlbumes(self):
        albumes = self.managerDB.obtenerTodosLosAlbumes()
        
        if albumes is None:
            self.listaAlbumes.clear()
            self.listaAlbumes.addItem("Error al cargar álbumes")
            self.listaAlbumes.addItem("Problema de conexión con la base de datos")
            print("Error al cargar álbumes")
            return
    
        self.datosAlbumesActuales = albumes
        
        self.listaAlbumes.clear()
        
        if not albumes:
            self.listaAlbumes.addItem("No hay álbumes en tu biblioteca")
        else:
            for album in albumes:
                datosAlbumTexto = f"{album['titulo']} - {album['artista']}"
                self.listaAlbumes.addItem(datosAlbumTexto)
            
            self.paginas.setCurrentWidget(self.listaAlbumes)
            print(f"Se agregaron {self.listaAlbumes.count()} albumes a la vista actual")
    
    def mostrarArtistas(self):
        artistas = self.managerDB.obtenerTodosLosArtistas()
        
        if artistas is None:
            self.listaArtistas.clear()
            self.listaArtistas.addItem("Error al cargar artistas")
            self.listaArtistas.addItem("Problema de conexión con la base de datos")
            print("Error al cargar artistas")
            return
    
        self.datosArtistasActuales = artistas
        
        self.listaArtistas.clear()
        
        if not artistas:
            self.listaArtistas.addItem("No hay artistas en tu biblioteca")
        else:
            for artista in artistas:
                datosArtistaTexto = f"{artista['nombre']} ({artista['total_canciones']} canciones)"
                self.listaArtistas.addItem(datosArtistaTexto)
        
            self.paginas.setCurrentWidget(self.listaArtistas)
            print(f"Se agregaron {self.listaArtistas.count()} artistas a la vista actual")
            
    def mostrarPlaylists(self):
        self.listaPlaylists.clear()
        
        self.listaPlaylists.addItem("Playlists - Próximamente")
        self.listaPlaylists.addItem("")
        self.listaPlaylists.addItem("Esta funcionalidad estará disponible")
        self.listaPlaylists.addItem("en una futura actualización")
        
        self.paginas.setCurrentWidget(self.listaPlaylists)
        
    def mostrarFavoritos(self):
        cancionesFavoritas = self.managerDB.obtenerCancionesFavoritas()
        
        if cancionesFavoritas is None:
            self.listaFavoritos.clear()
            self.listaFavoritos.addItem("Error al cargar favoritos")
            self.listaFavoritos.addItem("Problema de conexión con la base de datos")
            print("Error al cargar favoritos")
            return
    
        self.datosFavoritosActuales = cancionesFavoritas
        
        self.listaFavoritos.clear()
        
        if not cancionesFavoritas:
            self.listaFavoritos.addItem("No tienes canciones favoritas aún")
            self.listaFavoritos.addItem("")
            self.listaFavoritos.addItem("Haz clic en el corazón ♡ en la barra inferior")
            self.listaFavoritos.addItem("para agregar canciones a favoritos")
            print("No hay canciones favoritas")
        else:
            for cancion in cancionesFavoritas:
                minutos = (cancion["duracion_segundos"] // 60)
                segundos = (cancion["duracion_segundos"] % 60)
                duracionFormateada = f"{minutos}:{segundos:02d}"
                
                textoItem = f"{cancion['titulo_cancion']} - {cancion['artista']} - {duracionFormateada}"
                self.listaFavoritos.addItem(textoItem)
            
            self.paginas.setCurrentWidget(self.listaFavoritos)
            print(f"Se mostraron {len(cancionesFavoritas)} canciones favoritas")
            
    def reproducirAleatoriamente(self):
        canciones = self.managerDB.obtenerTodasLasCanciones()
        
        if canciones is None:
            print("Error: No se pudieron cargar las canciones")
            return
            
        if not canciones:
            print("No hay canciones en la biblioteca para reproducir")
            return
        
        self.colaReproduccion = canciones.copy()
        random.shuffle(self.colaReproduccion)
        self.indiceCancionActual = 0
        
        cancionAleatoria = self.colaReproduccion[0]
        
        rutaCancion, titulo, artista = self.obtenerDatosCancion(cancionAleatoria)
    
        if not rutaCancion:
            return
        
        if rutaCancion and os.path.exists(rutaCancion):
            self.reproductor.cargarCancion(rutaCancion)
            self.reproductor.play()
            
            self.tituloCancion.setText(titulo)
            self.artistaCancion.setText(artista)
            
            self.actualizarEstadoFavorito(cancionAleatoria)
            
            print(f"Reproduciendo aleatoriamente: {titulo}")
        else:
            print(f"Error: Archivo no encontrado - {rutaCancion}")
        
        print(f"Cola configurada con {len(self.colaReproduccion)} canciones")
            
    def reproducirCancionSiguiente(self):
        if not self.colaReproduccion:
            print("No hay canciones en la cola de reproducción")
            return
        
        self.indiceCancionActual = (self.indiceCancionActual + 1) % len(self.colaReproduccion)
        
        cancionSiguiente = self.colaReproduccion[self.indiceCancionActual]
        
        rutaCancion, titulo, artista = self.obtenerDatosCancion(cancionSiguiente)
    
        if not rutaCancion:
            return
        
        if rutaCancion and os.path.exists(rutaCancion):
            self.reproductor.cargarCancion(rutaCancion)
            self.reproductor.play()
            
            self.tituloCancion.setText(titulo)
            self.artistaCancion.setText(artista)
            
            self.actualizarEstadoFavorito(cancionSiguiente)
        else:
            print(f"Error: Archivo no encontrado - {rutaCancion}")
        
        print(f"Siguiente canción: {titulo}")
        
    def reproducirCancionPrevia(self):
        if not self.colaReproduccion:
            print("No hay canciones en la cola de reproducción")
            return
        
        self.indiceCancionActual = (self.indiceCancionActual - 1) % len(self.colaReproduccion)
        
        cancionPrevia = self.colaReproduccion[self.indiceCancionActual]
        
        rutaCancion, titulo, artista = self.obtenerDatosCancion(cancionPrevia)
    
        if not rutaCancion:
            return
        
        if rutaCancion and os.path.exists(rutaCancion):
            self.reproductor.cargarCancion(rutaCancion)
            self.reproductor.play()
            
            self.tituloCancion.setText(titulo)
            self.artistaCancion.setText(artista)
            
            self.actualizarEstadoFavorito(cancionPrevia)
        else:
            print(f"Error: Archivo no encontrado - {rutaCancion}")
        
        print(f"Canción anterior: {titulo}")
        
    def reproducirCancionSeleccionada(self):
        listaEmisora = self.sender()
        
        if listaEmisora == self.listaCanciones:
            datos = self.datosCancionesActuales
        elif listaEmisora == self.listaFavoritos:
            datos = self.datosFavoritosActuales
        else:
            return
        
        indice = listaEmisora.currentRow() # type: ignore
        
        if indice < 0:
            print("No hay ninguna canción seleccionada")
            return
        
        if not datos:
            print("No hay canciones en esta lista")
            return
        
        cancionSeleccionada = datos[indice]
        
        rutaCancion, titulo, artista = self.obtenerDatosCancion(cancionSeleccionada)
    
        if not rutaCancion:
            return
        
        self.colaReproduccion = [cancionSeleccionada]
        self.indiceCancionActual = 0
        
        if rutaCancion and os.path.exists(rutaCancion):
            metadatosCancion = obtenerMetadatosCancion(artista, titulo)
            
            self.reproductor.cargarCancion(rutaCancion)
            self.reproductor.play()
            
            if metadatosCancion:
                print("Metadatos encontrados, actualizando UI con datos de Last.fm")
                self.tituloCancion.setText(metadatosCancion["nombreCancion"])
                self.artistaCancion.setText(metadatosCancion["nombreArtista"])
                self.albumCancion.setText(metadatosCancion["albumCancion"])
                self.generoCancion.setText(metadatosCancion["generoPrincipalCancion"])
                #self.bioArtistaCancion = metadatosCancion.get("bioArtistaResumida", "")
                
                urlPortada = metadatosCancion["urlPortadaAlbum"]
                if urlPortada:
                    self.solicitarPortada(urlPortada)
                else:
                    self.imagenCancion.setPixmap(QPixmap("assets/icons/turntable.svg"))
            
            else:
                print("API falló. Usando metadatos locales de la base de datos.")
                self.tituloCancion.setText(titulo)
                self.artistaCancion.setText(artista)
                self.albumCancion.setText("Álbum Desconocido")
                self.generoCancion.setText("Género Desconocido")
                #self.bioArtistaCancion.setText("")
                self.imagenCancion.setPixmap(QPixmap("assets/icons/turntable.svg"))
                
            self.actualizarEstadoFavorito(cancionSeleccionada)
            print(f"Reproduciendo: {titulo}")
        else:
            print(f"Error: Archivo no encontrado - {rutaCancion}")
            
    def obtenerDatosCancion(self, cancion):
        if "ruta_archivo" not in cancion.keys():
            print("Error: La canción no tiene información de ruta")
            return None, None, None
        
        if "titulo_cancion" not in cancion.keys():
            print("Error: La canción no tiene título")
            return None, None, None
        
        if "artista" not in cancion.keys():
            print("Error: La canción no tiene información de artista")
            return None, None, None
    
        return cancion["ruta_archivo"], cancion["titulo_cancion"], cancion["artista"]
        
    def agregarAFavoritos(self):
        if not self.colaReproduccion or self.indiceCancionActual == -1:
            print("No hay canción actual para agregar a favoritos")
            self.botonFavorito.setChecked(False) 
            return
        
        cancionActual = self.colaReproduccion[self.indiceCancionActual]
        
        rutaCancion, titulo, artista = self.obtenerDatosCancion(cancionActual)
    
        if not rutaCancion:
            return
    
        idCancion = self.managerDB.obtenerIdCancion(rutaCancion)
        
        if idCancion is None:
            print("Error: No se pudo encontrar la canción en la base de datos")
            return
        
        nuevoEstado = self.botonFavorito.isChecked()
            
        exito = self.managerDB.marcarComoFavorito(idCancion, nuevoEstado)
        
        if exito:
            if nuevoEstado:
                print(f"{titulo} de {artista} se agregó a favoritos")
            else:
                print(f"{titulo} de {artista} se removió de favoritos")
        else:
            print("Error al actualizar favoritos en la base de datos")
            self.botonFavorito.setChecked(not nuevoEstado)
            
    def actualizarEstadoFavorito(self, cancion):
        if cancion is None:
            return

        if cancion['es_favorito']:
            estadoInt = cancion['es_favorito']
        else:
            estadoInt = 0
        
        estadoBool = bool(estadoInt)

        self.botonFavorito.setChecked(estadoBool)
            
    def mostrarColaDeReproduccion(self):
        self.listaColaReproduccion.clear()
        
        if not self.colaReproduccion:
            self.listaColaReproduccion.addItem("Cola de reproducción vacía")
            self.listaColaReproduccion.addItem("")
            self.listaColaReproduccion.addItem("Haz clic en una canción")
            self.listaColaReproduccion.addItem("o en el botón de reproducción aleatoria")
            self.listaColaReproduccion.addItem("para comenzar a reproducir música")
        else:
            for posicion, cancion in enumerate(self.colaReproduccion):
                if cancion['duracion_segundos'] != 0:
                    duracion_segundos = cancion['duracion_segundos']
                else:
                    duracion_segundos = 0
                    
                minutos = duracion_segundos // 60
                segundos = duracion_segundos % 60
                duracionFormateada = f"{minutos}:{segundos:02d}"
                
                if posicion == self.indiceCancionActual:
                    texto = f"REPRODUCIENDO AHORA -> {cancion['titulo_cancion']} - {cancion['artista']} [{duracionFormateada}]"

                    textoResaltado = QListWidgetItem(texto)
                    textoResaltado.setBackground(QColor(200, 230, 255))
                    self.listaColaReproduccion.addItem(textoResaltado)
                else:
                    posicionParaUsuario = f"{posicion + 1}."
                    texto = f"Posición: {posicionParaUsuario} - {cancion['titulo_cancion']} de {cancion['artista']} [{duracionFormateada}]"
                    self.listaColaReproduccion.addItem(texto)
            
            self.listaColaReproduccion.addItem("")
            self.listaColaReproduccion.addItem(f"{len(self.colaReproduccion)} canciones en cola en total")
        
        self.paginas.setCurrentWidget(self.listaColaReproduccion)
        print("Mostrando cola de reproducción")
        
    def mostrarPortada(self, datosImagen):
        portada = QPixmap()
        
        portada.loadFromData(datosImagen)
        
        self.imagenCancion.setPixmap(portada)
        
    def solicitarPortada(self, url):
        if self.hiloDescarga and self.hiloDescarga.isRunning():
            self.hiloDescarga.quit()
            self.hiloDescarga.wait()
            
        self.hiloDescarga = QThread()
        self.trabajadorDescarga = ImageDownloader(url)
        self.trabajadorDescarga.moveToThread(self.hiloDescarga)
        
        self.hiloDescarga.started.connect(self.trabajadorDescarga.descargarImagen)
        
        self.trabajadorDescarga.imagenDescargada.connect(self.mostrarPortada)
        
        self.trabajadorDescarga.imagenDescargada.connect(self.hiloDescarga.quit)
        self.hiloDescarga.finished.connect(self.hiloDescarga.deleteLater)
        self.trabajadorDescarga.imagenDescargada.connect(self.trabajadorDescarga.deleteLater)
        
        self.hiloDescarga.finished.connect(self.limpiarHiloDescarga)
        
        self.hiloDescarga.start()
        
    def cargarEstilos(self, rutaArchivo):
        try:
            with open(rutaArchivo, "r") as archivo:
                estilo = archivo.read()
                self.setStyleSheet(estilo)
                print(f"Estilos de {rutaArchivo} cargados correctamente.")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo de estilos en {rutaArchivo}")
        except Exception as error:
            print(f"Error al cargar estilos: {error}")