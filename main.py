from fastapi import FastAPI, Request
import hashlib
import sqlite3
from datetime import datetime

app = FastAPI()

# A/B 테스트 설정 (예: 100명 중 50명만 참여, A/B 각각 50%)
AB_TEST_CONFIG = {
    "test_name": "new_button_color",
    "enabled": True,
    "percentage": 50,  # 전체 중 50%만 참여
    "variant_split": {"A": 50, "B": 50}  # 참여자 중 A/B를 50:50으로
}

# DB 초기화
def init_db():
    with sqlite3.connect("ab_test.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_test_log (
            user_id TEXT,
            test_name TEXT,
            variant TEXT,
            timestamp TEXT
        )
        """)
init_db()


def get_hash_bucket(user_id: str, max_bucket: int = 100) -> int:
    h = hashlib.sha256(user_id.encode()).hexdigest()
    return int(h, 16) % max_bucket


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        return {"error": "Missing user_id"}

    config = AB_TEST_CONFIG
    if not config["enabled"]:
        return {"user_id": user_id, "ab_test": None}

    bucket = get_hash_bucket(user_id)
    if bucket >= config["percentage"]:
        return {"user_id": user_id, "ab_test": "excluded"}

    # Assign variant
    variant_bucket = bucket % 100
    if variant_bucket < config["variant_split"]["A"]:
        variant = "A"
    else:
        variant = "B"

    # Log to DB
    with sqlite3.connect("ab_test.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ab_test_log (user_id, test_name, variant, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, config["test_name"], variant, datetime.utcnow().isoformat()))
        conn.commit()

    return {"user_id": user_id, "ab_test": {"test_name": config["test_name"], "variant": variant}}

