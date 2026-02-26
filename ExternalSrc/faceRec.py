import json
import time
from typing import Dict, Optional, Tuple, List
import cv2
from picamera2 import Picamera2
import numpy as np


def start_camera(
    size: Tuple[int, int] = (840, 480),
    pixel_format: str = "RGB888",
    cascade_path: str = "haarcascade_frontalface_default.xml",
    lbph_path: str = "lbph.yml",
    labels_path: str = "labels.json",
):
    p = Picamera2()
    cfg = p.create_preview_configuration(main={"format": pixel_format, "size": size})
    p.configure(cfg)
    p.start()

    det = cv2.CascadeClassifier(cascade_path)
    if det.empty():
        raise FileNotFoundError(f"Failed to load cascade: {cascade_path}")

    rec = cv2.face.LBPHFaceRecognizer_create()
    rec.read(lbph_path)

    with open(labels_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    id2name: Dict[int, str] = {v: k for k, v in m.items()}

    return p, det, rec, id2name


def run_inference(
    p: Picamera2,
    det: cv2.CascadeClassifier,
    rec: "cv2.face_LBPHFaceRecognizer",
    id2name: Dict[int, str],
    *,
    threshold: float = 70.0,
    allowed_names: Optional[List[str]] = ("user1", "user2"),
    min_face: Tuple[int, int] = (20, 20),
    scale_factor: float = 1.2,
    min_neighbors: int = 5,
    roi_size: Tuple[int, int] = (300, 300),
    window_name: str = "rec",
    timeout: float = 15.0,
) -> int:
    start_time = time.time()
    try:
        while True:
            f = p.capture_array()
            faces = det.detectMultiScale(f, scale_factor, min_neighbors, minSize=min_face)
            detected_user = None

            for (x, y, w, h) in faces:
                cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 2)
                g = cv2.cvtColor(f[y:y+h, x:x+w], cv2.COLOR_RGB2GRAY)
                g = cv2.resize(g, roi_size)
                label, conf = rec.predict(g)

                if conf <= threshold:
                    name = id2name.get(label, "")
                    if not allowed_names or name in allowed_names:
                        cv2.rectangle(f, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        cv2.putText(
                            f,
                            name,
                            (x, y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2,
                        )
                        detected_user = name

            cv2.imshow(window_name, f)

            if detected_user == "user1":
                cv2.waitKey(1500)
                return "user_A"
            elif detected_user == "user2":
                cv2.waitKey(1500)
                return "user_B"

            if time.time() - start_time > timeout:
                return 0

            if cv2.waitKey(1) & 0xFF == 27:
                return 0
    finally:
        cv2.destroyAllWindows()



def stop_camera(p: Picamera2):
    try:
        p.stop()
    finally:
        cv2.destroyAllWindows()

def set_fullscreen(window_name: str):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

def show_black_screen(window_name: str = "rec"):
    black_frame = np.zeros((480, 840, 3), dtype=np.uint8)
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(window_name, black_frame)
    cv2.waitKey(1)
