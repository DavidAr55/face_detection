from flask import Flask, render_template, request, Response, redirect, url_for, flash, jsonify, session
from flask_socketio import SocketIO, emit
from datetime import datetime
from collections import defaultdict
import cv2
import threading
import numpy as np
import os
import time
import base64
import psutil
import MySQLdb
import random
import string

app = Flask(__name__)
app.secret_key = 'hot_taco'
socketio = SocketIO(app)
server_usage_history = []

# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'face_detection'

# Inicialización de la conexión a la base de datos
mysql = MySQLdb.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)

def get_gender_data():
    cursor = mysql.cursor()
    query = """
    SELECT DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i') as minute, 
           SUM(mens_detected) as mens_detected, 
           SUM(womens_detected) as womens_detected
    FROM classify_webcam
    GROUP BY minute
    UNION
    SELECT DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i') as minute, 
           SUM(mens_detected) as mens_detected, 
           SUM(womens_detected) as womens_detected
    FROM classify_esp32
    GROUP BY minute
    ORDER BY minute;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

@app.route('/gender_data')
def gender_data():
    data = get_gender_data()
    response = {
        'labels': [row[0] for row in data],
        'mens_detected': [row[1] for row in data],
        'womens_detected': [row[2] for row in data]
    }
    return jsonify(response)

# Detección de rostros y género
def faceDetection(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)
    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            cv2.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight / 150)), 8)
    return frameOpencvDnn, faceBoxes

# Definir las rutas de los modelos
faceProto = "models/opencv_face_detection/opencv_face_detector.pbtxt"
faceModel = "models/opencv_face_detection/opencv_face_detector_uint8.pb"
genderProto = "models/gender_detection/gender_deploy.prototxt"
genderModel = "models/gender_detection/gender_net.caffemodel"

# Definición de listas y valores medios del modelo:
MODEL_MEAN_VALUES = (100.4263377603, 60.7689143744, 114.895847746)
genderList = ['Male', 'Female']

# Cargando modelos previamente entrenados
faceNet = cv2.dnn.readNet(faceModel, faceProto)
genderNet = cv2.dnn.readNet(genderModel, genderProto)

padding = 20
camera_url = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global camera_url
    if request.method == 'POST':
        camera_url = "http://" + request.form['camera_url']
        return redirect(url_for('stream'))
    
    cursor = mysql.cursor()
    query = '''
        SELECT filename,
               SUM(CASE WHEN gender = 'Male' THEN 1 ELSE 0 END) AS mens_detected,
               SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) AS womens_detected,
               COUNT(*) AS total_detected
        FROM classify_media
        GROUP BY filename
    '''
    cursor.execute(query)
    results = cursor.fetchall()
    
    sales_data = []
    for row in results:
        sales_data.append({
            'filename': row[0],
            'mens_detected': row[1],
            'womens_detected': row[2],
            'total_detected': row[3]
        })

    session['selected_view'] = 'dashboard'
    return render_template('dashboard.html',  sales_data=sales_data)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = file.filename
            image = file.read()
            nparr = np.fromstring(image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            resultImg, faceBoxes = faceDetection(faceNet, img)
            genders = []
            for faceBox in faceBoxes:
                face = img[max(0, faceBox[1] - 20):min(faceBox[3] + 20, img.shape[0] - 1),
                           max(0, faceBox[0] - 20):min(faceBox[2] + 20, img.shape[1] - 1)]
                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]
                genders.append(gender)
                cv2.putText(resultImg, f'{gender}', (faceBox[0], faceBox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
                
                # Insertar el registro en la base de datos con el nombre del archivo
                cursor = mysql.cursor()
                cursor.execute("INSERT INTO classify_media (gender, filename) VALUES (%s, %s)", (gender, filename))
                mysql.commit()

            _, buffer = cv2.imencode('.jpg', resultImg)
            result_image = buffer.tobytes()
            encoded_image = base64.b64encode(result_image).decode('utf-8')
            return render_template('upload.html', processed_image=encoded_image)
    session['selected_view'] = 'upload'
    return render_template('upload.html')

def gen_frames():
    global camera_url
    print(camera_url)
    cap = cv2.VideoCapture(camera_url)
    
    # Verifica si la cámara se ha abierto correctamente
    if not cap.isOpened():
        # Mensaje de error en el servidor Flask si la cámara no se abre
        print(f"Error al abrir la cámara con URL: {camera_url}")
        yield b''
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            # Mensaje de error en el servidor Flask si no se pueden leer frames
            print("Error al leer el frame de la cámara")
            yield b''
            break
        
        resultImg, faceBoxes = faceDetection(faceNet, frame)
        if faceBoxes:
            for faceBox in faceBoxes:
                face = frame[max(0, faceBox[1] - padding):min(faceBox[3] + padding, frame.shape[0] - 1),
                             max(0, faceBox[0] - padding):min(faceBox[2] + padding, frame.shape[1] - 1)]
                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]
                cv2.putText(resultImg, f'{gender}', (faceBox[0], faceBox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
        
        ret, buffer = cv2.imencode('.jpg', resultImg)
        if not ret:
            # Mensaje de error en el servidor Flask si no se puede codificar el frame
            print("Error al codificar el frame")
            yield b''
            break
        
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()
    
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    
@app.route('/stream', methods=['GET', 'POST'])
def stream():
    global camera_url
    if request.method == 'POST':
        camera_url = "http://" + request.form['camera_url']
        if not camera_url:
            flash('Por favor, proporciona una URL de cámara válida.')
            return redirect(url_for('stream'))
    session['selected_view'] = 'stream'
    return render_template('stream.html', camera_url=camera_url)

@app.route('/webcam')
def webcam():
    session['selected_view'] = 'webcam'
    return render_template('webcam.html')

def insert_to_db(webcam_token, mens_detected, womens_detected):
    cursor = mysql.cursor()
    cursor.execute("INSERT INTO classify_webcam (webcam_token, mens_detected, womens_detected) VALUES (%s, %s, %s)",
                   (webcam_token, mens_detected, womens_detected))
    mysql.commit()
    cursor.close()

# Función para capturar frames de la webcam y detectar géneros
def gen_frames_webcam():
    cap = cv2.VideoCapture(0)  # Usar la cámara del dispositivo (índice 0)
    webcam_token = generate_id()

    if not cap.isOpened():
        print("Error al abrir la cámara del dispositivo")
        yield b''
        return

    last_insert_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer el frame de la cámara del dispositivo")
            yield b''
            break

        resultImg, faceBoxes = faceDetection(faceNet, frame)

        mens_detected = 0
        womens_detected = 0

        if faceBoxes:
            for faceBox in faceBoxes:
                face = frame[max(0, faceBox[1] - padding):min(faceBox[3] + padding, frame.shape[0] - 1),
                             max(0, faceBox[0] - padding):min(faceBox[2] + padding, frame.shape[1] - 1)]
                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]

                mens_detected += 1 if gender == "Male" else 0
                womens_detected += 1 if gender == "Female" else 0

                cv2.putText(resultImg, f'Gender: {gender}', (faceBox[0], faceBox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)

        # Emitir los datos a los clientes
        socketio.emit('update_counts', {'mens_detected': mens_detected, 'womens_detected': womens_detected})

        # Insertar en la base de datos cada 5 segundos
        current_time = time.time()
        if current_time - last_insert_time >= 5:
            insert_to_db(webcam_token, mens_detected, womens_detected)
            last_insert_time = current_time

        ret, buffer = cv2.imencode('.jpg', resultImg)
        if not ret:
            print("Error al codificar el frame")
            yield b''
            break

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/video_feed_webcam')
def video_feed_webcam():
    return Response(gen_frames_webcam(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/dashboard')
def dashboard():
    session['selected_view'] = 'dashboard'
    return render_template('dashboard.html')

def get_server_usage_data():
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    server_usage_data = {
        'cpu_usage': cpu_usage,
        'ram_usage': ram_usage,
        'disk_usage': disk_usage
    }
    
    server_usage_history.append(server_usage_data)
    server_usage_history_trimmed = server_usage_history[-25:]
    
    return server_usage_history_trimmed

@app.route('/get_server_usage_data')
def get_server_usage_data_route():
    server_usage_data = get_server_usage_data()
    
    return jsonify({'data': server_usage_data})

def generate_id(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

if __name__ == '__main__':
    app.run(debug=True)
