import cv2


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

    def draw(self, frame):
        if len(self.current_mouse_position) == 2:
            x, y = self.current_mouse_position
            text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            w = text_size[0] + 10  # Adicionando um espaço extra para o texto dentro do retângulo
            h = text_size[1] + 10  # Adicionando um espaço extra para o texto dentro do retângulo
            x1 = x - w // 2 - self.offset_x
            y1 = y - h // 2 - self.offset_y
            x2 = x1 + w
            y2 = y1 + h
            cv2.rectangle(frame, (x1, y1), (x2, y2 + 10), (25, 220, 255), 1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, self.text, (x1 + 5, y1 + 20), font, 0.4, (25, 220, 255), 1, cv2.LINE_AA)
