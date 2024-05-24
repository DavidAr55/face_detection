import cv2
import numpy as np

# Cambia la fuente del VideoCapture a la URL del ESP32 y ajusta el tiempo de espera
cap = cv2.VideoCapture('http://192.168.100.90:81/stream')

# Configurar el buffer y los FPS (estos valores pueden necesitar ajustes)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Tamaño del buffer
cap.set(cv2.CAP_PROP_FPS, 15)        # FPS del stream (ajustar según sea necesario)

faceClassif = cv2.CascadeClassifier('./modelo.xml')

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: no se pudo leer el frame de la cámara.")
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = faceClassif.detectMultiScale(gray, 1.1, 5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow('frame', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()