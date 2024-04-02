import cv2
import easyocr
import json
import re
import sys
import concurrent.futures
from queue import Queue

class TextRecognition:
    def __init__(self, video_source, language="en"):
        self.reader = easyocr.Reader([language])
        self.video_capture = VideoCapture(video_source)
        self.last_frame = None
        self.rois = []
        self.current_roi = None
        self.drawing = False
        self.deleted_rois = []
        self.running = True
        self.event_queue = Queue()

    def start(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            video_thread = executor.submit(self.video_processing_thread)
            user_input_thread = executor.submit(self.handle_user_input)
            self.display_window()
            video_thread.result()
            user_input_thread.result()

    def read_text(self, frame):
        if frame is None:
            return
        roi_data = {}
        for i, roi in enumerate(self.rois):
            x, y, w, h = roi
            cropped_frame = frame[y:y + h, x:x + w]
            results = self.reader.readtext(cropped_frame)

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

        if self.current_roi is not None:
            x, y, w, h = self.current_roi
            cv2.rectangle(frame, (x, y), (x + w, y + h), (129, 23, 255), 1)

        self.last_frame = frame

    def print_roi_data(self, roi_data):
        # Your code to print ROI data goes here
        pass

    def extract_label_and_value(self, text):
        parts = re.split(r"(\d+)", text)
        label = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else None
        return label, value

    def video_processing_thread(self):
        while self.running:
            ret, frame = self.video_capture.read()
            self.read_text(frame)

    def display_window(self):
        cv2.namedWindow("Text Recognition")
        cv2.setMouseCallback("Text Recognition", self.on_mouse_events)

        while self.running:
            if self.last_frame is not None:
                cv2.imshow("Text Recognition", self.last_frame)

            key = cv2.waitKey(1) & 0xFF
            self.event_queue.put(key)

        self.video_capture.release()
        cv2.destroyAllWindows()

    def on_mouse_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_roi = [x, y, 0, 0]

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.current_roi[2] = x - self.current_roi[0]
            self.current_roi[3] = y - self.current_roi[1]

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.rois.append(tuple(self.current_roi))
            self.current_roi = None

    def remove_last_roi(self):
        if self.rois:
            self.deleted_rois.append(self.rois.pop())

    def undo_roi_deletion(self):
        if self.deleted_rois:
            self.rois.append(self.deleted_rois.pop())

    def handle_user_input(self):
        while self.running:
            key = self.event_queue.get()
            if key == ord("q") or key == 27:  # 27 is the ESC key
                self.running = False
            elif key == ord("d"):
                self.remove_last_roi()
            elif key == ord("u"):
                self.undo_roi_deletion()

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
    #text_recognition = TextRecognition("http://192.168.0.51:81/stream")
    text_recognition = TextRecognition("http://192.168.0.38:81/stream") #OV2640
    text_recognition.start()
    while text_recognition.running:
        pass  # Wait until the "q" or "ESC" key is pressed
    sys.exit(0)
