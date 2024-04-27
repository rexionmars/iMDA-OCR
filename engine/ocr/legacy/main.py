import cv2
import easyocr
import json
import re
import sys
from queue import Queue


class FloatingRectangle:

    def __init__(self, window_name, rectangle_size=(120, 30), offset_x=40, offset_y=40):
        self.window_name = window_name
        self.rectangle_size = rectangle_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.current_mouse_position = (0, 0)
        self.text = ""

    def set_position(self, position):
        self.current_mouse_position = position

    def set_text(self, text):
        self.text = text

    def draw(self, frame):
        if len(self.current_mouse_position) == 2:
            x, y = self.current_mouse_position
            w, h = self.rectangle_size
            x1 = x - w // 2 - self.offset_x
            y1 = y - h // 2 - self.offset_y
            x2 = x1 + w
            y2 = y1 + h
            cv2.rectangle(frame, (x1, y1), (x2, y2), (25, 220, 255), 1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, self.text, (x1 + 5, y1 + 20), font, 0.4, (25, 220, 255), 1, cv2.LINE_AA)


class TextRecognition:

    def __init__(self, video_source, language="en"):
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
        self.stage_texts = [
            "Selecione a região principal (container)", "Selecione o label", "Selecione o valor principal",
            "Selecione o valor mínimo", "Selecione o valor máximo"
        ]
        self.floating_rectangle = FloatingRectangle('Text Recognition')

    def start(self):
        self.display_window()

    def read_text(self, frame):
        if frame is None:
            return

        if self.stage == len(self.stage_texts):
            roi_data = {}
            for i, roi in enumerate(self.rois):
                x, y, w, h = roi
                cropped_frame = frame[y:y + h, x:x + w]
                gray_cropped_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
                results = self.reader.readtext(gray_cropped_frame)

                roi_info = {}
                list_value = []

                for bbox, text, prob in results:
                    label, value = self.extract_label_and_value(text)
                    list_value.append(value)

                    if label:
                        if label not in roi_info:
                            roi_info[label] = []

                    text_x = x + bbox[0][0]
                    text_y = y + bbox[0][1]

                    cv2.rectangle(frame, (text_x, text_y), (x + bbox[2][0], y + bbox[2][1]), (0, 255, 0), 1)
                    cv2.putText(frame, text, (text_x, text_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                filtered_values = [item for item in list_value if item is not None]
                filtered_values = [float(item) for item in filtered_values]

                for label, values in roi_info.items():
                    values.extend(filtered_values)

                roi_data[f"ROI_ID {i}"] = roi_info

            print(json.dumps(roi_data, indent=4))

            self.print_roi_data(roi_data)

            for roi in self.rois:
                x, y, w, h = roi
                cv2.rectangle(frame, (x, y), (x + w, y + h), (214, 102, 3), 1)

        self.last_frame = frame

    def print_roi_data(self, roi_data):
        pass

    def extract_label_and_value(self, text):
        parts = re.split(r"(\d+)", text)
        label = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else None
        return label, value

    def display_window(self):
        cv2.namedWindow("Text Recognition")
        cv2.setMouseCallback("Text Recognition", self.on_mouse_events)

        while self.running:
            ret, frame = self.video_capture.read()
            if ret:
                self.display_text_instructions(frame)
                if self.stage < len(self.stage_texts):
                    if self.current_roi is not None:
                        self.draw_roi(frame, self.current_roi)
                    for roi in self.rois:
                        self.draw_roi(frame, roi)
                self.read_text(frame)
                cv2.imshow("Text Recognition", frame)

                key = cv2.waitKey(1) & 0xFF
                self.event_queue.put(key)

        self.video_capture.release()
        cv2.destroyAllWindows()

    def display_text_instructions(self, frame):
        if self.stage < len(self.stage_texts):
            text = self.stage_texts[self.stage]
        else:
            text = "Processo concluído. Pressione 'q' ou 'ESC' para sair."

        self.floating_rectangle.set_text(text)
        self.floating_rectangle.draw(frame)

    def draw_roi(self, frame, roi):
        x, y, w, h = roi
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

    def on_mouse_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.stage < len(self.stage_texts):
                self.drawing = True
                self.current_roi = [x, y, 0, 0]

        elif event == cv2.EVENT_MOUSEMOVE:
            if not self.drawing:  # Atualiza o retângulo com as instruções apenas se não estiver desenhando
                self.floating_rectangle.set_position((x, y))
                self.display_text_instructions(param)

            if self.drawing:
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

    def undo_roi_deletion(self):
        if self.deleted_rois:
            self.rois.append(self.deleted_rois.pop())


class VideoCapture:

    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()


if __name__ == "__main__":
    text_recognition = TextRecognition(0)  # Altere para o índice da sua câmera, se necessário
    text_recognition.start()
    while text_recognition.running:
        pass  # Aguarde até que a tecla "q" ou "ESC" seja pressionada
    sys.exit(0)
