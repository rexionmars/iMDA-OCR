import os
import sys

from ocr.common.OCR import TextRecognition, VideoCapture

if __name__ == "__main__":
    #text_recognition = TextRecognition("http://192.168.0.51:81/stream")
    server = "http://127.0.0.1:8080/receive-ocr-data"
    #text_recognition = TextRecognition("http://192.168.0.51:81/stream", server_url=server)  #OV2640
    text_recognition = TextRecognition("http://192.168.0.38:81/stream", server_url=server)  #OV2640
    text_recognition.start()
    while text_recognition.running:
        pass  # Wait until the "q" or "ESC" key is pressed
    sys.exit(0)
