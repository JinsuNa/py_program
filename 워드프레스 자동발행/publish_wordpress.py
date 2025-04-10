# 구글시트에 있는 데이터를 가지고 워드프레스에 자동으로 올려주는 프로그램 디폴트값

import json
import requests
from urllib.parse import urljoin
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time  # 딜레이를 추가하기 위해 time 모듈 사용

# 구글 시트와 연동
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "C:/wordpress/json/flowing-density-434702-e9-d71bfc242bdc.json", scope
)  # 구글 API 인증 키 경로 수정
client = gspread.authorize(creds)

# 구글 스프레드시트 불러오기
spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1_syBuzRmshz95CH5NbOBGHqmCKQe73ae36hZxqRh6rU/edit?gid=652544916#gid=652544916"
)
sheet = spreadsheet.worksheet("워드프레스")

# 각 열의 데이터를 가져오기
wp_urls = sheet.col_values(1)[1:]  # A2:A (워드프레스 URL)
wp_usernames = sheet.col_values(2)[1:]  # B2:B (워드프레스 사용자 이름)
wp_passwords = sheet.col_values(3)[1:]  # C2:C (워드프레스 비밀번호)
slugs = sheet.col_values(4)[1:]  # D2:D (슬러그)
titles = sheet.col_values(7)[1:]  # G2:G (제목)
tags_column = sheet.col_values(8)[1:]  # H2:H (태그)
contents = sheet.col_values(9)[1:]  # I2:I (본문 내용)


# 사용자 정의 HTML 블록 생성 함수
def create_html_block(content):
    # 사용자 정의 HTML 블록을 생성
    return f"<!-- wp:html --><div>{content}</div><!-- /wp:html -->"


# 태그를 H2:H에서 추출하는 함수
def tags_from_sheet(tags_column):
    # 쉼표로 구분된 태그들을 리스트로 반환
    return [tag.strip() for tag in tags_column.split(",") if tag.strip()]


# 태그를 확인하고 없으면 생성하는 함수
def get_or_create_tag(wp_url, wp_username, wp_password, tag_name):
    """
    워드프레스에서 태그를 확인하고 없으면 생성하는 함수
    """
    # 태그 검색 요청
    search_url = urljoin(wp_url, f"wp-json/wp/v2/tags?search={tag_name}")
    try:
        search_res = requests.get(search_url, auth=(wp_username, wp_password))
        if search_res.ok:
            tags = search_res.json()
            if tags:  # 이미 태그가 있는 경우
                return tags[0]["id"]
        else:
            print(f"태그 검색 실패: {search_res.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"태그 검색 중 에러 발생: {e}")
        return None

    # 태그가 없는 경우 새로 생성
    create_url = urljoin(wp_url, "wp-json/wp/v2/tags")
    payload = {
        "name": tag_name,
    }
    try:
        create_res = requests.post(
            create_url,
            data=json.dumps(payload),
            headers={"Content-type": "application/json"},
            auth=(wp_username, wp_password),
        )
        if create_res.ok:
            tag = create_res.json()
            return tag["id"]  # 생성된 태그의 ID 반환
        else:
            print(f"태그 생성 실패: {create_res.status_code} {create_res.text}")
    except requests.exceptions.RequestException as e:
        print(f"태그 생성 중 에러 발생: {e}")

    return None


# 메타 설명 자동 생성 함수
def generate_meta_description(title, content):
    # 120~155자 범위 내에서 적절한 메타 설명을 생성
    description = content[:150] + "..." if len(content) > 150 else content
    return description


# 워드프레스에 포스팅하는 함수
def post_to_wordpress(
    wp_url, wp_username, wp_password, slug, title, content, tags_column
):
    status = "publish"  # 상태 설정 (publish: 즉시발행, draft: 임시저장)

    # URL이 https://로 시작하지 않으면 자동으로 추가
    if not wp_url.startswith("https://"):
        wp_url = "https://" + wp_url

    # 사용자 정의 HTML 블록으로 변환
    html_block = create_html_block(content)

    # H2:H에서 태그를 추출하고, 각 태그의 ID를 가져옴
    tag_names = tags_from_sheet(tags_column)
    tag_ids = []
    for tag_name in tag_names:
        tag_id = get_or_create_tag(wp_url, wp_username, wp_password, tag_name)
        if tag_id:
            tag_ids.append(tag_id)

    # 메타 설명 자동 생성
    meta_description = generate_meta_description(title, content)

    # 포커스 키프레이즈는 태그 중 첫 번째 항목을 사용
    focus_keyword = tag_names[0] if tag_names else title

    # HTML 블록을 포함하는 payload
    payload = {
        "status": status,
        "slug": slug,
        "title": title,
        "content": html_block,  # 사용자 정의 HTML 블록이 포함된 콘텐츠
        "date": datetime.now().isoformat(),
        "tags": tag_ids,  # 태그 ID 배열을 사용
        "meta": {
            "yoast_wpseo_metadesc": meta_description,  # Yoast SEO의 메타 설명 필드 추가
            "yoast_wpseo_focuskw": focus_keyword,  # Yoast SEO의 포커스 키프레이즈 추가
        },
    }

    # API 요청
    try:
        res = requests.post(
            urljoin(wp_url, "wp-json/wp/v2/posts"),
            data=json.dumps(payload),
            headers={"Content-type": "application/json"},
            auth=(wp_username, wp_password),
        )

        if res.ok:
            print(f"포스팅 완료")
        else:
            print(
                f"포스팅 실패 code: {res.status_code} reason: {res.reason} msg: {res.text}"
            )
    except requests.exceptions.RequestException as e:
        print(f"요청 중 에러 발생: {e}")


# 각 데이터에 대해 워드프레스에 포스팅
for wp_url, wp_username, wp_password, slug, title, content, tags_column in zip(
    wp_urls, wp_usernames, wp_passwords, slugs, titles, contents, tags_column
):
    post_to_wordpress(
        wp_url, wp_username, wp_password, slug, title, content, tags_column
    )
