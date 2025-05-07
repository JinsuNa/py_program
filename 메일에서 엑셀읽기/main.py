from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from get_mail import get_mail_attachment_json

app = FastAPI()

# CORS 설정 (React 같은 외부에서도 API 호출 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" 대신 ["http://localhost:3000"] 이렇게 써도됨 (보안 강화용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "이메일 파싱 작업입니다."}

@app.get("/emails")
def read_mail_from_email():
    result = get_mail_attachment_json()
    return result

