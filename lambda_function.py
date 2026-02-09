import json
import os
import uuid
import base64
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket = os.environ["BUCKET_NAME"]

    # 1) 들어온 이벤트를 먼저 로그로 확인
    print("event:", event)
    print("raw_body(original):", event.get("body"))
    print("isBase64Encoded:", event.get("isBase64Encoded"))

    # 2) body 안전 처리 (없으면 빈 JSON)
    raw_body = event.get("body") or "{}"

    # 3) base64 인코딩이면 디코딩
    if event.get("isBase64Encoded"):
        try:
            raw_body = base64.b64decode(raw_body).decode("utf-8")
        except Exception as e:
            print("base64 decode error:", str(e))
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid base64 body"})
            }

    print("raw_body(final):", raw_body)

    # 4) JSON 파싱
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON body"})
        }

    # 5) 저장 키 생성
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"api-results/{ts}-{uuid.uuid4().hex}.json"

    # 6) S3 저장
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json"
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": True, "bucket": bucket, "key": key}, ensure_ascii=False)
    }
