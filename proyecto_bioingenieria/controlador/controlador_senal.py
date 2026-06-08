import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from modelo.senal import SignalModel


class SenalController:
    def __init__(self, vista):
        self.modelo = SignalModel()
        self.vista = vista
        self.canvas = None
        self._max_muestras = None
        self._conectar_signals()

    def _conectar_signals(self):
        self.vista.btn_cargar.clicked.connect(self._manejar_carga)
        self.vista.btn_seleccionar_canales.clicked.connect(
            self._manejar_seleccion_canales
        )
        self.vista.btn_agregar_ruido.clicked.connect(self._manejar_ruido)
        self.vista.btn_calcular_stats.clicked.connect(self._manejar_stats)

    def _manejar_carga(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self.vista, "Cargar senal .mat", "", "MAT (*.mat)"
        )
        if not ruta:
            return
        try:
            self.modelo.cargar_mat(ruta)
            self.modelo.cambiar_a_2d()
            self.vista.spin_canal_inicio.setMaximum(
                self.modelo.datos_2d.shape[1] - 1
            )
            self.vista.spin_canal_fin.setMaximum(
                self.modelo.datos_2d.shape[1] - 1
            )
            self.vista.spin_canal_fin.setValue(
                min(1000, self.modelo.datos_2d.shape[1] - 1)
            )
            self.vista.spin_canal_ruido.setMaximum(
                self.modelo.datos_2d.shape[0] - 1
            )
            self._graficar_senal_completa()
            QMessageBox.information(
                self.vista, "Exito",
                f"Senal cargada: {self.modelo.datos_3d.shape} -> "
                f"{self.modelo.datos_2d.shape}"
            )
        except Exception as e:
            QMessageBox.critical(self.vista, "Error", str(e))

    def _graficar_senal_completa(self):
        if self.modelo.datos_2d is None:
            return
        n_total = self.modelo.datos_2d.shape[1]
        n_mostrar = self._max_muestras or n_total
        fig, ax = plt.subplots(figsize=(8, 3))
        for i in range(min(5, self.modelo.datos_2d.shape[0])):
            ax.plot(
                self.modelo.datos_2d[i, :n_mostrar],
                label=self.modelo.nombres_canales[i]
            )
        ax.set_title(f"Senal completa ({n_mostrar} muestras)")
        ax.legend(fontsize=6)
        ax.set_xlabel("Muestras")
        ax.set_ylabel("Amplitud")
        fig.tight_layout()

        if self.canvas:
            self.canvas.deleteLater()
        self.canvas = FigureCanvasQTAgg(fig)
        ly = self.vista.frame_senal.layout()
        if ly is None:
            ly = QVBoxLayout(self.vista.frame_senal)
            self.vista.frame_senal.setLayout(ly)
        ly.addWidget(self.canvas)
        self.canvas.draw()

    def _manejar_seleccion_canales(self):
        if self.modelo.datos_2d is None:
            QMessageBox.warning(self.vista, "Error",
                                "Cargue una senal primero")
            return
        inicio = self.vista.spin_canal_inicio.value()
        fin = self.vista.spin_canal_fin.value()
        if inicio >= fin:
            QMessageBox.warning(self.vista, "Error",
                                "Inicio debe ser menor que Fin")
            return
        segmento = self.modelo.seleccionar_canales(inicio, fin)
        eje_x = np.arange(inicio, fin)

        fig, ax = plt.subplots(figsize=(8, 3))
        ax.clear()
        for i in range(min(5, segmento.shape[0])):
            ax.plot(eje_x, segmento[i], label=self.modelo.nombres_canales[i])
        ax.set_xlim(inicio, fin)
        ax.set_title(f"Canales [{inicio}:{fin}]")
        ax.set_xlabel("Muestras")
        ax.set_ylabel("Amplitud")
        ax.legend(fontsize=6)
        fig.tight_layout()

        if self.canvas:
            self.canvas.deleteLater()
        self.canvas = FigureCanvasQTAgg(fig)
        ly = self.vista.frame_senal.layout()
        if ly is None:
            ly = QVBoxLayout(self.vista.frame_senal)
            self.vista.frame_senal.setLayout(ly)
        ly.addWidget(self.canvas)
        self.canvas.draw()

    @staticmethod
    def _limpiar_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _manejar_ruido(self):
        if self.modelo.datos_2d is None:
            QMessageBox.warning(self.vista, "Error",
                                "Cargue una senal primero")
            return
        canal = self.vista.spin_canal_ruido.value()
        if canal >= self.modelo.datos_2d.shape[0]:
            QMessageBox.warning(self.vista, "Error",
                                "Canal fuera de rango")
            return
        tipo = self.vista.combo_tipo_ruido.currentText()
        original, modificada = self.modelo.agregar_ruido(canal, tipo)
        n_total = original.shape[0]
        n_mostrar = self._max_muestras or n_total

        fig_orig, ax_orig = plt.subplots(figsize=(6, 3))
        ax_orig.plot(original[:n_mostrar], color="#33691e")
        ax_orig.set_title(f"Original - {self.modelo.nombres_canales[canal]}")
        ax_orig.set_xlabel("Muestras")
        ax_orig.set_ylabel("Amplitud")
        fig_orig.tight_layout()

        fig_mod, ax_mod = plt.subplots(figsize=(6, 3))
        ax_mod.plot(modificada[:n_mostrar], color="#e63946")
        ax_mod.set_title(f"Modificada con ruido {tipo}")
        ax_mod.set_xlabel("Muestras")
        ax_mod.set_ylabel("Amplitud")
        fig_mod.tight_layout()

        if hasattr(self, '_canvas_orig') and self._canvas_orig:
            self._canvas_orig.deleteLater()
        if hasattr(self, '_canvas_mod') and self._canvas_mod:
            self._canvas_mod.deleteLater()

        self._canvas_orig = FigureCanvasQTAgg(fig_orig)
        ly_orig = self.vista.frame_original.layout()
        if ly_orig is None:
            ly_orig = QVBoxLayout(self.vista.frame_original)
            self.vista.frame_original.setLayout(ly_orig)
        self._limpiar_layout(ly_orig)
        ly_orig.addWidget(self._canvas_orig)
        self._canvas_orig.draw()

        self._canvas_mod = FigureCanvasQTAgg(fig_mod)
        ly_mod = self.vista.frame_modificada.layout()
        if ly_mod is None:
            ly_mod = QVBoxLayout(self.vista.frame_modificada)
            self.vista.frame_modificada.setLayout(ly_mod)
        self._limpiar_layout(ly_mod)
        ly_mod.addWidget(self._canvas_mod)
        self._canvas_mod.draw()

    def _manejar_stats(self):
        if self.modelo.datos_3d is None:
            QMessageBox.warning(self.vista, "Error",
                                "Cargue una senal primero")
            return
        if self.vista.radio_eje_0.isChecked():
            eje = 0
        elif self.vista.radio_eje_1.isChecked():
            eje = 1
        else:
            eje = 2
        try:
            prom = self.modelo.calcular_promedio(eje)
            desv = self.modelo.calcular_desviacion(eje)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4))
            ax1.stem(prom.flatten()[:100], linefmt="#33691e",
                     markerfmt="o")
            ax1.set_title(f"Promedio (eje {eje})")
            ax2.stem(desv.flatten()[:100], linefmt="#e63946",
                     markerfmt="o")
            ax2.set_title(f"Desviacion Estandar (eje {eje})")
            fig.tight_layout()

            if self.canvas:
                self.canvas.deleteLater()
            self.canvas = FigureCanvasQTAgg(fig)
            ly = self.vista.frame_senal.layout()
            if ly is None:
                ly = QVBoxLayout(self.vista.frame_senal)
                self.vista.frame_senal.setLayout(ly)
            ly.addWidget(self.canvas)
            self.canvas.draw()
        except Exception as e:
            QMessageBox.critical(self.vista, "Error", str(e))
