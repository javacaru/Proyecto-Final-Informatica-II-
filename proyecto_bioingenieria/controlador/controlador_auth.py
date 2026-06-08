import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage
from modelo.base_datos import BaseDatosModel
from modelo.camara import CamaraModel
from vista.ventanas import WelcomeDialog, LoginDialog, CameraDialog
from controlador.controlador_imagen import ImagenController
from controlador.controlador_senal import SenalController
from controlador.controlador_tabular import TabularController


class AuthController:
    def __init__(self):
        self.modelo_db = BaseDatosModel()
        self.modelo_cam = CamaraModel()
        self.vista_welcome = WelcomeDialog()
        self.vista_login = LoginDialog()
        self.vista_camara = CameraDialog()
        self.vista_main = None
        self.imagen_ctrl = None
        self.senal_ctrl = None
        self.tabular_ctrl = None
        self.usuario_actual = None

        self._conectar_signals()

    def _conectar_signals(self):
        self.vista_welcome.btn_ingresar.clicked.connect(self._ir_a_login)
        self.vista_login.btn_login.clicked.connect(self._manejar_login)
        self.vista_login.btn_cancelar.clicked.connect(self.vista_login.close)
        self.vista_camara.btn_capturar.clicked.connect(self._capturar_foto)
        self.vista_camara.btn_aceptar.clicked.connect(self._aceptar_foto)
        self.vista_camara.btn_cancelar.clicked.connect(self._cancelar_camara)

    def iniciar(self):
        if not self.modelo_db.conectar():
            QMessageBox.critical(None, "Error",
                                 "No se pudo conectar a la base de datos")
            return
        self.modelo_db.crear_tablas()
        self.vista_welcome.exec_()

    def _ir_a_login(self):
        self.vista_welcome.close()
        self.vista_login.lbl_error.setText("")
        self.vista_login.exec_()

    def _manejar_login(self):
        user_id = self.vista_login.txt_id.text().strip()
        password = self.vista_login.txt_password.text().strip()
        if not user_id or not password:
            self.vista_login.lbl_error.setText("Complete todos los campos")
            return
        usuario = self.modelo_db.validar_usuario(user_id, password)
        if usuario:
            self.usuario_actual = usuario
            self.vista_login.close()
            self._abrir_camara()
        else:
            self.vista_login.lbl_error.setText(
                "ID o contrasena incorrectos"
            )

    def _abrir_camara(self):
        if not self.modelo_cam.iniciar():
            QMessageBox.warning(None, "Error", "No se pudo acceder a la camara")
            self._abrir_principal()
            return
        self.vista_camara.timer.timeout.connect(self._actualizar_video)
        self.vista_camara.timer.start(30)
        self.vista_camara.exec_()

    def _actualizar_video(self):
        frame = self.modelo_cam.capturar_foto()
        if frame is not None:
            self.vista_camara.frame_actual = frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            self.vista_camara.lbl_video.setPixmap(pix.scaled(
                self.vista_camara.lbl_video.width(),
                self.vista_camara.lbl_video.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def _capturar_foto(self):
        if self.vista_camara.frame_actual is not None:
            ruta = os.path.join(
                os.path.dirname(__file__), "..", "assets",
                f"foto_{self.usuario_actual['id']}.jpg"
            )
            self.modelo_cam.guardar_foto(
                self.vista_camara.frame_actual, ruta
            )
            self.vista_camara.ruta_guardada = ruta
            QMessageBox.information(self.vista_camara, "Exito",
                                    "Foto capturada correctamente")

    def _aceptar_foto(self):
        self.vista_camara.timer.stop()
        self.modelo_cam.liberar()

        if self.vista_camara.ruta_guardada:
            self.modelo_db.guardar_sesion(
                self.usuario_actual["id"],
                self.vista_camara.ruta_guardada
            )
        self.vista_camara.close()
        self._abrir_principal()

    def _cancelar_camara(self):
        self.vista_camara.timer.stop()
        self.modelo_cam.liberar()
        self.vista_camara.close()
        self._abrir_principal()

    def _abrir_principal(self):
        from vista.ventanas import MainWindow
        self.vista_main = MainWindow()
        self.vista_main.lbl_usuario.setText(
            f"👤  {self.usuario_actual['nombre']}  |  {self.usuario_actual['rol'].capitalize()}"
        )
        self.imagen_ctrl = ImagenController(
            self.vista_main.tab_dicom
        )
        self.senal_ctrl = SenalController(
            self.vista_main.tab_senal
        )
        self.tabular_ctrl = TabularController(
            self.vista_main.tab_tabular
        )
        self.vista_main.show()
