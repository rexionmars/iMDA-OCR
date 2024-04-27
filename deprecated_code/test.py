import cv2
import easyocr
import json
import re
import concurrent.futures
import requests
import os
import time

from queue import Queue


class TextRecognition:

    def __init__(self, video_source: str, server_url: str, language="en"):
        self.reader = easyocr.Reader([language])
        self.video_capture = VideoCapture(video_source)
        self.server_url = server_url

    def start(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            video_thread = executor.submit(self.video_processing_thread)
            video_thread.result()

    def read_text(self, frame):
        if frame is None:
            return
        rois = self.fetch_rois_from_server(self.server_url)
        self.draw_rois_on_frame(frame, rois)

        roi_data = {}
        for i, roi in enumerate(rois):
            x, y, w, h = roi
            cropped_frame = frame[int(y):int(y + h), int(x):int(x + w)]

            results = self.reader.readtext(cropped_frame)

            roi_info = {}
            list_value = []

            # TODO: print ditc os results
            for bbox, text, prob in results:
                label, value = self.extract_label_and_value(text)
                list_value.append(value)

                if label:
                    if label not in roi_info:
                        roi_info[label] = []

                text_x = x + bbox[0][0]
                text_y = y + bbox[0][1]
                cv2.rectangle(frame, (int(text_x), int(text_y)),
                              (int(x + bbox[2][0]), int(y + bbox[2][1])), (0, 255, 0), 1)
                cv2.putText(frame, text, (int(text_x), int(text_y) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 1)
                cv2.putText(frame, prob, (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            filtered_values = [item for item in list_value if item is not None]
            filtered_values = [float(item) for item in filtered_values]

            for label, values in roi_info.items():
                values.extend(filtered_values)

            roi_data[f"ROI_ID {i}"] = roi_info

        print(json.dumps(roi_data, indent=4))

    def fetch_rois_from_server(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                rois_data = response.json()
                return [(roi['x1'], roi['y1'], roi['x2'], roi['y2']) for roi in rois_data.values()]
            else:
                print("Erro ao buscar os ROIs do servidor. Código de status:", response.status_code)
                print("Resposta do servidor:", response.text)
        except Exception as e:
            print("Erro ao buscar ROIs do servidor:", str(e))
        return []

    def draw_rois_on_frame(self, frame, rois):
        for roi in rois:
            x, y, w, h = roi
            cv2.rectangle(frame, (int(x), int(y)), (int(w), int(h)), (0, 255, 0), 1)

    def print_roi_data(self, roi_data):
        # Your code to print ROI data goes here
        pass

    def extract_label_and_value(self, text: str):
        parts = re.split(r"(\d+)", text)
        label = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else None
        return label, value

    def video_processing_thread(self) -> None:
        while True:
            ret, frame = self.video_capture.read()
            self.read_text(frame)
            cv2.imshow("Text Recognition", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # 27 is the ESC key
                break

        self.video_capture.release()
        cv2.destroyAllWindows()


class VideoCapture:

    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()


if __name__ == "__main__":
    server = "http://127.0.0.1:8080/get-ocr-data"
    text_recognition = TextRecognition("http://192.168.0.38:81/stream", server_url=server)  #OV2640
    text_recognition.start()
