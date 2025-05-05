from fastapi import FastAPI, Request
import hashlib
import sqlite3
from datetime import datetime
from ab_test_config_v2 import AB_TEST_CONFIG

app = FastAPI()
db_path = "db/ab_test.db"

# DB 초기화
def init_db():
    with sqlite3.connect(db_path) as conn:
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


def get_hash_bucket(user_id: str, test_name: str, max_bucket: int = 100) -> int:
    key = f"{user_id}:{test_name}"
    h = hashlib.sha256(key.encode()).hexdigest()
    return int(h, 16) % max_bucket


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        return {"error": "Missing user_id"}

    assigned_tests = []

    for test in AB_TEST_CONFIG:
        if not test["enabled"]:
            continue

        bucket = get_hash_bucket(user_id, test["test_name"])
        if bucket >= test["percentage"]:
            continue  # 제외됨

        # A/B 배정
        variant_bucket = bucket % 100
        if variant_bucket < test["variant_split"]["A"]:
            variant = "A"
        else:
            variant = "B"

        assigned_tests.append({
            "test_name": test["test_name"],
            "variant": variant
        })

        # 저장
        with sqlite3.connect("db_path") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ab_test_log (user_id, test_name, variant, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, config["test_name"], variant, datetime.utcnow().isoformat()))
            conn.commit()

    return {"user_id": user_id, "ab_test": assigned_tests }
