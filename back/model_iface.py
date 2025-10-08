# model_iface.py
# Интерфейс для загрузки и запуска вашей YOLO модели (ultralytics API).

from ultralytics import YOLO
from typing import List, Tuple
import numpy as np

from config import MODEL_CLASSES


class YoloModel:
    """Класс-обёртка вокруг ultralytics YOLO для удобства вызова."""
    def __init__(self, path: str):
        # загрузка модели
        self.model = YOLO(path)
        # если имена классов не заданы в модели — ставим по конфигу
        if not getattr(self.model, 'names', None):
            self.model.names = {i: name for i, name in enumerate(MODEL_CLASSES)}

    def predict_frame(self, frame: np.ndarray, conf: float=0.5) -> List[Tuple[str, float, Tuple[int,int,int,int]]]:
        """Запускает инференс по одному кадру и возвращает список (class_name, conf, xyxy).
        Возвращаемые боксы уже в координатах кадра (целые числа).
        """
        results = self.model.predict(source=frame, imgsz=640, conf=conf, verbose=False)
        res = results[0] if isinstance(results, list) else results
        boxes = getattr(res, 'boxes', None)
        if boxes is None:
            return []
        xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes.xyxy, 'cpu') else np.array(boxes.xyxy)
        confs = boxes.conf.cpu().numpy() if hasattr(boxes.conf, 'cpu') else np.array(boxes.conf)
        cls_idxs = boxes.cls.cpu().numpy().astype(int) if hasattr(boxes.cls, 'cpu') else np.array(boxes.cls).astype(int)
        out = []
        for box, c, cls in zip(xyxy, confs, cls_idxs):
            x1, y1, x2, y2 = map(int, box.tolist())
            name = self.model.names.get(int(cls), str(int(cls)))
            out.append((name, float(c), (x1, y1, x2, y2)))
        return out