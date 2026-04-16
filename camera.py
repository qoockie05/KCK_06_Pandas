import cv2

cap0 = cv2.VideoCapture(0)  # kamera front
cap1 = cv2.VideoCapture(1)  # kamera bok

def resize_to_height(frame, target_height=480):
    h, w = frame.shape[:2]
    new_width = int(w * target_height / h)
    return cv2.resize(frame, (new_width, target_height))

while True:
    ok0, frame0 = cap0.read()
    ok1, frame1 = cap1.read()

    if not ok0 or not ok1:
        print("Nie udało się odczytać jednej z kamer.")
        break

    frame0 = resize_to_height(frame0, 480)
    frame1 = resize_to_height(frame1, 480)

    cv2.putText(frame0, "Kamera przod", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame1, "Kamera bok", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    combined = cv2.hconcat([frame0, frame1])

    cv2.imshow("Podglad 2 kamer", combined)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap0.release()
cap1.release()
cv2.destroyAllWindows()