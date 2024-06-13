# Descripción del Proyecto
Este proyecto implementa un sistema de detección de rostros y predicción de género en tiempo real utilizando Flask, OpenCV y una cámara IP ESP32 o la cámara del dispositivo. La aplicación permite capturar y procesar video en tiempo real para detectar rostros y predecir el género de las personas detectadas. Los resultados se almacenan en una base de datos MySQL y se presentan en una interfaz web interactiva.

## Características Principales
1. **Detección de Rostros**: Utiliza una red neuronal convolucional (CNN) preentrenada para detectar rostros en tiempo real.
2. **Predicción de Género**: Predice el género de los rostros detectados utilizando un modelo preentrenado.
3. **Transmisión de Video en Tiempo Real**: Captura video en tiempo real desde una cámara IP ESP32 o la cámara del dispositivo.
4. **Almacenamiento de Resultados**: Almacena los resultados de la detección y predicción en una base de datos MySQL.
5. **Interfaz Web**: Proporciona una interfaz web interactiva para visualizar los resultados y gestionar la configuración de la cámara.
6. **Monitorización del Servidor**: Monitoriza el uso del servidor (CPU, RAM y disco) y muestra los datos en tiempo real.

## Requisitos del Sistema:
- Python 3.x
- Flask
- Flask-SocketIO
- OpenCV
- NumPy
- MySQLdb
- psutil


## Instalación:
1. **Clonar el Repositorio**
```bash
git clone https://github.com/DavidAr55/face_detection.git
cd tu_proyecto
```

2. **Crear un Entorno Virtual**
```bash
python -m venv env
source env/bin/activate   # En Windows, usa `env\Scripts\activate`
```

3. **Instalar las Dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar la Base de Datos**
* **Crear una base de datos MySQL llamada "face_detection"**
* **Configurar las credenciales de la base de datos en el archivo de configuración.**


5. **Descargar los Modelos Preentrenados**
* Descargar los archivos de los modelos preentrenados y ubicarlos en las rutas especificadas en el código.

## Uso
1. **Iniciar la Aplicación**
```bash
flask run
```

2. **Acceder a la Interfaz Web**
* Abre tu navegador web y dirígete a http://localhost:5000.

3. **Configuración de la Cámara**
* En la página principal, ingresa la URL de tu cámara IP ESP32 y comienza la transmisión.
* Alternativamente, usa la cámara del dispositivo seleccionando la opción de webcam.


4. **Visualización y Gestión de Resultados**
* Ve al panel de control para visualizar las estadísticas de detección.
* Sube imágenes para la detección de rostros y predicción de género desde la página de subida.

## Estructura del Proyecto
* ```bash app.py ```:  Archivo principal de la aplicación Flask.
* ```bash templates/ ```: Directorio que contiene las plantillas HTML para la interfaz web.
* ```bash static/```: Directorio que contiene los archivos estáticos como CSS y JavaScript.
* ```bash models/```: Directorio que contiene los archivos de los modelos preentrenados.

## Contribución
Las contribuciones son bienvenidas. Por favor, sigue estos pasos:
1. Haz un fork del repositorio.
2. Crea una nueva rama (git checkout -b feature/nueva-caracteristica).
3. Realiza tus cambios y haz commits (git commit -am 'Añadir nueva característica').
4. Envía tus cambios a la rama principal (git push origin feature/nueva-caracteristica).
5. Abre un Pull Request.

## Licencia
Este proyecto está licenciado bajo la Licencia MIT. Para más detalles, consulta el archivo LICENSE.