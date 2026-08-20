"""
本地冒烟测试：用 FastAPI 的 TestClient 跑一遍核心接口。
运行：在 backend/ 目录下  pytest  （需先 pip install pytest httpx）
"""
import os
import pytest
from fastapi.testclient import TestClient

# 测试专用 token，避免依赖 .env
os.environ["API_TOKEN"] = "test_token"
# 注意：sqlite :memory: 在连接池下每个连接是独立库，表会“消失”，
# 所以测试用临时文件库（跑前删旧文件，保证干净）。
_TEST_DB = "/tmp/health_test.db"
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _TEST_DB

from app.main import app
from app.database import init_db

init_db()
client = TestClient(app)
H = {"Authorization": "Bearer test_token"}


def test_auth_required():
    """没带 token 应返回 401"""
    assert client.get("/api/profile").status_code == 401


def test_profile_flow():
    r = client.post("/api/profile", headers=H, json={
        "gender": "male", "age": 30, "height_cm": 175, "current_weight_kg": 70,
        "daily_calorie_goal": 2000,
    })
    assert r.status_code == 200
    assert r.json()["current_weight_kg"] == 70


def test_food_and_summary():
    client.post("/api/food", headers=H, json={
        "meal_type": "lunch", "name": "鸡胸肉", "weight_g": 200, "calories": 330,
    })
    client.post("/api/food", headers=H, json={
        "meal_type": "breakfast", "name": "燕麦", "calories": 150,
    })
    s = client.get("/api/summary/today", headers=H).json()
    assert s["intake_total"] == 480.0


def test_watch_sync_and_tdee():
    client.post("/api/sync/watch", headers=H, json={
        "active_calories": 600, "steps": 9000,
    })
    s = client.get("/api/summary/today", headers=H).json()
    # BMR = 10*70 + 6.25*175 - 5*30 + 5 = 1648.75 ；TDEE = BMR + 600 = 2248.75
    assert s["tdee"] == pytest.approx(2248.8, abs=1)
    assert s["deficit_or_surplus"] == pytest.approx(2248.8 - 480, abs=1)


def test_trend():
    r = client.get("/api/trend?days=7", headers=H)
    assert r.status_code == 200
    assert len(r.json()["data"]) == 7
