import sys
import argparse
from ocr.TextRecognition import TextRecognition


def main(camera_index):
    text_recognition = TextRecognition(camera_index)
    text_recognition.start()
    while text_recognition.running:
        pass  # Aguarde até que a tecla "q" ou "ESC" seja pressionada
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script para reconhecimento de texto com índice da câmera')
    parser.add_argument('--camera-index', type=int, default=0, help='Índice da câmera (padrão: 0)')
    args = parser.parse_args()
    main(args.camera_index)
