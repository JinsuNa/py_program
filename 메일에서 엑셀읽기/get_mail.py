import email
import imaplib
import os
from email.header import decode_header
import pandas as pd

from config import ACCOUNT, PASSWORD

IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = ACCOUNT
EMAIL_PASSWORD = PASSWORD

# 현재 파일의 절대 경로 기준으로 저장 폴더 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "attachments")
os.makedirs(SAVE_DIR, exist_ok=True)

def decode_subject(subject_raw):
    """이메일 제목 디코딩"""
    decoded_subject, encoding = decode_header(subject_raw)[0]
    if isinstance(decoded_subject, bytes):
        return decoded_subject.decode(encoding if encoding else "utf-8")
    return decoded_subject

def get_mail_attachment_json():
    """첨부파일 있는 메일의 CSV/XLSX 파일을 JSON으로 파싱"""
    global df
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()

    result_list = []

    # 최근 100개 메일만 체크
    for num in reversed(mail_ids[-10:]):
        status, msg_data = mail.fetch(num, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = msg.get("Subject")
        decoded_subject = decode_subject(subject)

        has_attachment = False

        if msg.is_multipart():
            for part in msg.walk():
                filename = part.get_filename()

                if filename:
                    has_attachment = True
                    filename = decode_header(filename)[0][0]
                    if isinstance(filename, bytes):
                        filename = filename.decode()

                    # CSV / XLSX 만 처리
                    if filename.endswith(".csv") or filename.endswith(".xlsx"):
                        filepath = os.path.join(SAVE_DIR, filename)

                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))

                        if filename.endswith(".csv"):
                            df = pd.read_csv(filepath)
                        elif filename.endswith(".xlsx"):
                            df = pd.read_excel(filepath)

                        json_data = df.to_dict(orient="records")

                        result_list.append({
                            "email_subject": decoded_subject,
                            "filename": filename,
                            "data": json_data
                        })

    mail.logout()

    if result_list:
        return {"status": "success", "files": result_list}
    else:
        return {"status": "fail", "message": "첨부된 CSV 또는 XLSX 파일 없음"}

if __name__ == "__main__":
    result = get_mail_attachment_json()
    print(result)
