import cv2
import sys

def test_webcam():
    # 웹캠 디바이스 인덱스 시도
    for index in range(10):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"웹캠이 연결되었습니다! (인덱스: {index})")
            ret, frame = cap.read()
            if ret:
                cv2.imwrite('test_capture.jpg', frame)
                print("테스트 이미지가 저장되었습니다.")
            cap.release()
            return True
    print("웹캠을 열 수 없습니다!")
    return False

if __name__ == "__main__":
    test_webcam()