import cv2
import numpy as np


class FloatingRectangle:

    def __init__(self, window_name, rectangle_size=(120, 30), offset_x=40, offset_y=40):
        self.window_name = window_name
        self.rectangle_size = rectangle_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.current_mouse_position = (0, 0)
        self.text = ""

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.draw)

        self.win = np.zeros((500, 500, 3), dtype='uint8')

    def draw(self, event, x, y, flags, param):
        self.current_mouse_position = (x, y)

        if event == cv2.EVENT_MOUSEMOVE:
            self.win[:] = 0  # Limpa a janela a cada movimento do mouse
            self.draw_rectangle(self.win, self.current_mouse_position, self.rectangle_size)

    def draw_rectangle(self, image, position, size):
        x, y = position
        w, h = size
        # Calcula as coordenadas do retângulo para que ele esteja acima do cursor do mouse
        x1 = x - w // 2 - self.offset_x
        y1 = y - h // 2 - self.offset_y
        x2 = x1 + w
        y2 = y1 + h
        # Desenha o retângulo na imagem
        cv2.rectangle(image, (x1, y1), (x2, y2), (25, 220, 255), 1)
        # Adiciona o texto dentro do retângulo
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image, self.text, (x1 + 5, y1 + 20), font, 0.4, (25, 220, 255), 1, cv2.LINE_AA)

    def set_text(self, text):
        self.text = text

    def run(self):
        while True:
            cv2.imshow(self.window_name, self.win)

            k = cv2.waitKey(1)

            if k == ord('c'):
                self.win[:] = 0

            if k == 27:
                cv2.destroyAllWindows()
                break


if __name__ == "__main__":
    floating_rectangle = FloatingRectangle('window')
    floating_rectangle.set_text("Selecione o ROI")
    floating_rectangle.run()
