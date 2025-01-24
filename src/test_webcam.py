import cv2

def test_webcam():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다!")
        return
    
    print("웹캠이 정상적으로 열렸습니다.")
    
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다!")
    else:
        print("프레임을 성공적으로 읽었습니다.")
    
    cap.release()

if __name__ == "__main__":
    test_webcam() 