import cv2

from configurations.constants import DEAFULT_COLOR_DETECTION_RECTANGLE as YELLOW


class BasicGeometrics:

    @staticmethod
    def rounded_rectangle(frame, bbox, lenght_of_corner=5, thickness_of_line=1, radius_corner=3):
        x, y, w, h = bbox
        x1, y1 = x + w, y + h

        # Draw straight lines
        cv2.line(frame, (x, y), (x + lenght_of_corner, y), YELLOW, thickness_of_line)
        cv2.line(frame, (x, y), (x, y + lenght_of_corner), YELLOW, thickness_of_line)

        # Top Right  x1,y
        cv2.line(frame, (x1, y), (x1 - lenght_of_corner, y), YELLOW, thickness_of_line)
        cv2.line(frame, (x1, y), (x1, y + lenght_of_corner), YELLOW, thickness_of_line)

        # Bottom Left  x,y1
        cv2.line(frame, (x, y1), (x + lenght_of_corner, y1), YELLOW, thickness_of_line)
        cv2.line(frame, (x, y1), (x, y1 - lenght_of_corner), YELLOW, thickness_of_line)

        # Bottom Right  x1,y1
        cv2.line(frame, (x1, y1), (x1 - lenght_of_corner, y1), YELLOW, thickness_of_line)
        cv2.line(frame, (x1, y1), (x1, y1 - lenght_of_corner), YELLOW, thickness_of_line)

        return frame
