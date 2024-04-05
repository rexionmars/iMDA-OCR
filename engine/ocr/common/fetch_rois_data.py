import cv2
import requests
import numpy as np

def fetch_rois_from_server(url):
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

def draw_rois_on_frame(frame, rois):
    for roi in rois:
        x, y, w, h = roi
        cv2.rectangle(frame, (int(x), int(y)), (int(w), int(h)), (0, 255, 0), 1)



def main():
    server_url = "http://127.0.0.1:8080/get_roi_data"
    video_stream_url = "http://192.168.0.51:81/stream"

    cap = cv2.VideoCapture(video_stream_url)

    while True:
        # Buscar ROIs do servidor
        rois = fetch_rois_from_server(server_url)

        # Capturar frame do vídeo
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame do vídeo.")
            break

        # Desenhar ROIs no frame
        draw_rois_on_frame(frame, rois)
        # Exibir resolução atual
        resolution = f"{frame.shape[1]} x {frame.shape[0]}"
        cv2.putText(frame, resolution, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

        # Exibir o frame com os ROIs
        cv2.imshow("ROIs from Server", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # 27 é a tecla ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
