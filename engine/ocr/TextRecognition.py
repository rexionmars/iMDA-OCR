import cv2
import easyocr
import json
import re

from queue import Queue

from common.FloatingRectangle import FloatingRectangle
from common.VideoCapture import VideoCapture


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
            "Select the main region (container)", "Select the label", "Select the main value",
            "Select the minimum value", "Select the maximum value"
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
                    #cv2.putText(frame, text, (text_x, text_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    print(f"Label: {label}, Value: {value}")

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

                if key == ord('r'):  # Pressione 'r' para remover o último ROI
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
