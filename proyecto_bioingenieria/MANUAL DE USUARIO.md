MANUAL DE USUARIO
Proyecto Final - Bioingeniería Informática II 2026-1
Universidad de Antioquia
========================================================


¿QUÉ ES ESTA APLICACIÓN?
--------------------------
BioMed Analizer Pro es una aplicación de escritorio para cargar, visualizar y procesar
datos biomédicos. Permite trabajar con tres tipos de datos: imágenes médicas
en formato DICOM, señales biológicas en formato .mat, y datos tabulares en
CSV o Excel. Todo desde una sola ventana con pestañas.


ANTES DE EJECUTAR
------------------
Necesitas tener Python instalado y las siguientes librerías. Puedes
instalarlas todas de una vez ejecutando en la terminal:

  pip install "nombre libreria"

Las librerías requeridas son: PyQt5, pydicom, nibabel, opencv-python,
numpy, pandas, matplotlib, mysql-connector-python y scipy.


También necesitas tener MySQL corriendo en tu máquina con los siguientes datos
de conexión:

Cree un usuario en PhpMyAdmin con los siguientes datos:
    Host:      localhost
    Usuario:   root1
    Contraseña: 4321

Cree la base de datos llamada: biomedica

Las tablas se crean automáticamente al iniciar la app si no existen.


PARA EJECUTAR LA APLICACIÓN
------------------
ejecuta el archivo:

    main.py


USUARIOS DISPONIBLES
---------------------
La primera vez que se inicia la app, se crean automáticamente tres usuarios:

    ID: admin      Contraseña: 1234    Rol: Administrador
    ID: user1      Contraseña: 1234    Rol: Usuario
    ID: user2      Contraseña: 1234    Rol: Usuario


========================================================
FLUJO PRINCIPAL DE LA APLICACIÓN
========================================================

La app tiene 4 pasos al entrar antes de llegar a la ventana principal.
Sigue este orden:


PASO 1 - PANTALLA DE BIENVENIDA -------------------------

Es la primera ventana que aparece. Solo tiene un botón:

    [ Ingresar ] --> Abre la pantalla de login.


PASO 2 - LOGIN ------------------------------------------
Aquí ingresas con tu usuario y contraseña.

    Campo ID:         Escribe el ID del usuario (ej: admin)
    Campo Contraseña: Escribe la contraseña (ej: 1234)
    [ Cancelar ]      --> Cierra la ventana de login.


PASO 3 - CÁMARA --------------------------------------------
Después de un login exitoso, se abre la ventana de cámara para registrar
una foto de la sesión. Esto queda guardado en la base de datos.

    [ Capturar ]    --> Toma la foto en ese momento y la guarda en la
                        carpeta assets/ con el nombre foto_<ID>.jpg.
                        Aparece un mensaje confirmando que fue capturada.
    [ Aceptar ]     --> Guarda el registro de la sesión en la base de datos
                         y abre la ventana principal.
   
   En caso de salir un error revise si su camara esta activada. 


PASO 4 - VENTANA PRINCIPAL
----------------------------
Es la ventana central de la app. Tiene tres pestañas en la parte superior:

    [ Imágenes DICOM ]   [ Señales ]   [ Datos Tabulares ]

En la parte superior también aparece el nombre del usuario y su rol.


========================================================
PESTAÑA 1: IMÁGENES DICOM
========================================================

Esta pestaña permite cargar y procesar imágenes médicas DICOM.

CARGA DE ARCHIVO
    [ Cargar DICOM ] --> Abre un diálogo donde puedes elegir:
                         - Cargar carpeta: carga una serie DICOM completa
                           (varios archivos .dcm que forman un volumen 3D)
                         - Cargar archivo: carga un solo archivo DICOM
                         - Cargar imagen: carga una imagen estándar (jpg, png)

    Cada vez que se carga un archivo, este va a generar un csv (de nombre metadatos) en la carpeta donde está ubicado el archivo seleccionado.
    Después de cargar, automáticamente:
    - Aparecen los tres cortes del volumen (sagital, coronal, axial)
    - La tabla de metadatos se llena con datos como fecha del estudio,
      modalidad, fabricante, duración, etc.

