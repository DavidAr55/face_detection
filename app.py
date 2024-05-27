from flask import Flask, render_template, request, Response, redirect, url_for, flash, jsonify
import cv2
import numpy as np
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para mostrar mensajes flash

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
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
genderList = ['Masculino', 'Femenino']

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
    return render_template('index.html')

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
@app.route('/stream')
def stream():
    if camera_url is None:
        flash('Por favor, proporciona una URL de cámara válida.')
        return redirect(url_for('index'))
    return render_template('stream.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
