import cv2
import numpy as np

current_mouse_position = (0, 0)
rectangle_size = (120, 30)  # Tamanho fixo do retângulo
offset_y = 40  # Deslocamento vertical em relação ao mouse
offset_x = 40


def draw(event, x, y, flags, param):
    global current_mouse_position

    current_mouse_position = (x, y)

    if event == cv2.EVENT_MOUSEMOVE:
        win[:] = 0  # Limpa a janela a cada movimento do mouse
        draw_rectangle(win, current_mouse_position, rectangle_size)


def draw_rectangle(image, position, size):
    x, y = position
    w, h = size
    # Calcula as coordenadas do retângulo para que ele esteja 20 pixels acima do cursor do mouse
    x1 = x - w // 2 - offset_x
    y1 = y - h // 2 - offset_y
    x2 = x1 + w
    y2 = y1 + h
    # Desenha o retângulo na imagem
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), -1)
    # Adiciona o texto "Selecione o ROI" dentro do retângulo
    cv2.putText(image, "Selecione o ROI", (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)


cv2.namedWindow('window')
cv2.setMouseCallback('window', draw)

win = np.zeros((500, 500, 3), dtype='uint8')

while True:
    cv2.imshow('window', win)

    k = cv2.waitKey(1)

    if k == ord('c'):
        win[:] = 0

    if k == 27:
        cv2.destroyAllWindows()
        break
