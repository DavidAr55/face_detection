from flask import Flask, render_template, request, Response, redirect, url_for, flash, jsonify, session
from flask_socketio import SocketIO, emit
import cv2
import threading
import numpy as np
import os
import psutil
import MySQLdb

app = Flask(__name__)
app.secret_key = 'hot_taco'
socketio = SocketIO(app)
server_usage_history = []

# Configuración de la conexión a la base de datos
def get_db_connection():
    return MySQLdb.connect(
        host='localhost',
        user='root',
        password='',
        db='face_classify',
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor
    )

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
    session['selected_view'] = 'dashboard'
    return render_template('dashboard.html')

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
            image = file.read()
            nparr = np.fromstring(image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            resultImg, faceBoxes = faceDetection(faceNet, img)
            genders = []
            for faceBox in faceBoxes:
                face = img[max(0, faceBox[1] - padding):min(faceBox[3] + padding, img.shape[0] - 1),
                           max(0, faceBox[0] - padding):min(faceBox[2] + padding, img.shape[1] - 1)]
                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]
                genders.append(gender)
                cv2.putText(resultImg, f'{gender}', (faceBox[0], faceBox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
            _, buffer = cv2.imencode('.jpg', resultImg)
            result_image = buffer.tobytes()
            return Response(result_image, mimetype='image/jpeg')
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

def gen_frames_webcam():
    cap = cv2.VideoCapture(0)  # Usar la cámara del dispositivo (índice 0)

    if not cap.isOpened():
        print("Error al abrir la cámara del dispositivo")
        yield b''
        return
    
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
        
        # print(f"Mens: {mens_detected} | Womens: {womens_detected}")
        # Emitir los datos a los clientes
        socketio.emit('update_counts', {'mens_detected': mens_detected, 'womens_detected': womens_detected})
        
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

if __name__ == '__main__':
    app.run(debug=True)
