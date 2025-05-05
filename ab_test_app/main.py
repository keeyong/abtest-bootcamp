from fastapi import FastAPI, Request
import hashlib
import sqlite3
from datetime import datetime
from ab_test_config import AB_TEST_CONFIG

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


def split_userid(id, num_of_variants=2):
     h = hashlib.md5(str(id).encode())
     return int(h.hexdigest(), 16) % num_of_variants 


@app.post("/bucket-user")
async def bucket_user(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    # user_id가 존재하지 않는다면 에러 리턴
    if not user_id:
        return {"error": "Missing user_id"}

    config = AB_TEST_CONFIG
    # 해당 AB 테스트가 활성화되지 않았다면 소속된 AB 테트스 정도 없이 리턴
    if not config["enabled"]:
        return {"user_id": user_id, "ab_test": None}

    # bucket 정보를 바탕으로 이를 db에 저장
    variant = 'A' if split_userid(user_id) == 0 else 'B' 

    # DB에 로그하기
    # 사실은 로그 파일이나 NoSQL 등에 저장하는 것이 더 선호됨
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ab_test_log (user_id, test_name, variant, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, config["test_name"], variant, datetime.utcnow().isoformat()))
        conn.commit()

    return {"user_id": user_id, "ab_test": {"test_name": config["test_name"], "variant": variant}}
