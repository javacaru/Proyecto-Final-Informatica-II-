import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from modelo.imagen import DICOMModel
from vista.ventanas import DialogoCarga


class ImagenController:
    def __init__(self, vista):
        self.modelo = DICOMModel()
        self.vista = vista
        self.canvas_zoom = None
        self.canvas_procesado = None
        self.ultimo_recorte = None
        self.vista._controlador = self
        self._conectar_signals()

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    def _conectar_signals(self):
        self.vista.btn_cargar.clicked.connect(self._manejar_carga)
        self.vista.slider_sagital.valueChanged.connect(
            lambda v: self._actualizar_corte("sagital", v)
        )
        self.vista.slider_coronal.valueChanged.connect(
            lambda v: self._actualizar_corte("coronal", v)
        )
        self.vista.slider_axial.valueChanged.connect(
            lambda v: self._actualizar_corte("axial", v)
        )
        self.vista.btn_zoom.clicked.connect(self._manejar_zoom)
        self.vista.btn_segmentar.clicked.connect(self._manejar_binarizacion)
        self.vista.btn_morfologia.clicked.connect(self._manejar_morfologia)
        self.vista.btn_convertir_nifti.clicked.connect(self._manejar_convertir_nifti)

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def _manejar_carga(self):
        dlg = DialogoCarga(self.vista)
        if dlg.exec_() != DialogoCarga.Accepted or dlg.modo is None:
            return

        ruta = ""
        if dlg.modo == "carpeta":
            ruta = QFileDialog.getExistingDirectory(
                self.vista, "Seleccionar carpeta DICOM"
            )
        elif dlg.modo == "archivo":
            ruta, _ = QFileDialog.getOpenFileName(
                self.vista, "Seleccionar archivo DICOM",
                "", "DICOM (*.dcm);;Todos (*)"
            )
        elif dlg.modo == "imagen":
            ruta, _ = QFileDialog.getOpenFileName(
                self.vista, "Seleccionar imagen",
                "", "Imágenes (*.jpg *.jpeg *.png *.bmp *.tiff)"
            )

        if not ruta:
            return

        try:
            self.modelo.cargar_dicom(ruta)
            self.vista.mostrar_metadatos(self.modelo.metadatos)

            base_dir = ruta if os.path.isdir(ruta) else os.path.dirname(ruta)
            self.modelo.guardar_metadatos_csv(os.path.join(base_dir, "metadatos.csv"))

            shape = self.modelo.matriz_uint8.shape  # (Z, Y, X)
            self.vista.slider_axial.setMaximum(shape[0] - 1)
            self.vista.slider_coronal.setMaximum(shape[1] - 1)
            self.vista.slider_sagital.setMaximum(shape[2] - 1)
            self.vista.slider_axial.setValue(shape[0] // 2)
            self.vista.slider_coronal.setValue(shape[1] // 2)
            self.vista.slider_sagital.setValue(shape[2] // 2)

            # Ajustar máximos de los spinboxes al tamaño real de la imagen
            self.vista.spin_center_x.setMaximum(shape[2] - 1)
            self.vista.spin_center_y.setMaximum(shape[1] - 1)
            self.vista.spin_width.setMaximum(shape[2])
            self.vista.spin_height.setMaximum(shape[1])
            # Centrar el recorte por defecto
            self.vista.spin_center_x.setValue(shape[2] // 2)
            self.vista.spin_center_y.setValue(shape[1] // 2)

            QMessageBox.information(
                self.vista, "Éxito",
                f"Imagen cargada: {self.modelo.matriz_3d.shape}"
            )
        except Exception as e:
            QMessageBox.critical(self.vista, "Error", str(e))

    # ------------------------------------------------------------------
    # Cortes
    # ------------------------------------------------------------------
    def _refrescar_cortes(self):
        if self.modelo.matriz_uint8 is None:
            return
        self._actualizar_corte("sagital", self.vista.slider_sagital.value())
        self._actualizar_corte("coronal",  self.vista.slider_coronal.value())
        self._actualizar_corte("axial",    self.vista.slider_axial.value())

    def _actualizar_corte(self, eje, idx):
        if self.modelo.matriz_uint8 is None:
            return
        cortes = {
            "sagital": (self.vista.lbl_sagital, self.modelo.obtener_corte_sagital),
            "coronal": (self.vista.lbl_coronal, self.modelo.obtener_corte_coronal),
            "axial":   (self.vista.lbl_axial,   self.modelo.obtener_corte_axial),
        }
        lbl, fn = cortes[eje]
        self.vista.mostrar_corte(lbl, fn(idx))

    # ------------------------------------------------------------------
    # Zoom  — lee los 4 valores directamente del .ui
    # ------------------------------------------------------------------
    def _manejar_zoom(self):
        if self.modelo.matriz_3d is None:
            QMessageBox.warning(self.vista, "Error", "Cargue un DICOM primero")
            return

        shape = self.modelo.matriz_3d.shape  # (Z, Y, X)

        cx = min(self.vista.spin_center_x.value(), shape[2] - 1)
        cy = min(self.vista.spin_center_y.value(), shape[1] - 1)
        tw = min(self.vista.spin_width.value(),    shape[2])
        th = min(self.vista.spin_height.value(),   shape[1])

        recorte, bbox = self.modelo.recortar_zoom((cx, cy), (tw, th))
        self.ultimo_recorte = recorte

        idx_axial  = shape[0] // 2
        original   = self.modelo.matriz_uint8[idx_axial]
        img_color  = self.modelo.dibujar_rectangulo(original, bbox)

        recorte_norm  = self.modelo.normalizar_uint8(np.expand_dims(recorte, 0))[0]
        recorte_redim = cv2.resize(recorte_norm, (200, 200), interpolation=cv2.INTER_LINEAR)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))
        ax1.imshow(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB))
        ax1.set_title("Original con recuadro")
        ax1.axis("off")
        ax2.imshow(recorte_redim, cmap="gray")
        ax2.set_title(f"Recorte {recorte_redim.shape}")
        ax2.axis("off")

        self._mostrar_canvas(fig, self.vista.frame_original, "canvas_zoom")

    # ------------------------------------------------------------------
    # Segmentación / Morfología
    # ------------------------------------------------------------------
    def _manejar_binarizacion(self):
        if self.ultimo_recorte is None:
            QMessageBox.warning(self.vista, "Error", "Haga ZOOM primero")
            return

        metodo  = self.vista.combo_binarizacion.currentText()
        r_norm  = self.modelo.normalizar_uint8(np.expand_dims(self.ultimo_recorte, 0))[0]
        res     = self.modelo.binarizar(r_norm, metodo)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))
        ax1.imshow(r_norm, cmap="gray");  ax1.set_title("Original");           ax1.axis("off")
        ax2.imshow(res,    cmap="gray");  ax2.set_title(f"Binarizacion: {metodo}"); ax2.axis("off")

        self._mostrar_canvas(fig, self.vista.frame_recorte, "canvas_procesado")

    def _manejar_morfologia(self):
        if self.ultimo_recorte is None:
            QMessageBox.warning(self.vista, "Error", "Haga ZOOM primero")
            return

        kernel = self.vista.spin_kernel.value()
        tipo   = self.vista.combo_morfologia.currentText()
        r_norm = self.modelo.normalizar_uint8(np.expand_dims(self.ultimo_recorte, 0))[0]
        res    = self.modelo.transformar_morfologica(r_norm, kernel, tipo)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))
        ax1.imshow(r_norm, cmap="gray"); ax1.set_title("Original");                    ax1.axis("off")
        ax2.imshow(res,    cmap="gray"); ax2.set_title(f"Morfologia: {tipo} (k={kernel})"); ax2.axis("off")

        self._mostrar_canvas(fig, self.vista.frame_recorte, "canvas_procesado")

    # ------------------------------------------------------------------
    # NIfTI
    # ------------------------------------------------------------------
    def _manejar_convertir_nifti(self):
        if self.modelo.matriz_3d is None:
            QMessageBox.warning(self.vista, "Error", "Cargue un DICOM primero")
            return
        ruta, _ = QFileDialog.getSaveFileName(self.vista, "Guardar NIFTI", "", "NIFTI (*.nii)")
        if ruta:
            try:
                self.modelo.convertir_nifti(ruta)
                QMessageBox.information(self.vista, "Exito", f"NIFTI: {ruta}")
            except Exception as e:
                QMessageBox.critical(self.vista, "Error", str(e))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _mostrar_canvas(self, fig, frame, atributo):
        """Inserta un FigureCanvasQTAgg dentro de un QFrame del .ui."""
        canvas_viejo = getattr(self, atributo, None)
        if canvas_viejo:
            canvas_viejo.deleteLater()

        canvas = FigureCanvasQTAgg(fig)
        setattr(self, atributo, canvas)

        ly = frame.layout()
        if ly is None:
            ly = QVBoxLayout(frame)
            frame.setLayout(ly)
        else:
            self._limpiar_layout(ly)

        ly.addWidget(canvas)
        canvas.draw()

    @staticmethod
    def _limpiar_layout(layout):
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
