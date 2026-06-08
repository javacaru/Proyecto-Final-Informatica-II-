import cv2
import numpy as np
import os


class CamaraModel:
    def __init__(self):
        self.captura = None

    def iniciar(self):
        self.captura = cv2.VideoCapture(0)
        return self.captura.isOpened()

    def capturar_foto(self):
        if self.captura is None or not self.captura.isOpened():
            return None
        ret, frame = self.captura.read()
        if ret:
            return frame
        return None

    def liberar(self):
        if self.captura and self.captura.isOpened():
            self.captura.release()

    def guardar_foto(self, imagen, ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        cv2.imwrite(ruta, imagen)
        return os.path.exists(ruta)
