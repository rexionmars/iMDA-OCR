import pandas as pd
import threading
import easyocr
import time
import cv2
import re

from threading import Timer
from queue import Queue
from typing import List
from icecream import ic

from common import FloatingRectangle
from common import BasicGeometrics
from common import VideoCapture
from configurations.debug_flag_control import ENABLE_VISUAL_GEOMETRIC_DETECTORS, ENABLE_DEBUG_ROI_INFO
from configurations.constants import DEAFULT_COLOR_DETECTION_RECTANGLE as YELLOW
from configurations.constants import DEFAULT_COLOR_DETECTION_TEXT as GREEN


class TextRecognition:
    stage_texts = [
        "Select the Information Unit", "Enter the label", "Select the main value", "Select the minimum value",
        "Select the maximum value"
    ]

    def __init__(self, video_source, language="en"):
        self.geometric = BasicGeometrics()
        self.reader = easyocr.Reader([language])
        self.video_capture = VideoCapture(video_source)
        self.rois = []
        self.deleted_rois = []
        self.event_queue = Queue()
        self.drawing = False
        self.running = True
        self.last_frame = None
        self.current_roi = None
        self.stage = 0
        self.show_floating_rectangle = True
        self.floating_rectangle = FloatingRectangle('Text Recognition')
        self.delayed_processing_thread = threading.Thread(target=self.delayed_processing)
        self.delayed_processing_thread.daemon = True
        self.delayed_processing_thread.start()
        self.label_text = ""

    def start(self):
        self.display_window()

    def process_filtered_values(self, unit_name: str, filtered_values: List[float]) -> None:
        # Adicione os valores filtrados à fila de processamento
        self.event_queue.put((unit_name, filtered_values))
    
    # Salva os dados em um determinado intervalo de tempo: 15s, 30s, 1m, 30m, 3h, 1h, 6h, 12h, 24h
    def save_data_in_interval(self, unit_name: str, unit_values: List[float], interval: int) -> None:
        # Salve os dados em um arquivo CSV
        data = {
            "unit_name": unit_name,
            "current": unit_values[0] if unit_values else 0,
            "min": unit_values[1] if len(unit_values) > 1 else 0,
            "max": unit_values[2] if len(unit_values) > 2 else 0,
            "timestamp": time.time()
        }
        df = pd.DataFrame(data, index=[0])
        df.to_csv(f"{unit_name}.csv", mode="a", header=False, index=False)
        ic.configureOutput(prefix="Data Saved\t")


        # Agende a próxima execução
        Timer(interval, self.save_data_in_interval, args=[unit_name, unit_values, interval]).start()

    def delayed_processing(self) -> None:
        while self.running:
            # Verifique se há valores na fila de processamento
            if not self.event_queue.empty():
                # Obtenha os valores da fila
                unit_name, filtered_values = self.event_queue.get()

                unit_base_values = {
                    "current": filtered_values[0] if filtered_values else 0,
                    "min": filtered_values[1] if len(filtered_values) > 1 else 0,
                    "max": filtered_values[2] if len(filtered_values) > 2 else 0,
                }

                time.sleep(1)  # Delay para controlar a taxa de processamento
                if ENABLE_DEBUG_ROI_INFO:
                    self._print_roi_data(unit_name, filtered_values)
                return unit_name, unit_base_values

    def _extract_label_and_value(self, text):
        parts = re.split(r"(\d+)", text)
        label = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else None
        return label, value

    def _print_roi_data(self, unit_name: str, unit_values: List[float]) -> None:
        _unit_data_structure = {
            f"{unit_name}": {
                "current": unit_values[0] if unit_values else 0,
                "min": unit_values[1] if len(unit_values) > 1 else 0,
                "max": unit_values[2] if len(unit_values) > 2 else 0,
            }
        }
        ic.configureOutput(prefix="Unit Data Structure\t")
        ic(_unit_data_structure)

    def read_text(self, frame):
        if frame is None:
            return

        if self.stage == len(self.__class__.stage_texts):
            for roi in self.rois:
                x, y, w, h = roi
                cropped_frame = frame[y:y + h, x:x + w]
                gray_cropped_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
                results = self.reader.readtext(gray_cropped_frame)

                list_value = []

                for bbox, text, prob in results:
                    label, value = self._extract_label_and_value(text)
                    list_value.append(value)

                    if label:
                        self.process_filtered_values(label, [float(value) if value is not None else 0])

                    text_x = x + bbox[0][0]
                    text_y = y + bbox[0][1]

                    if ENABLE_VISUAL_GEOMETRIC_DETECTORS:
                        # Desenha o texto e o retângulo ao redor do texto reconhecido
                        cv2.rectangle(frame, (text_x, text_y), (x + bbox[2][0], y + bbox[2][1]), GREEN, 1)
                        cv2.putText(frame, text, (text_x, text_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 1)

                # Remove valores nulos da lista
                filtered_values = [float(item) for item in list_value if item is not None]
                ic.configureOutput(prefix="Filtered Values\t")
                ic(filtered_values)

                # ROI
                self.geometric.rounded_rectangle(frame, (x, y, w, h), thickness_of_line=1)

        self.last_frame = frame

    def _draw_roi(self, frame, roi):
        x, y, w, h = roi
        self.geometric.rounded_rectangle(frame, (x, y, w, h), thickness_of_line=1)

    def draw_text_input(self, frame, prompt):
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = ''
        self.floating_rectangle.set_text(prompt)

        while True:
            temp_frame = frame.copy()
            self.floating_rectangle.draw(temp_frame)
            cv2.putText(temp_frame, text, (60, 85), font, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow("Text Recognition", temp_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 13:  # Enter key
                break
            elif key == 8:  # Backspace key
                text = text[:-1]
            elif key == 27:  # Esc key
                text = ''
                break
            elif 32 <= key <= 126:  # Printable characters
                text += chr(key)

        return text

    def display_window(self):
        cv2.namedWindow("Text Recognition")
        cv2.setMouseCallback("Text Recognition", self.on_mouse_events)

        while self.running:
            ret, frame = self.video_capture.read()
            if ret:
                self.display_text_instructions(frame)
                if self.stage < len(self.stage_texts) and self.stage_texts[self.stage] == "Enter the label":
                #if self.stage_texts[self.stage] == "Enter the label":
                    self.label_text = self.draw_text_input(frame, "Enter the label: ")
                    self.stage += 1  # Progresso para o próximo estágio
                else:
                    if self.stage < len(self.stage_texts):
                        if self.current_roi is not None:
                            self._draw_roi(frame, self.current_roi)
                        for roi in self.rois:
                            self.geometric.rounded_rectangle(frame, roi, thickness_of_line=1)
                    self.read_text(frame)

                    if self.show_floating_rectangle:  # Verifica se o retângulo flutuante deve ser exibido
                        self.floating_rectangle.draw(frame)
                    cv2.imshow("Text Recognition", frame)

                key = cv2.waitKey(1) & 0xFF
                if key != 255:  # Verifica se uma tecla foi pressionada
                    self.event_queue.put(True)  # Informa à thread de processamento que uma tecla foi pressionada

                if key == ord('q'):
                    self.running = False
                elif key == ord('r'):  # Pressione 'r' para remover o último ROI
                    self.remove_last_roi()
                elif key == ord('u'):  # Pressione 'u' para desfazer a remoção do último ROI
                    self.undo_roi_deletion()

        self.video_capture.release()
        cv2.destroyAllWindows()

    def display_text_instructions(self, frame):
        if self.stage < len(self.stage_texts):
            text = self.stage_texts[self.stage]
        else:
            text = "Process completed. Press 'q' or 'ESC' to exit."
            self.show_floating_rectangle = False

        self.floating_rectangle.set_text(text)


    def on_mouse_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.stage < len(self.stage_texts):
                self.drawing = True
                self.current_roi = [x, y, 0, 0]

        elif event == cv2.EVENT_MOUSEMOVE:
            if not self.drawing:  # Atualiza o retângulo com as instruções apenas se não estiver desenhando
                self.floating_rectangle.set_position((x, y))

            if self.drawing:
                self.floating_rectangle.set_position(
                    (x, y))  # Atualiza a posição do retângulo mesmo durante o desenho
                if self.current_roi is not None:
                    self.current_roi[2] = x - self.current_roi[0]
                    self.current_roi[3] = y - self.current_roi[1]

        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                if self.current_roi is not None:
                    self.rois.append(tuple(self.current_roi))
                    self.current_roi = None
                    if self.stage < len(self.stage_texts):
                        self.stage += 1

    def remove_last_roi(self):
        if self.rois:
            self.deleted_rois.append(self.rois.pop())

            if self.stage > 0:
                self.stage -= 1

            if self.stage < len(self.stage_texts):
                self.floating_rectangle.set_text(self.stage_texts[self.stage])

    def undo_roi_deletion(self):
        if self.deleted_rois:
            self.rois.append(self.deleted_rois.pop())

            if self.stage < len(self.stage_texts):
                self.floating_rectangle.set_text(self.stage_texts[self.stage])
            

if __name__ == "__main__":
    text_recognition = TextRecognition(0)
    text_recognition.start()