import cv2

faceClassif = cv2.CascadeClassifier('./modelo.xml')

# Definir una función para la detección de rostros
def detect_faces(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = faceClassif.detectMultiScale(gray,
                                         scaleFactor=1.01,
                                         minNeighbors=5,
                                         minSize=(30, 30),
                                         maxSize=(200, 200))
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return image

# Cargar y mostrar cada imagen de prueba
for i in range(1, 8):
    image_path = f'./prueba_{i}.jpg'
    image = cv2.imread(image_path)
    result_image = detect_faces(image)
    cv2.imshow(f'Prueba {i}', result_image)
    cv2.waitKey(0)

cv2.destroyAllWindows()
