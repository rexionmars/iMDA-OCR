import pygame
import sys
import cv2
import numpy as np
import easyocr
import pandas as pd
import time
import json
import re
import threading
import argparse
from queue import Queue
from typing import List



# Assumindo que essas importações estão disponíveis em seu projeto
from configurations.constants import DEFAULT_COLOR_DETECTION_TEXT as GREEN
from configurations.debug_flag_control import ENABLE_VISUAL_GEOMETRIC_DETECTORS

class BasicGeometrics:
    @staticmethod
    def rounded_rectangle(surface, bbox, length_of_corner=5, thickness_of_line=1, radius_corner=3):
        x, y, w, h = bbox
        x1, y1 = x + w, y + h
        color = (255, 255, 0)  # Yellow

        pygame.draw.line(surface, color, (x, y), (x + length_of_corner, y), thickness_of_line)
        pygame.draw.line(surface, color, (x, y), (x, y + length_of_corner), thickness_of_line)
        pygame.draw.line(surface, color, (x1, y), (x1 - length_of_corner, y), thickness_of_line)
        pygame.draw.line(surface, color, (x1, y), (x1, y + length_of_corner), thickness_of_line)
        pygame.draw.line(surface, color, (x, y1), (x + length_of_corner, y1), thickness_of_line)
        pygame.draw.line(surface, color, (x, y1), (x, y1 - length_of_corner), thickness_of_line)
        pygame.draw.line(surface, color, (x1, y1), (x1 - length_of_corner, y1), thickness_of_line)
        pygame.draw.line(surface, color, (x1, y1), (x1, y1 - length_of_corner), thickness_of_line)

class FloatingRectangle:
    def __init__(self, window_name, offset_x=40, offset_y=40):
        self.window_name = window_name
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.current_mouse_position = (0, 0)
        self.text = ""

    def set_position(self, position):
        self.current_mouse_position = position

    def set_text(self, text):
        self.text = text

    def draw(self, surface):
        x, y = self.current_mouse_position
        font = pygame.font.Font(None, 24)
        text_surface = font.render(self.text, True, (25, 220, 255))
        text_rect = text_surface.get_rect()
        
        w = text_rect.width + 10
        h = text_rect.height + 10
        x1 = x - w // 2 - self.offset_x
        y1 = y - h // 2 - self.offset_y
        
        pygame.draw.rect(surface, (25, 220, 255), (x1, y1, w, h), 1)
        surface.blit(text_surface, (x1 + 5, y1 + 5))

class VideoCapture:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()

