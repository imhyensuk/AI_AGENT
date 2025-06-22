# tools/mongo.py

import os
from dotenv import load_dotenv
import pymongo
from bson.objectid import ObjectId
import json

# .env에서 MONGODB_URI 불러오기
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI가 .env 파일에 정의되어 있어야 합니다.")

def get_collection(db_name, coll_name):
    client = pymongo.MongoClient(MONGODB_URI)
    db = client[db_name]
    collection = db[coll_name]
    return collection

def run(
    action=None,           # "find", "find_one", "insert", "update", "delete"
    db_name=None,          # 데이터베이스 이름
    coll_name=None,        # 컬렉션 이름
    query=None,            # dict, 조회/수정/삭제 조건
    data=None,             # dict, 삽입/수정할 데이터
    update=None,           # dict, update 명령 (예: {"$set": {...}})
    many=False,            # 여러 개 작업 여부
    object_id=None,        # _id로 직접 접근 시
    projection=None        # dict, 반환 필드 제한(예: {"name": 1, "_id": 0})
):
    """
    action: "find", "find_one", "insert", "update", "delete" 중 하나
    db_name: 데이터베이스 이름
    coll_name: 컬렉션 이름
    query: dict, 조회/수정/삭제 조건
    data: dict, 삽입 또는 수정할 데이터
    update: dict, update 명령 (예: {"$set": {...}})
    many: 여러 개 작업 여부 (True/False)
    object_id: _id로 직접 접근 시(str 또는 ObjectId)
    projection: dict, 반환 필드 제한(예: {"name": 1, "_id": 0})
    """
    if not db_name or not coll_name:
        return "db_name과 coll_name을 지정해 주세요."
    collection = get_collection(db_name, coll_name)
    try:
        # _id로 직접 접근 보정
        if object_id:
            if not query:
                query = {}
            query["_id"] = ObjectId(object_id) if not isinstance(object_id, ObjectId) else object_id

        if action == "find":
            cursor = collection.find(query or {}, projection or None)
            results = [doc for doc in cursor]
            for doc in results:
                doc["_id"] = str(doc["_id"])
            limited = results[:10]  # 최대 10건만 반환
            return (
                "조회 결과가 없습니다."
                if not limited
                else "조회 결과(최대 10건):\n" + json.dumps(limited, ensure_ascii=False, indent=2)
            )
        elif action == "find_one":
            doc = collection.find_one(query or {}, projection or None)
            if doc:
                doc["_id"] = str(doc["_id"])
                return "조회 결과(1건):\n" + json.dumps(doc, ensure_ascii=False, indent=2)
            else:
                return "조회 결과가 없습니다."
        elif action == "insert":
            if not data:
                return "삽입할 data를 입력해 주세요."
            result = collection.insert_one(data)
            return f"삽입 완료: _id={str(result.inserted_id)}"
        elif action == "update":
            if not query or not update:
                return "수정할 query와 update를 모두 입력해 주세요."
            if many:
                result = collection.update_many(query, update)
                return f"{result.modified_count}개 문서가 수정되었습니다."
            else:
                result = collection.update_one(query, update)
                return f"{result.modified_count}개 문서가 수정되었습니다."
        elif action == "delete":
            if not query:
                return "삭제할 query를 입력해 주세요."
            if many:
                result = collection.delete_many(query)
                return f"{result.deleted_count}개 문서가 삭제되었습니다."
            else:
                result = collection.delete_one(query)
                return f"{result.deleted_count}개 문서가 삭제되었습니다."
        else:
            return "지원하지 않는 action입니다. (find, find_one, insert, update, delete 중 선택)"
    except Exception as e:
        return f"MongoDB 작업 중 오류 발생: {e}"
