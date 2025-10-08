# writer.py
# Асинхронный писатель клипов — оптимизирован: в очереди храним JPEG-байты, а не сырые BGR-массивы.
# Это существенно снижает потребление оперативной памяти.

import threading
import queue
import traceback
import cv2
import numpy as np
from typing import List, Tuple, Optional
from collections import deque

from detector import ViolationEvent, Detection

# Параметры сжатия JPEG (качество 1..100). 80 — хорошее соотношение.
JPEG_QUALITY = 80

class ClipWriter:
    """
    Асинхронный писатель клипов (пул воркеров).
    Экономит память: в задаче храним (frame_idx, jpg_bytes) вместо (frame_idx, ndarray).
    Воркер декодирует jpeg -> ndarray только при записи.
    """

    def __init__(self, workers: int = 2, queue_max: int = 200, webhook: Optional[str] = None):
        self.queue: "queue.Queue" = queue.Queue(maxsize=queue_max)
        self.stop_event = threading.Event()
        self.workers = []
        self.webhook = webhook
        for _ in range(workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker(self):
        while not self.stop_event.is_set():
            try:
                task = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if task is None:
                self.queue.task_done()
                break
            try:
                self._process_task(task)
            except Exception as e:
                print("[WRITER] Exception:", e)
                traceback.print_exc()
            finally:
                self.queue.task_done()

    def _process_task(self, task: dict):
        # task содержит: frames (list of (frame_idx, jpg_bytes)), fps, out_path, event, clip_detections
        frames: List[Tuple[int, bytes]] = task.get('frames', [])
        fps: float = task.get('fps', 25.0)
        out_path: str = task.get('out_path')
        ev: Optional[ViolationEvent] = task.get('event')
        clip_detections: List[Detection] = task.get('clip_detections', [])

        if not frames:
            print("[WRITER] empty frames for", out_path)
            return

        # Декодируем первый кадр для получения размера
        # frames[0] = (frame_idx, jpg_bytes)
        first = frames[0]
        if isinstance(first, tuple) and len(first) == 2:
            _, jpg0 = first
            arr = np.frombuffer(jpg0, dtype=np.uint8)
            first_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if first_img is None:
                print("[WRITER] cannot decode first frame for", out_path, "- skipping")
                return
            h, w = first_img.shape[:2]
        else:
            print("[WRITER] unexpected frames format - skipping", out_path)
            return

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        if not writer.isOpened():
            print("[WRITER] Failed to open VideoWriter for", out_path)
            return

        # подготовим детекции по кадру
        dets_by_frame = {}
        for d in clip_detections:
            dets_by_frame.setdefault(d.frame_idx, []).append(d)

        # iterate and write (decode each JPEG when needed)
        for item in frames:
            if not (isinstance(item, tuple) and len(item) == 2):
                continue
            f_idx, jpg_bytes = item
            try:
                arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
                f_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if f_img is None:
                    # если не удалось декодировать — пропускаем этот кадр
                    print(f"[WRITER] failed to decode frame {f_idx} in {out_path}")
                    continue
            except Exception as e:
                print(f"[WRITER] exception decoding frame {f_idx}: {e}")
                continue

            frame_copy = f_img  # уже отдельный массив после imdecode
            # рисуем детекции для этого кадра (если есть)
            for d in dets_by_frame.get(f_idx, []):
                x1, y1, x2, y2 = d.bbox
                color = (0,0,255) if d.class_name in ("no_glove","no_head","no_uniform","floor","table") else (0,200,0)
                thickness = max(1, int(min(w,h) / 400))
                cv2.rectangle(frame_copy, (x1,y1),(x2,y2), color, thickness=thickness)
                label = f"{d.class_name} {d.conf:.2f}"
                cv2.putText(frame_copy, label, (x1, max(0,y1-6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1, cv2.LINE_AA)
            # добавим таймстамп/индекс кадра
            ts_text = f"{f_idx}  {f_idx/fps:.1f}s"
            cv2.putText(frame_copy, ts_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1, cv2.LINE_AA)

            writer.write(frame_copy)

        writer.release()

        # обновляем событие
        if ev is not None:
            ev.clip_path = out_path
            ev.saved = True
            ev.pending = False
            ev.enqueued = False

        # webhook
        if self.webhook and ev is not None:
            try:
                import requests
                payload = {
                    'event_id': ev.id,
                    'class_names': ev.class_names,
                    'avg_conf': sum(ev.confs)/len(ev.confs) if ev.confs else None,
                    'time_s': ev.time_s,
                    'wall_time_first': ev.wall_time_first,
                    'clip_path': out_path
                }
                resp = requests.post(self.webhook, json=payload, timeout=5.0)
                if 200 <= resp.status_code < 300:
                    print(f"[WEBHOOK] sent for event {ev.id} -> {resp.status_code}")
                else:
                    print(f"[WEBHOOK] non-2xx for event {ev.id} -> {resp.status_code} {resp.text[:200]}")
            except Exception as e:
                print(f"[WRITER] webhook failed: {e}")

        print(f"[WRITER] finished writing {out_path}")

    def enqueue(self, frames_buffer: deque, event_frame_idx: int, fps: float, out_path: str,
                all_detections: List[Detection], event: Optional[ViolationEvent],
                pre_sec: int=3, post_sec: int=5) -> bool:
        """
        Собирает срез кадров из buffer и помещает задачу в очередь.
        Теперь в frames_to_write кладём (frame_idx, jpeg_bytes) — экономия памяти.
        """
        pre_frames = int(round(pre_sec * fps))
        post_frames = int(round(post_sec * fps))
        start_idx = event_frame_idx - pre_frames
        end_idx = event_frame_idx + post_frames
        frames_to_write = []
        available = [i for i,_ in frames_buffer]
        if not available:
            return False
        max_idx = max(available)
        end_idx_adj = min(end_idx, max_idx)
        # собираем кадры: кодируем в JPEG bytes сразу (сжатые копии)
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        for idx, f in frames_buffer:
            if start_idx <= idx <= end_idx_adj:
                try:
                    # кодируем фрейм в JPEG
                    success, jpg = cv2.imencode('.jpg', f, encode_params)
                    if not success:
                        print(f"[ENQUEUE] jpeg encode failed for frame {idx} (skipping)")
                        continue
                    jpg_bytes = jpg.tobytes()
                    frames_to_write.append((idx, jpg_bytes))
                except Exception as e:
                    print(f"[ENQUEUE] exception encoding frame {idx}: {e}")
                    continue

        clip_dets = [d for d in all_detections if start_idx <= d.frame_idx <= end_idx_adj]
        task = {'frames': frames_to_write, 'fps': fps, 'out_path': out_path, 'event': event, 'clip_detections': clip_dets}
        try:
            self.queue.put(task, block=False)
            if event is not None:
                event.enqueued = True
            return True
        except queue.Full:
            print('[ENQUEUE] task queue full, dropping clip', out_path)
            return False

    def shutdown(self):
        # дождаться всех задач и корректно остановить воркеры
        self.queue.join()
        self.stop_event.set()
        for _ in self.workers:
            try:
                self.queue.put(None)
            except Exception:
                pass
        for t in self.workers:
            t.join(timeout=1.0)
