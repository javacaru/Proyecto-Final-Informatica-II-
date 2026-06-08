import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog, QMainWindow, QWidget, QLabel, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage


def _ui_path(filename):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", filename)


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("welcome_dialog.ui"), self)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("login_dialog.ui"), self)


class CameraDialog(QDialog):
    foto_capturada = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("camera_dialog.ui"), self)
        self.timer = QTimer()
        self.frame_actual = None
        self.ruta_guardada = ""


class DialogoCarga(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("dialogo_carga.ui"), self)
        self.modo = None
        self.btn_carpeta.clicked.connect(lambda: self._aceptar("carpeta"))
        self.btn_archivo.clicked.connect(lambda: self._aceptar("archivo"))
        self.btn_imagen.clicked.connect(lambda: self._aceptar("imagen"))
        self.btn_cancelar.clicked.connect(self.reject)

    def _aceptar(self, modo):
        self.modo = modo
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("main_window.ui"), self)

        self.tab_dicom = DicomTabWidget()
        self.tab_senal = SignalTabWidget()
        self.tab_tabular = TabularTabWidget()

        self.tab_principal.addTab(self.tab_dicom, "Imagenes DICOM")
        self.tab_principal.addTab(self.tab_senal, "Senales")
        self.tab_principal.addTab(self.tab_tabular, "Datos Tabulares")


class DicomTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("dicom_tab.ui"), self)
        self._controlador = None

        self.combo_binarizacion.addItems([
            "Binario", "Binario Invertido", "Truncado",
            "Tozero", "Tozero Invertido"
        ])

        self.combo_morfologia.clear()
        self.combo_morfologia.addItems([
            "Apertura", "Cierre", "Gradiente", "Erosion", "Dilatacion"
        ])

        self.tabla_metadatos.setColumnCount(2)
        self.tabla_metadatos.setHorizontalHeaderLabels(["Propiedad", "Valor"])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._controlador is not None:
            self._controlador._refrescar_cortes()

    def mostrar_metadatos(self, metadatos):
        self.tabla_metadatos.setRowCount(len(metadatos))
        for i, (key, value) in enumerate(metadatos.items()):
            self.tabla_metadatos.setItem(
                i, 0, QTableWidgetItem(str(key))
            )
            self.tabla_metadatos.setItem(
                i, 1, QTableWidgetItem(str(value))
            )
        self.tabla_metadatos.resizeColumnsToContents()

    def mostrar_corte(self, label, array_gray):
        if array_gray is None:
            return
        import numpy as np
        arr = np.ascontiguousarray(array_gray)
        h, w = arr.shape
        qimg = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
        pix = QPixmap.fromImage(qimg)
        label.setPixmap(pix.scaled(
            label.width(), label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))


class SignalTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("signal_tab.ui"), self)

        self.combo_tipo_ruido.clear()
        self.combo_tipo_ruido.addItems(["gaussiano", "salt_pepper", "uniforme"])
        self.radio_eje_1.setChecked(True)


class TabularTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(_ui_path("tabular_tab.ui"), self)
