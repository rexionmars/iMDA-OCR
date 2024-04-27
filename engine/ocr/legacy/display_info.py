import cv2


class FloatingRectangle:

    def __init__(self, window_name, rectangle_size=(120, 30), offset_x=40, offset_y=40):
        self.window_name = window_name
        self.rectangle_size = rectangle_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.current_mouse_position = (0, 0)
        self.text = ""
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._update_mouse_position)

    def _update_mouse_position(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            self.current_mouse_position = (x, y)

    def _draw_rectangle(self, frame):
        x, y = self.current_mouse_position
        w, h = self.rectangle_size
        x1 = x - w // 2 - self.offset_x
        y1 = y - h // 2 - self.offset_y
        x2 = x1 + w
        y2 = y1 + h
        cv2.rectangle(frame, (x1, y1), (x2, y2), (25, 220, 255), 1)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, self.text, (x1 + 5, y1 + 20), font, 0.4, (25, 220, 255), 1, cv2.LINE_AA)

    def set_text(self, text):
        self.text = text

    def run(self):
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            self._draw_rectangle(frame)

            cv2.imshow(self.window_name, frame)

            k = cv2.waitKey(1)

            if k == ord('c'):
                frame[:] = 0

            if k == 27:
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    floating_rectangle = FloatingRectangle('window')
    floating_rectangle.set_text("Hello OpenCV!")
    floating_rectangle.run()
