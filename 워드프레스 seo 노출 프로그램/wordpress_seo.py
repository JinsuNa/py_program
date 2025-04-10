import time
import re
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os


# 설정 파일 로드
def load_config():
    config = {}
    print("설정 파일을 로드하는 중입니다.")
    with open("config.txt") as f:
        for line in f:
            key, value = line.strip().split("= ")
            config[key] = value.strip('"')
    print("설정 파일이 성공적으로 로드되었습니다.")
    return config


config = load_config()

# OpenAI API 키 설정
openai.api_key = config["openai_api"]

# 날짜 확인을 위한 현재 날짜
current_date = datetime.now().strftime("%Y-%m-%d")

# 메모장 파일 경로
memo_path = f"C:/wordpress_seo/{current_date}_posts.txt"

# 크롬 드라이버 설정
driver = webdriver.Chrome()


# 워드프레스 로그인
def wordpress_login():
    print("워드프레스 로그인 페이지로 이동 중입니다.")
    driver.get(f"{config['url']}/wp-login.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "user_login"))
    ).send_keys(config["wordpress_id"])
    driver.find_element(By.ID, "user_pass").send_keys(config["wordpress_pw"])
    driver.find_element(By.ID, "wp-submit").click()
    print("워드프레스에 성공적으로 로그인되었습니다.")
    time.sleep(5)  # 5초 대기


# 금일 작성된 포스트 목록 가져오기
def get_today_posts():
    print("금일 작성된 포스트 목록을 가져오는 중입니다.")
    driver.get(f"{config['url']}/wp-admin/edit.php")

    # 금일 날짜 가져오기 (예: 2024/10/10 형식)
    today_date = datetime.now().strftime("%Y/%m/%d")

    # 포스트 목록에서 날짜 필드를 찾아 금일 작성된 글을 필터링
    post_elements = driver.find_elements(By.CSS_SELECTOR, "tr.type-post")
    today_posts = []

    for post_element in post_elements:
        # 각 포스트의 날짜 가져오기
        date_element = post_element.find_element(By.CSS_SELECTOR, ".date.column-date")
        post_date = date_element.text.strip()

        # 금일 날짜와 비교하여 일치하는 게시물만 저장
        if today_date in post_date:
            post_id = post_element.get_attribute("id").replace("post-", "")
            today_posts.append(post_id)

    print(f"금일 작성된 포스트 {len(today_posts)}개를 확인했습니다.")
    time.sleep(5)  # 5초 대기
    return today_posts


# 슬러그 값 추출 함수 (yoast-google-preview-slug-metabox에서)
def get_slug_value():
    print("슬러그 값을 가져오는 중입니다.")
    slug_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "yoast-google-preview-slug-metabox"))
    )
    slug_value = slug_element.get_attribute("value")

    # '-' 특수기호 제거
    cleaned_slug = re.sub(r"-", "", slug_value)

    print(f"가져온 슬러그 값: {cleaned_slug}")
    time.sleep(5)  # 5초 대기
    return cleaned_slug


# focus-keyword와 meta-description 수정
def edit_post(post_id, slug_value, description):
    print(f"포스트 {post_id}를 수정하는 중입니다.")
    driver.get(f"{config['url']}/wp-admin/post.php?post={post_id}&action=edit")

    # 슬러그 값을 가져옴
    slug_value = get_slug_value()

    # focus-keyword 입력란 찾기 및 수정
    keyword_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "focus-keyword-input-metabox"))
    )
    keyword_input.clear()
    keyword_input.send_keys(slug_value)
    time.sleep(5)  # 5초 대기

    # meta-description 입력란 찾기 및 수정
    description_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, "yoast-google-preview-description-metabox")
        )
    )
    description_field.clear()
    description_field.send_keys(description)
    time.sleep(5)  # 5초 대기

    # 게시물 업데이트 버튼 클릭
    driver.find_element(By.ID, "publish").click()
    print(f"포스트 {post_id}의 수정이 완료되었습니다.")
    time.sleep(5)  # 5초 대기


# OpenAI를 사용해 요약 생성
def generate_summary(text):
    print("OpenAI를 통해 요약을 생성하는 중입니다.")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"해당 글에 대한 요약을 공백 포함 150자로 꼭 맞추시오: {text}",
            },
        ],
        max_tokens=130,
        temperature=0.5,
    )

    summary = response["choices"][0]["message"]["content"].strip()

    # 요약의 길이가 140~150자 사이가 되도록 조정
    if len(summary) > 150:
        summary = summary[:150].strip()  # 150자로 잘라냄
    elif len(summary) < 140:
        summary = summary.ljust(140)  # 140자에 맞추기 위해 공백 추가

    print("요약 생성이 완료되었습니다.")
    time.sleep(5)  # 5초 대기
    return summary


# 게시물의 본문을 추출하는 함수
def get_post_content(post_id):
    print(f"포스트 {post_id}의 내용을 가져오는 중입니다.")
    driver.get(f"{config['url']}/wp-admin/post.php?post={post_id}&action=edit")

    # 게시물의 본문을 포함하는 <textarea> 태그에서 본문을 추출
    content_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "content"))
    )
    post_content = content_element.get_attribute("value")
    print(f"포스트 {post_id}의 내용을 성공적으로 가져왔습니다.")
    time.sleep(5)  # 5초 대기
    return post_content


# 메모장 파일 관리
def manage_memo(post_id):
    print(f"포스트 {post_id}가 이미 처리되었는지 확인하는 중입니다.")
    if os.path.exists(memo_path):
        with open(memo_path, "r") as f:
            processed_posts = f.read().splitlines()
        if str(post_id) in processed_posts:
            print(f"포스트 {post_id}는 이미 처리되었습니다.")
            time.sleep(5)  # 5초 대기
            return False  # 이미 처리된 게시물
    else:
        print(f"메모장이 존재하지 않아 새로 생성합니다: {memo_path}")
        with open(memo_path, "w") as f:
            pass  # 파일 생성

    with open(memo_path, "a") as f:
        f.write(f"{post_id}\n")
    print(f"포스트 {post_id}가 처리 목록에 추가되었습니다.")
    time.sleep(5)  # 5초 대기
    return True


# 300초마다 새 게시물 체크 및 수정
def monitor_new_posts():
    print("새 게시물을 모니터링하는 중입니다.")
    while True:
        today_posts = get_today_posts()
        for post_id in today_posts:
            if manage_memo(post_id):
                # 포스트 내용을 가져옴
                post_content = get_post_content(post_id)

                # OpenAI를 통해 요약 생성
                summary = generate_summary(post_content)

                # 게시물 수정 (슬러그 값을 focus-keyword로 입력)
                edit_post(post_id, post_content, summary)

        print("300초 후에 다시 새 게시물을 확인합니다.")
        time.sleep(300)  # 300초 대기 후 다시 확인


# 프로그램 시작
print("프로그램이 시작되었습니다.")
wordpress_login()
monitor_new_posts()
