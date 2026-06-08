import numpy as np
import scipy.io as sio


class SignalModel:
    def __init__(self):
        self.ruta = ""
        self.datos_3d = None
        self.datos_2d = None
        self.fs = 1.0
        self.nombres_canales = []

    def cargar_mat(self, ruta):
        self.ruta = ruta
        mat = sio.loadmat(ruta)

        var_name = None
        for key in mat:
            if not key.startswith('__'):
                var_name = key
                break

        if var_name is None:
            raise ValueError("No se encontraron variables en el archivo .mat")

        data = mat[var_name]

        if data.ndim == 1:
            self.datos_3d = np.expand_dims(np.expand_dims(data, axis=0), axis=-1)
        elif data.ndim == 2:
            self.datos_3d = np.expand_dims(data, axis=-1)
        elif data.ndim == 3:
            self.datos_3d = data
        else:
            raise ValueError(f"Dimensiones no soportadas: {data.ndim}")

        self.cambiar_a_2d()
        self.nombres_canales = [f"Canal {i+1}" for i in range(self.datos_2d.shape[0])]

        if 'fs' in mat:
            self.fs = float(np.squeeze(mat['fs']))
        else:
            self.fs = 1.0

        return True

    def cambiar_a_2d(self):
        if self.datos_3d is None:
            return None
        if self.datos_3d.ndim == 3:
            n_canales, n_tiempo, n_trials = self.datos_3d.shape
            self.datos_2d = self.datos_3d.reshape(n_canales, n_tiempo * n_trials)
        else:
            self.datos_2d = self.datos_3d
        return self.datos_2d

    def seleccionar_canales(self, inicio, fin):
        if self.datos_2d is None:
            return None
        inicio = max(0, inicio)
        fin = min(self.datos_2d.shape[1], fin)
        return self.datos_2d[:, inicio:fin]

    def agregar_ruido(self, canal, tipo='gaussiano', params=None):
        if self.datos_2d is None:
            return None, None
        if params is None:
            params = {'media': 0, 'desviacion': 0.1 * np.std(self.datos_2d[canal])}

        original = self.datos_2d[canal].copy()

        if tipo == 'gaussiano':
            ruido = np.random.normal(params['media'], params['desviacion'], original.shape)
        elif tipo == 'salt_pepper':
            ruido = np.random.choice([-1, 0, 1], size=original.shape,
                                     p=[0.02, 0.96, 0.02]) * np.max(np.abs(original)) * 0.5
        elif tipo == 'uniforme':
            ruido = np.random.uniform(-params['desviacion'], params['desviacion'], original.shape)
        else:
            ruido = np.random.normal(0, params['desviacion'], original.shape)

        modificada = original + ruido
        return original, modificada

    def calcular_promedio(self, eje):
        if self.datos_3d is None:
            return None
        return np.mean(self.datos_3d, axis=eje)

    def calcular_desviacion(self, eje):
        if self.datos_3d is None:
            return None
        return np.std(self.datos_3d, axis=eje)