class TextRecognition:
    stage_texts = [
        "Select the Information Unit", "Enter the label name", "Select the main value", "Select the minimum value",
        "Select the maximum value"
    ]

    def __init__(self, video_source, language="en"):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Text Recognition")

        self.geometric = BasicGeometrics()
        self.reader = easyocr.Reader([language])
        self.video_capture = VideoCapture(video_source)
        self.floating_rectangle = FloatingRectangle("Text Recognition")
        self.event_queue = Queue()
        self.rois = []
        self.deleted_rois = []
        self.drawing = False
        self.running = True
        self.last_frame = None
        self.current_roi = None
        self.stage = 0
        self.show_floating_rectangle = True
        self.delayed_processing_thread = threading.Thread(target=self.__delayed_processing)
        self.delayed_processing_thread.daemon = True
        self.delayed_processing_thread.start()
        self.label_text = ""
        self.start_time = None
        self.text = ""
        self.clock = pygame.time.Clock()

    def start(self):
        self.display_window()

    def __process_filtered_values(self, filtered_values: List[float]) -> None:
        self.event_queue.put((filtered_values))

    def __save_data_in_interval(self, unit_name: str, unit_values: List[float]) -> None:
        if self.start_time is None:
            self.start_time = time.time()

        current_time = time.time()
        elapsed_time = int(current_time - self.start_time)

        data_unit = {
            "unit_name": unit_name,
            "current": unit_values[0] if unit_values else 0,
            "min": unit_values[1] if len(unit_values) > 1 else 0,
            "max": unit_values[2] if len(unit_values) > 2 else 0,
            "time": elapsed_time
        }
        df = pd.DataFrame(data_unit, index=[0])
        df.to_csv(f"{unit_name}.csv", mode="a", header=False, index=False)

    def __delayed_processing(self) -> None:
        while self.running:
            if not self.event_queue.empty():
                filtered_values = self.event_queue.get()
                label = self.text[22:].upper()
                label = label.replace(" ", "_")

                time.sleep(1)
                self.__print_roi_data(label, filtered_values)
                self.__save_data_in_interval(label, filtered_values)

    def __extract_label_and_value(self, text):
        parts = re.split(r"(\d+)", text)
        _label = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else None
        return value

    def __print_roi_data(self, unit_name: str, unit_values: List[float]) -> None:
        _unit_data_structure = {
            f"{unit_name}": {
                "current": unit_values[0] if unit_values else 0,
                "min": unit_values[1] if len(unit_values) > 1 else 0,
                "max": unit_values[2] if len(unit_values) > 2 else 0,
            }
        }
        print(json.dumps(_unit_data_structure, indent=4))

    def read_text(self, frame: np.ndarray) -> None:
        if frame is None:
            return

        if self.stage == len(self.__class__.stage_texts):
            for roi in self.rois:
                x, y, w, h = roi
                cropped_frame = frame[y:y + h, x:x + w]
                gray_cropped_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
                results = self.reader.readtext(gray_cropped_frame)

                list_value = []

                for bbox, text, _prob in results:
                    value = self.__extract_label_and_value(text)
                    list_value.append(value)

                    self.__process_filtered_values([float(value) if value is not None else 0])

                    text_x = x + bbox[0][0]
                    text_y = y + bbox[0][1]

                    if ENABLE_VISUAL_GEOMETRIC_DETECTORS:
                        pygame.draw.rect(self.screen, GREEN, (text_x, text_y, bbox[2][0] - bbox[0][0], bbox[2][1] - bbox[0][1]), 1)
                        font = pygame.font.Font(None, 24)
                        text_surface = font.render(text, True, GREEN)
                        self.screen.blit(text_surface, (text_x, text_y - 10))

                _filtered_values = [float(item) for item in list_value if item is not None]

                self.geometric.rounded_rectangle(self.screen, (x, y, w, h), thickness_of_line=1)

        self.last_frame = frame

    def draw_text_input(self, prompt):
        self.text = "Enter the label name: "
        self.floating_rectangle.set_text(prompt)

        input_active = True
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        if len(self.text) > len("Enter the label name: "):
                            self.text = self.text[:-1]
                    elif event.unicode.isprintable():
                        self.text += event.unicode

            self.screen.fill((0, 0, 0))
            self.floating_rectangle.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(30)

        return self.text

    def display_window(self):
        label_text = None

        while self.running:
            ret, frame = self.video_capture.read()
            if ret:
                # Corrigir a orientação da imagem
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.width, self.height))
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                frame = pygame.surfarray.make_surface(frame)
                self.screen.blit(frame, (0, 0))

                self.display_text_instructions()
                if self.stage < len(self.stage_texts) and self.stage_texts[self.stage] == "Enter the label name":
                    label_text = self.draw_text_input("Enter the label: ")
                    print(f"[INFO] Label Text: {label_text}")
                    self.stage += 1
                else:
                    if self.stage < len(self.stage_texts):
                        if self.current_roi is not None:
                            self.geometric.rounded_rectangle(self.screen, self.current_roi, thickness_of_line=1)
                        for roi in self.rois:
                            self.geometric.rounded_rectangle(self.screen, roi, thickness_of_line=1)
                    self.read_text(pygame.surfarray.array3d(self.screen))

                    if self.show_floating_rectangle:
                        self.floating_rectangle.draw(self.screen)

                pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.remove_last_roi()
                    elif event.key == pygame.K_u:
                        self.undo_roi_deletion()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.on_mouse_events("down", *event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.on_mouse_events("motion", *event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.on_mouse_events("up", *event.pos)

            if label_text is not None:
                self.label_text = label_text
                label_text = None

            self.clock.tick(30)

        self.video_capture.release()
        pygame.quit()

    def display_text_instructions(self):
        if self.stage < len(self.stage_texts):
            text = self.stage_texts[self.stage]
        else:
            text = "Process completed. Press 'q' or 'ESC' to exit."
            self.show_floating_rectangle = False

        self.floating_rectangle.set_text(text)

    def on_mouse_events(self, event_type, x, y):
        if event_type == "down":
            if self.stage < len(self.stage_texts):
                self.drawing = True
                self.current_roi = [x, y, 0, 0]
        elif event_type == "motion":
            if not self.drawing:
                self.floating_rectangle.set_position((x, y))
            if self.drawing:
                self.floating_rectangle.set_position((x, y))
                if self.current_roi is not None:
                    self.current_roi[2] = x - self.current_roi[0]
                    self.current_roi[3] = y - self.current_roi[1]
        elif event_type == "up":
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

def main(camera_index):
    text_recognition = TextRecognition(camera_index)
    text_recognition.start()
    while text_recognition.running:
        pass  # Aguarde até que a tecla "q" ou "ESC" seja pressionada
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script para reconhecimento de texto com índice da câmera')
    parser.add_argument('--camera-index', type=str, default=0, help='Índice da câmera (padrão: 0)')
    args = parser.parse_args()
    main(args.camera_index)