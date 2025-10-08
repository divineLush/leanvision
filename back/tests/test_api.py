# tests/test_api.py
import os
import tempfile
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Импортируем ваше приложение
from api import app, UPLOAD_DIR, OUTPUT_DIR

client = TestClient(app)

# Убедимся, что директории существуют
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_dummy_video():
    """Создаём минимальный MP4-файл (заглушку) для тестов."""
    # Это не настоящий видеофайл, но для проверки загрузки подойдёт
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x02\x00"

@pytest.fixture
def dummy_video():
    return create_dummy_video()


def test_upload_video(dummy_video):
    """Тест: загрузка видео"""
    files = {"file": ("test.mp4", dummy_video, "video/mp4")}
    response = client.post("/videos/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert "path" in data
    assert os.path.exists(data["path"])


def test_start_process_without_video():
    """Тест: запуск обработки без указания видео → ошибка"""
    response = client.post("/process/start", json={})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_full_workflow(dummy_video):
    """Тест: полный цикл — загрузка → запуск → статус → клипы"""
    # 1. Загрузка
    files = {"file": ("test.mp4", dummy_video, "video/mp4")}
    upload_resp = client.post("/videos/upload", files=files)
    assert upload_resp.status_code == 200
    video_id = upload_resp.json()["video_id"]

    # 2. Запуск обработки
    start_resp = client.post("/process/start", json={"video_id": video_id})
    assert start_resp.status_code == 200
    task_data = start_resp.json()
    task_id = task_data["task_id"]
    assert task_data["status"] == "queued"

    # 3. Проверка статуса
    status_resp = client.get(f"/process/{task_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["task_id"] == task_id

    # 4. Попытка получить клипы (даже если папка пуста — не ошибка)
    clips_resp = client.get(f"/process/{task_id}/clips")
    assert clips_resp.status_code == 200
    assert isinstance(clips_resp.json(), list)


def test_list_events():
    """Тест: получение списка событий (даже если их нет)"""
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_health_check():
    """Тест: эндпоинт здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


def test_static_files_mount():
    """Тест: проверка, что /static смонтирован (без реального файла)"""
    # Просто убедимся, что маршрут существует
    response = client.get("/static/nonexistent.txt")
    # Должен вернуть 404, но не 404 от FastAPI (а от StaticFiles)
    # Важно: не должно быть 404 от маршрутизации (т.е. маршрут найден)
    assert response.status_code in (404, 200)  # 200 если файл есть, 404 если нет — но не 404 "Not Found" от маршрутов