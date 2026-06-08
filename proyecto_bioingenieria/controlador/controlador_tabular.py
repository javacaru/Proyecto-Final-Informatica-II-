import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QListWidgetItem,
    QTableWidgetItem, QVBoxLayout
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from modelo.datos_tabulares import TabularModel


class TabularController:
    def __init__(self, vista):
        self.modelo = TabularModel()
        self.vista = vista
        self.canvas = None
        self._conectar_signals()

    def _conectar_signals(self):
        self.vista.btn_cargar.clicked.connect(self._manejar_carga)
        self.vista.btn_plot.clicked.connect(self._manejar_plot)
        self.vista.btn_scatter.clicked.connect(self._manejar_scatter)

    def _manejar_carga(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self.vista, "Cargar archivo",
            "", "CSV (*.csv);;Excel (*.xlsx *.xls)"
        )
        if not ruta:
            return
        try:
            self.modelo.cargar_archivo(ruta)
            columnas = self.modelo.obtener_nombres_columnas()
            self.vista.lista_columnas.clear()
            for col in columnas:
                item = QListWidgetItem(col)
                item.setSelected(False)
                self.vista.lista_columnas.addItem(item)

            self.vista.combo_col1.clear()
            self.vista.combo_col2.clear()
            self.vista.combo_col1.addItems(columnas)
            self.vista.combo_col2.addItems(columnas)

            self._mostrar_info()
            self._mostrar_describe()

            QMessageBox.information(
                self.vista, "Exito",
                f"Archivo cargado: {self.modelo.datos.shape}"
            )
        except Exception as e:
            QMessageBox.critical(self.vista, "Error", str(e))

    def _mostrar_info(self):
        info = self.modelo.obtener_info()
        lineas = info.strip().split("\n")
        self.vista.tabla_info.setRowCount(len(lineas))
        self.vista.tabla_info.setColumnCount(1)
        self.vista.tabla_info.setHorizontalHeaderLabels(["Info()"])
        for i, linea in enumerate(lineas):
            self.vista.tabla_info.setItem(
            i, 0, QTableWidgetItem(linea)
        )

    def _mostrar_describe(self):
        df = self.modelo.obtener_describe()
        if df is None or df.empty:
            return
        self.vista.tabla_describe.setRowCount(df.shape[0])
        self.vista.tabla_describe.setColumnCount(df.shape[1] + 1)
        headers = ["Estadistica"] + list(df.columns)
        self.vista.tabla_describe.setHorizontalHeaderLabels(headers)
        for i, idx in enumerate(df.index):
            self.vista.tabla_describe.setItem(i, 0, QTableWidgetItem(str(idx)))
            for j, col in enumerate(df.columns):
                self.vista.tabla_describe.setItem(
                    i, j + 1, QTableWidgetItem(f"{df.loc[idx, col]:.4f}")
                )

    def _manejar_plot(self):
        items = self.vista.lista_columnas.selectedItems()
        if len(items) < 1:
            QMessageBox.warning(
                self.vista, "Aviso",
                "Seleccione al menos 1 columna para graficar"
            )
            return
        cols = [item.text() for item in items]
        n = len(cols)
        # altura dinámica: mínimo 3, máximo razonable
        alto = max(3, min(n * 2.5, 12))
        fig, axes = plt.subplots(n, 1, figsize=(8, alto))
        if n == 1:
            axes = [axes]
        for ax, col in zip(axes, cols):
            data = self.modelo.obtener_columna(col)
            if data is not None:
                ax.plot(data, linewidth=0.8)
                ax.set_title(f"Columna: {col}", fontsize=9)
                ax.set_xlabel("Índice", fontsize=8)
                ax.tick_params(labelsize=7)
        fig.tight_layout(pad=1.5)

        if self.canvas:
            self.canvas.deleteLater()
        self.canvas = FigureCanvasQTAgg(fig)
        ly = self.vista.frame_plot.layout()
        if ly is None:
            ly = QVBoxLayout(self.vista.frame_plot)
            self.vista.frame_plot.setLayout(ly)
        # limpiar widgets anteriores del layout
        while ly.count():
            w = ly.takeAt(0).widget()
            if w:
                w.deleteLater()
        ly.addWidget(self.canvas)
        self.canvas.draw()

    def _manejar_scatter(self):
        col1 = self.vista.combo_col1.currentText()
        col2 = self.vista.combo_col2.currentText()
        if not col1 or not col2:
            return
        x, y = self.modelo.obtener_scatter(col1, col2)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(x, y, alpha=0.85, s=30, color="#e63946", edgecolors="#1a1a1a", linewidths=0.3)
        ax.set_xlabel(col1, fontsize=10)
        ax.set_ylabel(col2, fontsize=10)
        ax.set_title(f"Scatter: {col1}  vs  {col2}", fontsize=11, pad=12)
        ax.tick_params(labelsize=8)
        ax.set_facecolor("#ffffff")
        fig.patch.set_facecolor("#e8f0e2")
        ax.spines["bottom"].set_color("#33691e")
        ax.spines["left"].set_color("#33691e")
        ax.spines["top"].set_color("#33691e")
        ax.spines["right"].set_color("#33691e")
        ax.xaxis.label.set_color("#1a1a1a")
        ax.yaxis.label.set_color("#1a1a1a")
        ax.title.set_color("#558b2f")
        ax.tick_params(colors="#1a1a1a")
        fig.tight_layout(pad=2)

        if self.canvas:
            self.canvas.deleteLater()
        self.canvas = FigureCanvasQTAgg(fig)
        ly = self.vista.frame_plot.layout()
        if ly is None:
            ly = QVBoxLayout(self.vista.frame_plot)
            self.vista.frame_plot.setLayout(ly)
        while ly.count():
            w = ly.takeAt(0).widget()
            if w:
                w.deleteLater()
        ly.addWidget(self.canvas)
        self.canvas.draw()
