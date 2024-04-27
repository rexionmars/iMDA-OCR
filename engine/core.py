import sys
from ocr.TextRecognition import TextRecognition

if __name__ == "__main__":
    text_recognition = TextRecognition(0)  # Altere para o índice da sua câmera, se necessário
    text_recognition.start()
    while text_recognition.running:
        pass  # Aguarde até que a tecla "q" ou "ESC" seja pressionada
    sys.exit(0)
