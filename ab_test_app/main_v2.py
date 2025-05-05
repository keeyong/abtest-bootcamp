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
            timestamp TEXT,
            PRIMARY KEY (user_id, test_name)
        )
        """)
init_db()


def split_userid(abtest_id, user_id, size_of_test, num_of_variants=2):
   id = str(user_id) + str(abtest_id)
   h = hashlib.md5(id.encode())
   bucket = int(h.hexdigest(), 16)
   print(size_of_test, bucket % 100, bucket % num_of_variants)
   if (bucket % 100) < size_of_test:
       return bucket % num_of_variants
   else:
       return None


@app.post("/bucket-user")
async def bucket_user(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        return {"error": "Missing user_id"}

    assigned_tests = []

    for test in AB_TEST_CONFIG:
        if not test["enabled"]:
            continue

        bucket = split_userid(test["test_name"], user_id, test["percentage"])

        # 사용자가 AB test에 포함되지 않았다면 다음 AB test로 이동
        if bucket is None:
            continue

        if bucket == 0:
            variant = "A"
        else:
            variant = "B"
 
        assigned_tests.append({
            "test_name": test["test_name"],
            "variant": variant
        })

        # 저장
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ab_test_log (user_id, test_name, variant, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, test["test_name"], variant, datetime.utcnow().isoformat()))
            conn.commit()

    return {"user_id": user_id, "ab_test": assigned_tests }
