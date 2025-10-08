# detector.py
# Логика объединения детекций в события (блоки), debounce и хранение метаданных событий.

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import threading

from utils import union_bbox, iou, now_iso
from config import VIOLATION_CLASSES


@dataclass
class Detection:
    class_name: str
    conf: float
    bbox: Tuple[int,int,int,int]
    frame_idx: int
    time_s: float
    wall_time: str


@dataclass
class ViolationEvent:
    id: int
    class_names: List[str] = field(default_factory=list)
    confs: List[float] = field(default_factory=list)
    bbox: Tuple[int,int,int,int] = (0,0,0,0)
    frame_idx: int = 0
    time_s: float = 0.0
    wall_time_first: str = ""
    pending: bool = True
    last_update_s: float = 0.0
    saved: bool = False
    enqueued: bool = False


class ViolationDetector:
    """Класс агрегирует детекции в события. Потокобезопасен (лок при регистрации)."""

    def __init__(self, merge_window_sec: int = 10):
        self.events: List[ViolationEvent] = []
        self.next_id = 1
        self.merge_window = merge_window_sec
        self.lock = threading.Lock()

    def register_detection(self, det: Detection, current_s: float) -> (bool, ViolationEvent):
        """
        Регистрируем детекцию. Если она попадает в существующее событие (тот же кадр или
        близко по времени + пространственно), то сливаем. Иначе создаём новое событие.
        Возвращаем (is_new_event_created, event)
        """
        with self.lock:
            now = det.time_s
            for ev in self.events[::-1]:
                time_close = abs(ev.time_s - now) <= self.merge_window
                same_frame = (ev.frame_idx == det.frame_idx)
                spatial = iou(ev.bbox, det.bbox) > 0.1
                if same_frame or (time_close and spatial):
                    if det.class_name not in ev.class_names:
                        ev.class_names.append(det.class_name)
                    ev.confs.append(det.conf)
                    ev.bbox = union_bbox(ev.bbox, det.bbox)
                    if det.time_s < ev.time_s:
                        ev.time_s = det.time_s
                        ev.frame_idx = det.frame_idx
                    ev.last_update_s = current_s
                    ev.pending = True
                    ev.saved = False
                    ev.enqueued = False  # сбрасываем маркер, т.к. появились новые данные
                    return False, ev
            # create
            ev = ViolationEvent(
                id=self.next_id,
                class_names=[det.class_name],
                confs=[det.conf],
                bbox=det.bbox,
                frame_idx=det.frame_idx,
                time_s=det.time_s,
                wall_time_first=det.wall_time,
                pending=True,
                last_update_s=current_s,
                saved=False,
                enqueued=False
            )
            self.next_id += 1
            self.events.append(ev)
            return True, ev