VISUALIZACIÓN DE CORTES
    Hay tres imágenes en pantalla con sus respectivos sliders debajo:

    Slider Sagital  --> Mueve el corte de izquierda a derecha del volumen
    Slider Coronal  --> Mueve el corte de adelante hacia atrás
    Slider Axial    --> Mueve el corte de arriba hacia abajo

    Mueve cualquier slider y la imagen correspondiente se actualiza
    en tiempo real.

ZOOM
    [ Zoom ] --> Recorta una región del corte axial, la redimensiona
                 y muestra el resultado al lado de la imagen original.
                 También dibuja un rectángulo indicando las dimensiones
                según el espaciado del pixel y el grosor del zoom que quiera realizar.

SEGMENTACIÓN
    Binarización: Selecciona el método de umbralización:
        - Binario
        - Binario Invertido
        - Truncado
        - Tozero
        - Tozero Invertido

    [ Segmentar ] --> Aplica el método seleccionado sobre el zoom actual y muestra el resultado.

TRANSFORMACIONES MORFOLÓGICAS
    SpinBox Kernel:     Define el tamaño del kernel (recomendado: 3, 5, 7)
    Morfología:   Selecciona la operación:
        - Apertura
        - Cierre
        - Gradiente
        - Erosion
        - Dilatacion

    [ Morfología ] --> Aplica la transformación sobre la imagen
                       que se le realizo zoom con el kernel definido.

EXPORTAR
    [ Convertir a NIfTI ] --> Convierte el volumen DICOM cargado a formato
                              NIfTI (.nii). Abre un diálogo para elegir
                              dónde guardar el archivo resultante.

========================================================
PESTAÑA 2: SEÑALES
========================================================

Esta pestaña procesa señales biológicas guardadas en archivos .mat

CARGA DE ARCHIVO
    [ Cargar señal ] --> Abre un explorador para seleccionar un archivo .mat.
                         La señal se carga como un arreglo 3D
                        que se reorganiza a 2D automáticamente.

SELECCIÓN DE CANALES
    Puede poner un valor de canal inicial y un valor de canal final. Luego oprima 

    [ Seleccionar canales ] --> Visualiza los canales en el rango indicado.
                                

AGREGAR RUIDO
    Tipo de ruido a agregar:
        - gaussiano
        - salt_pepper
        - uniforme

    [ Agregar ruido ] --> Muestra en subplots la señal original del canal
                          seleccionado y la misma señal con el ruido agregado.

ESTADÍSTICAS
    Radio Eje 0 / Eje 1 / Eje 2: Selecciona el eje sobre el que se
                                  calcula el promedio y la desviación estándar.

    [ Calcular estadísticas ] --> Calcula el promedio y la desviación
                                  estándar del arreglo de señal por el eje
                                  seleccionado y los muestra como gráficas
                                  de tipo stem.


========================================================
PESTAÑA 3: DATOS TABULARES
========================================================

Esta pestaña trabaja con archivos de datos en formato CSV o Excel.

CARGA DE ARCHIVO
    [ Cargar archivo ] --> Abre un explorador para seleccionar un archivo
                           .csv o .xlsx. Al cargar, automáticamente se
                           llenan las tablas de información.


VISUALIZACIÓN INDIVIDUAL DE COLUMNAS
    Lista de columnas:  Muestra todas las columnas disponibles del archivo.
                        Puede seleccionar la cantidad de columnas que desee.

    [ Graficar columnas ] --> Genera una gráfica por cada columna
                              seleccionada, mostrándolas juntas en subplots.

SCATTER PLOT
     
    Columna X:    Selecciona la columna para el eje horizontal
    Columna Y:    Selecciona la columna para el eje vertical

    [ Scatter ] --> Genera una gráfica de dispersión entre
                    las dos columnas seleccionadas.

