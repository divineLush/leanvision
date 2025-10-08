# utils.py
# Утилитарные функции: файловая система, время, bbox

import os
import datetime
from typing import Tuple


def ensure_dir(path: str):
    """Создаёт директорию, если её нет."""
    os.makedirs(path, exist_ok=True)


def now_iso() -> str:
    """Текущее локальное время в формате ISO с временной зоной."""
    return datetime.datetime.now().astimezone().isoformat()


def union_bbox(a: Tuple[int,int,int,int], b: Tuple[int,int,int,int]):
    """Возвращает охватывающую bbox коробку для двух xyxy-боксов."""
    x1 = min(a[0], b[0])
    y1 = min(a[1], b[1])
    x2 = max(a[2], b[2])
    y2 = max(a[3], b[3])
    return (x1, y1, x2, y2)


def iou(boxA: Tuple[int,int,int,int], boxB: Tuple[int,int,int,int]) -> float:
    """Простая IoU между двумя bbox (xyxy)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    boxAArea = max(0, boxA[2]-boxA[0]) * max(0, boxA[3]-boxA[1])
    boxBArea = max(0, boxB[2]-boxB[0]) * max(0, boxB[3]-boxB[1])
    denom = boxAArea + boxBArea - interArea
    if denom == 0:
        return 0.0
    return interArea / denom