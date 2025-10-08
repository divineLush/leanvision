# config.py
# Центральные параметры системы. Меняйте по окружению/камере.

MODEL_PATH = "models/best.pt"
INPUT_VIDEO = "input_shift.mp4"
OUTPUT_DIR = "results_shift"

# параметры инференса
CONF_THRESH = 0.5
DETECT_EVERY_N_FRAMES = 5

# параметры клипов
CLIP_PRE_SEC = 3
CLIP_POST_SEC = 5
MERGE_WINDOW_SEC = 10
FINALIZE_DELAY = 5.0

# классы модели: имена должны совпадать с вашей моделью YOLO
MODEL_CLASSES = ["floor", "glove", "head", "no_glove", "no_head", "no_uniform", "table", "uniform"]
VIOLATION_CLASSES = {"no_glove", "no_head", "no_uniform", "floor", "table"}

# очередь/воркеры
ASYNC_WORKERS = 2
TASK_QUEUE_MAXSIZE = 200

# webhook
WEBHOOK_URL = None  # при необходимости укажите URL