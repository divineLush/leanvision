# main.py
# Главный CLI: сборка пайплайна, цикл по кадрам, логика finalize (debounce) и экспорт отчетов.

import argparse
from collections import deque
import pandas as pd
from tqdm import tqdm
import os
import cv2

from config import *
from utils import ensure_dir, now_iso
from model_iface import YoloModel
from detector import ViolationDetector, Detection
from writer import ClipWriter


def process_video(model_path, video_path, out_dir, conf_thresh=CONF_THRESH, detect_every_n=DETECT_EVERY_N_FRAMES,
                  merge_sec=MERGE_WINDOW_SEC, finalize_delay=FINALIZE_DELAY, save_immediately=False,
                  workers=ASYNC_WORKERS, webhook=None):
    ensure_dir(out_dir)
    clips_dir = os.path.join(out_dir, 'clips')
    ensure_dir(clips_dir)

    model = YoloModel(model_path)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    # буфер кадров
    max_buffer_sec = CLIP_PRE_SEC + CLIP_POST_SEC + finalize_delay + 2
    frames_buffer = deque(maxlen=int(max_buffer_sec * fps) + 10)

    detector = ViolationDetector(merge_window_sec=merge_sec)
    writer = ClipWriter(workers=workers, queue_max=TASK_QUEUE_MAXSIZE, webhook=webhook)

    all_detections = []
    pbar = tqdm(total=total, desc='Processing frames')
    idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames_buffer.append((idx, frame.copy()))
            current_s = idx / fps
            wall_t = now_iso()

            # финализировать pending события при простое
            for ev in list(detector.events):
                if ev.pending and not ev.saved and not ev.enqueued:
                    if current_s - ev.last_update_s >= finalize_delay:
                        clip_filename = f"event_{ev.id}_{'_'.join(ev.class_names)}_{int(ev.time_s)}s.mp4"
                        clip_path = os.path.join(clips_dir, clip_filename)
                        success = writer.enqueue(frames_buffer, ev.frame_idx, fps, clip_path, all_detections, ev,
                                                  pre_sec=CLIP_PRE_SEC, post_sec=CLIP_POST_SEC)
                        if success:
                            print(f"[ENQUEUE] {ev.id}")

            if idx % detect_every_n == 0:
                dets = model.predict_frame(frame, conf=conf_thresh)
                for cname, conf, bbox in dets:
                    if conf < conf_thresh:
                        continue
                    det = Detection(class_name=cname, conf=conf, bbox=bbox, frame_idx=idx, time_s=current_s, wall_time=wall_t)
                    all_detections.append(det)
                    if cname in VIOLATION_CLASSES:
                        is_new, ev = detector.register_detection(det, current_s)
                        if is_new and save_immediately:
                            clip_path = os.path.join(clips_dir, f"event_{ev.id}_{'_'.join(ev.class_names)}_{int(ev.time_s)}s.mp4")
                            writer.enqueue(frames_buffer, ev.frame_idx, fps, clip_path, all_detections, ev,
                                           pre_sec=CLIP_PRE_SEC, post_sec=CLIP_POST_SEC)
            idx += 1
            pbar.update(1)
    finally:
        # финализировать оставшиеся
        for ev in detector.events:
            if ev.pending and not ev.saved and not ev.enqueued:
                clip_path = os.path.join(clips_dir, f"event_{ev.id}_{'_'.join(ev.class_names)}_{int(ev.time_s)}s_final.mp4")
                writer.enqueue(frames_buffer, ev.frame_idx, fps, clip_path, all_detections, ev,
                               pre_sec=CLIP_PRE_SEC, post_sec=CLIP_POST_SEC)
        writer.shutdown()
        pbar.close()
        cap.release()

    # экспорт отчётов
    det_rows = []
    for d in all_detections:
        det_rows.append({'wall_time': d.wall_time, 'time_s': d.time_s, 'frame_idx': d.frame_idx,
                         'class_name': d.class_name, 'conf': d.conf, 'bbox': d.bbox})
    df = pd.DataFrame(det_rows)
    df.to_csv(os.path.join(out_dir, 'detections_all.csv'), index=False)

    ev_rows = []
    for e in detector.events:
        ev_rows.append({'id': e.id, 'class_names': e.class_names, 'confs': e.confs, 'time_s': e.time_s,
                        'frame_idx': e.frame_idx, 'wall_time_first': e.wall_time_first, 'bbox': e.bbox,
                        'clip_path': e.clip_path, 'saved': e.saved})
    pd.DataFrame(ev_rows).to_csv(os.path.join(out_dir, 'violations_events.csv'), index=False)

    print('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=MODEL_PATH)
    parser.add_argument('--video', default=INPUT_VIDEO)
    parser.add_argument('--out', default=OUTPUT_DIR)
    parser.add_argument('--conf', type=float, default=CONF_THRESH)
    parser.add_argument('--every', type=int, default=DETECT_EVERY_N_FRAMES)
    parser.add_argument('--merge_sec', type=int, default=MERGE_WINDOW_SEC)
    parser.add_argument('--finalize-delay', type=float, default=FINALIZE_DELAY)
    parser.add_argument('--save-immediately', action='store_true')
    parser.add_argument('--workers', type=int, default=ASYNC_WORKERS)
    parser.add_argument('--webhook', type=str, default=None)
    args = parser.parse_args()

    process_video(
        model_path=args.model,
        video_path=args.video,
        out_dir=args.out,
        conf_thresh=args.conf,
        detect_every_n=args.every,
        merge_sec=args.merge_sec,
        finalize_delay=args.finalize_delay,
        save_immediately=args.save_immediately,
        workers=args.workers,
        webhook=args.webhook
    )