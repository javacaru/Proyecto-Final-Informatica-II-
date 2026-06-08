import pandas as pd
import numpy as np
from io import StringIO


class TabularModel:
    def __init__(self):
        self.ruta = ""
        self.datos = None
        self.info_str = ""
        self.describe_df = None

    def cargar_archivo(self, ruta):
        self.ruta = ruta
        if ruta.endswith('.csv'):
            self.datos = pd.read_csv(ruta)
        elif ruta.endswith('.xlsx') or ruta.endswith('.xls'):
            self.datos = pd.read_excel(ruta)
        else:
            raise ValueError("Formato no soportado. Use .csv o .xlsx")

        buffer = StringIO()
        self.datos.info(buf=buffer)
        self.info_str = buffer.getvalue()

        numeric_cols = self.datos.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            self.describe_df = self.datos[numeric_cols].describe()
        else:
            self.describe_df = pd.DataFrame()

        return True

    def obtener_nombres_columnas(self):
        if self.datos is None:
            return []
        return list(self.datos.columns)

    def obtener_columna(self, col):
        if self.datos is None or col not in self.datos.columns:
            return None
        return self.datos[col].values

    def obtener_info(self):
        return self.info_str

    def obtener_describe(self):
        return self.describe_df

    def obtener_scatter(self, col1, col2):
        if self.datos is None:
            return None, None
        return self.datos[col1].values, self.datos[col2].values
