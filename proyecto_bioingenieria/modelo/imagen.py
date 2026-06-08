import os
import numpy as np
import pandas as pd
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
import nibabel as nib
import cv2


class DICOMModel:
    def __init__(self):
        self.ruta = ""
        self.dataset = None
        self.matriz_3d = None
        self.datos_dicom = []
        self.spacing = (1.0, 1.0)
        self.grosor = 1.0
        self.metadatos = {}
        self.rescale_slope = 1.0
        self.rescale_intercept = 0.0
        self.matriz_hu = None
        self.matriz_uint8 = None

    def cargar_dicom(self, ruta):
        self.ruta = ruta

        # --- Soporte JPG / PNG ---
        ext = os.path.splitext(ruta)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'):
            img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"No se pudo leer la imagen: {ruta}")
            self.matriz_3d = np.expand_dims(img.astype(np.float64), axis=0)
            self.dataset = None
            self.datos_dicom = []
            self.spacing = (1.0, 1.0)
            self.grosor = 1.0
            self.rescale_slope = 1.0
            self.rescale_intercept = 0.0
            self.metadatos = {
                "Archivo": os.path.basename(ruta),
                "Tipo": ext.upper().replace(".", ""),
                "Dimensiones": f"{img.shape[1]} x {img.shape[0]} px",
                "Study Date": "N/A", "Study Time": "N/A",
                "Study Modality": "IMG", "Study Description": "Imagen digital",
                "Series Time": "N/A", "Duracion Estudio": "N/A",
                "Manufacturer": "N/A", "Patient Name": "N/A",
                "Patient ID": "N/A", "Patient Birth Date": "N/A",
                "Patient Sex": "N/A"
            }
            self.matriz_hu = self.matriz_3d.copy()
            self.matriz_uint8 = self.normalizar_uint8(self.matriz_3d)
            return True

        # --- DICOM ---
        if os.path.isdir(ruta):
            slices = []
            for archivo in sorted(os.listdir(ruta)):
                ruta_archivo = os.path.join(ruta, archivo)
                try:
                    ds = pydicom.dcmread(ruta_archivo, force=True)
                    if hasattr(ds, 'pixel_array'):
                        slices.append(ds)
                except Exception:
                    continue
            if not slices:
                raise ValueError("No se encontraron archivos DICOM válidos en el directorio")
            slices.sort(key=lambda x: float(getattr(x, 'SliceLocation', 0)))
            self.datos_dicom = slices
            self.dataset = slices[0]
            self.matriz_3d = np.stack([s.pixel_array for s in slices], axis=0)
        else:
            self.dataset = pydicom.dcmread(ruta, force=True)
            self.datos_dicom = [self.dataset]
            self.matriz_3d = np.expand_dims(self.dataset.pixel_array, axis=0)

        self.spacing = (
            float(getattr(self.dataset, 'PixelSpacing', [1.0, 1.0])[0]),
            float(getattr(self.dataset, 'PixelSpacing', [1.0, 1.0])[1])
        )
        self.grosor = float(getattr(self.dataset, 'SliceThickness', 1.0))
        self.rescale_slope = float(getattr(self.dataset, 'RescaleSlope', 1))
        self.rescale_intercept = float(getattr(self.dataset, 'RescaleIntercept', 0))
        self.metadatos = self.extraer_metadatos()
        self.matriz_hu = self.convertir_a_hounsfield(self.matriz_3d)
        self.matriz_uint8 = self.normalizar_uint8(self.matriz_hu)
        return True

    def extraer_metadatos(self):
        if not self.dataset:
            return {}
        ds = self.dataset
        study_date = str(getattr(ds, 'StudyDate', ''))
        study_time = str(getattr(ds, 'StudyTime', ''))
        series_time = str(getattr(ds, 'SeriesTime', ''))

        duracion = ""
        if study_time and series_time:
            try:
                st_h, st_m, st_s = int(study_time[:2]), int(study_time[2:4]), float(study_time[4:])
                se_h, se_m, se_s = int(series_time[:2]), int(series_time[2:4]), float(series_time[4:])
                diff = (se_h * 3600 + se_m * 60 + se_s) - (st_h * 3600 + st_m * 60 + st_s)
                duracion = f"{diff:.2f} s"
            except Exception:
                duracion = "N/A"

        return {
            "Study Date": study_date,
            "Study Time": study_time,
            "Study Modality": str(getattr(ds, 'Modality', '')),
            "Study Description": str(getattr(ds, 'StudyDescription', '')),
            "Series Time": series_time,
            "Duracion Estudio": duracion,
            "Manufacturer": str(getattr(ds, 'Manufacturer', '')),
            "Patient Name": str(getattr(ds, 'PatientName', '')),
            "Patient ID": str(getattr(ds, 'PatientID', '')),
            "Patient Birth Date": str(getattr(ds, 'PatientBirthDate', '')),
            "Patient Sex": str(getattr(ds, 'PatientSex', ''))
        }

    def convertir_a_hounsfield(self, matriz):
        return matriz * self.rescale_slope + self.rescale_intercept

    def normalizar_uint8(self, matriz):
        matriz_norm = np.zeros_like(matriz, dtype=np.float64)
        for i in range(matriz.shape[0]):
            slice_data = matriz[i]
            min_val = slice_data.min()
            max_val = slice_data.max()
            if max_val > min_val:
                matriz_norm[i] = ((slice_data - min_val) / (max_val - min_val)) * 255
            else:
                matriz_norm[i] = slice_data - min_val
        return matriz_norm.astype(np.uint8)

    def obtener_corte_sagital(self, idx):
        if self.matriz_uint8 is None:
            return None
        idx = max(0, min(idx, self.matriz_uint8.shape[2] - 1))
        return self.matriz_uint8[:, :, idx].T

    def obtener_corte_coronal(self, idx):
        if self.matriz_uint8 is None:
            return None
        idx = max(0, min(idx, self.matriz_uint8.shape[1] - 1))
        return self.matriz_uint8[:, idx, :].T

    def obtener_corte_axial(self, idx):
        if self.matriz_uint8 is None:
            return None
        idx = max(0, min(idx, self.matriz_uint8.shape[0] - 1))
        return self.matriz_uint8[idx]

    def dibujar_rectangulo(self, imagen, bbox):
        x, y, w, h = bbox
        img_color = cv2.cvtColor(imagen, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(img_color, (x, y), (x + w, y + h), (0, 255, 0), 2)
        ancho_mm = w * self.spacing[1]
        alto_mm = h * self.spacing[0]
        texto = f"{ancho_mm:.1f}x{alto_mm:.1f} mm"
        cv2.putText(img_color, texto, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return img_color

    def recortar_zoom(self, centro, tamanio):
        if self.matriz_3d is None:
            return None
        cx, cy = centro
        tw, th = tamanio
        x1 = max(0, cx - tw // 2)
        y1 = max(0, cy - th // 2)
        x2 = min(self.matriz_3d.shape[2], cx + tw // 2)
        y2 = min(self.matriz_3d.shape[1], cy + th // 2)
        slice_idx = self.matriz_3d.shape[0] // 2
        recorte = self.matriz_3d[slice_idx, y1:y2, x1:x2]
        return recorte, (x1, y1, x2 - x1, y2 - y1)

    def binarizar(self, imagen, metodo):
        if len(imagen.shape) == 3:
            gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        else:
            gray = imagen.copy()

        MAPA_METODOS = {
            "Binario": cv2.THRESH_BINARY,
            "Binario Invertido": cv2.THRESH_BINARY_INV,
            "Truncado": cv2.THRESH_TRUNC,
            "Tozero": cv2.THRESH_TOZERO,
            "Tozero Invertido": cv2.THRESH_TOZERO_INV,
        }
        flag = MAPA_METODOS.get(metodo, cv2.THRESH_BINARY)
        otsu_types = {"Binario", "Binario Invertido"}
        if metodo in otsu_types:
            flag += cv2.THRESH_OTSU
            _, result = cv2.threshold(gray, 0, 255, flag)
        else:
            _, result = cv2.threshold(gray, 127, 255, flag)
        return result

    def transformar_morfologica(self, imagen, kernel_size, tipo):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        if len(imagen.shape) == 3:
            gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        else:
            gray = imagen.copy()

        tipos = {
            "Apertura": cv2.MORPH_OPEN,
            "Cierre": cv2.MORPH_CLOSE,
            "Gradiente": cv2.MORPH_GRADIENT,
            "Erosion": cv2.MORPH_ERODE,
            "Dilatacion": cv2.MORPH_DILATE
        }
        op = tipos.get(tipo, cv2.MORPH_OPEN)
        return cv2.morphologyEx(gray, op, kernel)

    def guardar_metadatos_csv(self, ruta):
        df = pd.DataFrame([self.metadatos])
        df.to_csv(ruta, index=False)
        return True

    def convertir_nifti(self, ruta_salida):
        if self.matriz_hu is None:
            return False
        affine = np.eye(4)
        affine[0, 0] = self.spacing[1]
        affine[1, 1] = self.spacing[0]
        affine[2, 2] = self.grosor
        img_nifti = nib.Nifti1Image(self.matriz_hu, affine)
        nib.save(img_nifti, ruta_salida)
        return True


class NIFTIModel:
    def __init__(self):
        self.ruta = ""
        self.img_nifti = None
        self.matriz_3d = None

    def cargar_nifti(self, ruta):
        self.ruta = ruta
        self.img_nifti = nib.load(ruta)
        self.matriz_3d = self.img_nifti.get_fdata()
        return True

    def obtener_corte(self, eje, idx):
        if self.matriz_3d is None:
            return None
        if eje == "sagital":
            return self.matriz_3d[:, :, idx].T
        elif eje == "coronal":
            return self.matriz_3d[:, idx, :].T
        elif eje == "axial":
            return self.matriz_3d[idx]
        return None
