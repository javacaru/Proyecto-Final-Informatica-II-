import hashlib
import mysql.connector
from mysql.connector import Error
import datetime


class BaseDatosModel:
    def __init__(self, host="localhost", user="root1", password="4321", database="biomedica"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conexion = None

    @staticmethod
    def _hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def conectar(self):
        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return self.conexion.is_connected()
        except Error as e:
            print(f"Error de conexion: {e}")
            return False

    def crear_tablas(self):
        if not self.conexion or not self.conexion.is_connected():
            return False
        cursor = self.conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                rol VARCHAR(20) NOT NULL DEFAULT 'usuario'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_usuario VARCHAR(50),
                ruta_foto VARCHAR(255),
                fecha DATETIME,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
            )
        """)
        self.conexion.commit()
        cursor.close()

        cursor = self.conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("""
                INSERT INTO usuarios (id, nombre, password, rol) VALUES
                (%s, %s, %s, %s),
                (%s, %s, %s, %s),
                (%s, %s, %s, %s)
            """, (
                'admin', 'Administrador', self._hash_password('1234'), 'administrador',
                'user1', 'Usuario 1', self._hash_password('1234'), 'usuario',
                'user2', 'Usuario 2', self._hash_password('1234'), 'usuario'
            ))
            self.conexion.commit()
        cursor.close()
        return True

    def validar_usuario(self, user_id, password):
        if not self.conexion or not self.conexion.is_connected():
            return None
        cursor = self.conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, rol FROM usuarios WHERE id = %s AND password = %s",
            (user_id, self._hash_password(password))
        )
        usuario = cursor.fetchone()
        cursor.close()
        return usuario

    def guardar_sesion(self, id_usuario, ruta_foto):
        if not self.conexion or not self.conexion.is_connected():
            return False
        cursor = self.conexion.cursor()
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO sesiones (id_usuario, ruta_foto, fecha) VALUES (%s, %s, %s)",
            (id_usuario, ruta_foto, fecha)
        )
        self.conexion.commit()
        cursor.close()
        return True

    def cerrar(self):
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()
