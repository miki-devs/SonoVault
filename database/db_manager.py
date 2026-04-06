import sqlite3
from sqlite3 import Error
import os

class DatabaseManager:
    def __init__(self, databasePath=None):

        if databasePath is None:
            currentDir = os.path.dirname(os.path.abspath(__file__))
            self.databasePath = os.path.join(currentDir, "sonovault.db")
        else:
            self.databasePath = databasePath
            
        self.conexion = None
        
    def conectar(self):
        try:
            os.makedirs(os.path.dirname(self.databasePath), exist_ok=True)
            
            self.conexion = sqlite3.connect(self.databasePath)
            self.conexion.row_factory = sqlite3.Row
            print(f"Conexión a SQLite exitosa: {self.databasePath}")
            return True
        except Error as errorConexion:
            print(f"Error al conectar a la base de datos: {errorConexion}")
            return False
        
    def desconectar(self):
        if self.conexion:
            self.conexion.close()
            
    def intentarConectar(self):
        if not self.conexion:
            print("Intentando conectar a la base de datos...")
            conexionExitosa = self.conectar()
            if not conexionExitosa:
                print("Error: No se pudo establecer conexión a la BD")
                return False
        return True
            
    def crearTablas(self):
        if not self.conectar():
            return False
            
        try:
            cursor = self.conexion.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS artistas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS albumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    id_artista INTEGER,
                    FOREIGN KEY (id_artista) REFERENCES artistas (id),
                    UNIQUE(titulo, id_artista)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS canciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    id_artista INTEGER,
                    id_album INTEGER,
                    ruta_archivo TEXT UNIQUE,
                    duracion_segundos INTEGER,
                    es_favorito INTEGER DEFAULT 0,
                    FOREIGN KEY (id_artista) REFERENCES artistas (id),
                    FOREIGN KEY (id_album) REFERENCES albumes (id)
                )
            ''')
            
            self.conexion.commit()
            print("Tablas creadas exitosamente")
            return True
            
        except Error as error:
            print(f"Error creando tablas: {error}")
            return False
        finally:
            if cursor:
                cursor.close()
            
    def agregarCancion(self, datosCancion):
        if not self.conexion:
            if not self.conectar():
                print("Error: No se pudo establecer la conexión a la base de datos. La canción no será agregada.")
                return False
                
        cursor = self.conexion.cursor()
        
        try:
            nombreArtista = datosCancion.get("artista", "Artista Desconocido")
            
            consultaBuscarArtista = "SELECT id FROM artistas WHERE nombre = ?"
            cursor.execute(consultaBuscarArtista, (nombreArtista,))
            resultadoArtista = cursor.fetchone()
            if resultadoArtista:
                idArtista = resultadoArtista['id']
            else:
                consultaInsertarArtista = "INSERT INTO artistas (nombre) VALUES (?)"
                cursor.execute(consultaInsertarArtista, (nombreArtista,))
                idArtista = cursor.lastrowid
                
            tituloAlbum = datosCancion.get("album", "Álbum Desconocido")
            consultaBuscarAlbum = "SELECT id FROM albumes WHERE titulo = ? AND id_artista = ?"
            cursor.execute(consultaBuscarAlbum, (tituloAlbum, idArtista))
            resultadoAlbum = cursor.fetchone()
            if resultadoAlbum:
                idAlbum = resultadoAlbum['id']
            else:
                consultaInsertarAlbum = "INSERT INTO albumes (titulo, id_artista) VALUES (?, ?)"
                cursor.execute(consultaInsertarAlbum, (tituloAlbum, idArtista))
                idAlbum = cursor.lastrowid
                
            tituloCancion = datosCancion.get("titulo", "Canción Desconocida")
            rutaCancion = datosCancion.get("ruta_archivo")
            duracionCancion = datosCancion.get("duracion_segundos", 0)
            
            if not rutaCancion:
                raise ValueError("La ruta del archivo de la canción no existe, será omitida.")
            
            consultaInsertarCancion = """
                INSERT OR REPLACE INTO canciones 
                (titulo, id_artista, id_album, ruta_archivo, duracion_segundos)
                VALUES (?, ?, ?, ?, ?)
            """
            valoresCancion = (tituloCancion, idArtista, idAlbum, rutaCancion, duracionCancion)
            cursor.execute(consultaInsertarCancion, valoresCancion)
            self.conexion.commit()
            print(f"Canción '{tituloCancion}' agregada exitosamente")
            return True
            
        except Error as errorAgregar:
            print(f"Error en la modificación de la base de datos: {errorAgregar}")
            self.conexion.rollback()
            return False
        except Exception as e:
            print(f"Error inesperado: {e}")
            self.conexion.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
                
    def obtenerTodasLasCanciones(self):
        if not self.intentarConectar():
            return None
            
        cursor = self.conexion.cursor()
        
        try:
            consultaMostrarInfoCancion = """
                SELECT
                    c.titulo AS titulo_cancion, c.duracion_segundos, c.es_favorito, c.ruta_archivo,
                    ar.nombre AS artista,
                    al.titulo as album
                FROM canciones c
                LEFT JOIN artistas ar ON c.id_artista = ar.id
                LEFT JOIN albumes al ON c.id_album = al.id
                ORDER BY ar.nombre, al.titulo, c.titulo
            """
            
            cursor.execute(consultaMostrarInfoCancion)
            cancionesEncontradas = cursor.fetchall()
            return cancionesEncontradas
        except Error as error:
            print(f"Error al obtener canciones: {error}")
            return None
        finally:
            if cursor:
                cursor.close()
                
    def obtenerTodosLosArtistas(self):
        if not self.intentarConectar():
            return None
            
        cursor = self.conexion.cursor()
        
        try:
            consultaMostrarInfoArtistas = """
                SELECT
                    a.id,
                    a.nombre, 
                    COUNT(c.id) AS total_canciones
                FROM artistas a
                LEFT JOIN canciones c ON a.id = c.id_artista
                GROUP BY a.id, a.nombre
                ORDER BY a.nombre
            """
            
            cursor.execute(consultaMostrarInfoArtistas)
            artistasEncontrados = cursor.fetchall()
            return artistasEncontrados
        except Error as error:
            print(f"Error al obtener artistas: {error}")
            return None
        finally:
            if cursor:
                cursor.close()
                
    def obtenerTodosLosAlbumes(self):
        if not self.intentarConectar():
            return None
            
        cursor = self.conexion.cursor()
        
        try:
            consultaMostrarInfoAlbumes = """
                SELECT
                    al.id,
                    al.titulo AS titulo,
                    ar.nombre AS artista
                FROM albumes al
                LEFT JOIN artistas ar ON al.id_artista = ar.id
                ORDER BY al.titulo, ar.nombre
            """
            
            cursor.execute(consultaMostrarInfoAlbumes)
            albumesEncontrados = cursor.fetchall()
            return albumesEncontrados
        except Error as error:
            print(f"Error al obtener albumes: {error}")
            return None
        finally:
            if cursor:
                cursor.close()
                
    def buscarCanciones(self, textoBusqueda):
        if not self.intentarConectar():
            return None
            
        cursor = self.conexion.cursor()
        
        try:
            consultaBuscarCancion = """
                SELECT
                    c.titulo AS titulo_cancion, c.duracion_segundos, c.ruta_archivo,
                    ar.nombre AS artista,
                    al.titulo AS album
                FROM canciones c
                LEFT JOIN artistas ar ON c.id_artista = ar.id
                LEFT JOIN albumes al ON c.id_album = al.id
                WHERE c.titulo LIKE ? OR ar.nombre LIKE ? OR al.titulo LIKE ?
                ORDER BY ar.nombre, c.titulo
            """
            parametroBusqueda = f"%{textoBusqueda}%"
            cursor.execute(consultaBuscarCancion, (parametroBusqueda, parametroBusqueda, parametroBusqueda))
            
            listaCanciones = cursor.fetchall()
            
            return listaCanciones
        except Error as error:
            print(f"Error en la búsqueda: {error}")
            return None
        finally:
            if cursor:
                cursor.close()
                
    def obtenerCancionesFavoritas(self):
        if not self.intentarConectar():
            return None
            
        cursor = self.conexion.cursor()
        
        try:
            consulta = """
                SELECT
                    c.titulo AS titulo_cancion, c.duracion_segundos, c.es_favorito, c.ruta_archivo,
                    ar.nombre AS artista,
                    al.titulo AS album
                FROM canciones c
                LEFT JOIN artistas ar ON c.id_artista = ar.id
                LEFT JOIN albumes al ON c.id_album = al.id
                WHERE c.es_favorito = 1
                ORDER BY ar.nombre, c.titulo
            """
            
            cursor.execute(consulta)
            cancionesFavoritas = cursor.fetchall()
            return cancionesFavoritas
            
        except Error as error:
            print(f"Error al obtener canciones favoritas: {error}")
            return None
        finally:
            if cursor:
                cursor.close()
                
    def obtenerIdCancion(self, ruta_archivo):
        if not self.intentarConectar():
            return None
            
        cursor = self.conexion.cursor()
        try:
            cursor.execute("SELECT id FROM canciones WHERE ruta_archivo = ?", (ruta_archivo,))
            resultado = cursor.fetchone()
            if resultado:
                return resultado["id"]
            else:
                return None
        except Error as e:
            print(f"Error obteniendo ID de canción: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def marcarComoFavorito(self, id_cancion, es_favorito):
        if not self.intentarConectar():
            return False
            
        cursor = self.conexion.cursor()
        
        try:
            consultaFavorito = "UPDATE canciones SET es_favorito = ? WHERE id = ?"
            
            if es_favorito:
                valor_favorito = 1
            else:
                valor_favorito = 0
            
            cursor.execute(consultaFavorito, (valor_favorito, id_cancion))
            self.conexion.commit()
            return True
        except Error as error:
            print(f"Error actualizando favorito: {error}")
            self.conexion.rollback()
            return False
        finally:
            if cursor:
                cursor.close()