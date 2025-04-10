import time
import os
import subprocess
import chromedriver_autoinstaller
import shutil
import pyperclip
import pyautogui
import requests
import urllib3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    NoAlertPresentException,
)
from function import (
    load_login_data,
    check_url_and_click,
    find_and_click_button,
    load_category_id,
    load_api_keys,
    get_blog_posts,
    extract_blog_content,
    load_keywords,
    generate_prompt,
    create_article,
    request_markdown_conversion,
    generate_title,
    request_title_generation,
    paste_title_to_blog,
    paste_markdown_content_to_blog,
    paste_keyword_to_tag_text,
    wait_for_element,
    wait_for_element_to_be_clickable,
    is_keyword_published,
    install_and_move_chromedriver,
)


# SSL 경고 메시지를 무시하는 설정
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 크롬 드라이버 자동 설치 또는 업데이트
chromedriver_autoinstaller.install()

# 크롬 드라이버를 덮어쓸 대상 경로 지정
target_path = r"C:\main_tstroy"

# 크롬 드라이버 설치 및 덮어쓰기 실행
install_and_move_chromedriver(target_path)

# 크롬이 설치된 경로 (윈도우 기본 설치 경로 기준)
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


# 크롬 옵션 설정
chrome_options = Options()

# iPad Pro 12.9인치의 해상도와 사용자 에이전트 설정
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Safari/605.1.15"
)
chrome_options.add_argument("--window-size=1024,1366")  # iPad Pro 12.9인치 해상도

# Chrome 드라이버 실행
driver = webdriver.Chrome(options=chrome_options)

# 티스토리 로그인 페이지로 이동
driver.get("https://www.tistory.com/auth/login")
time.sleep(5)  # 페이지 로딩을 위해 대기

# link_kakao_id 클래스를 가진 카카오 로그인 버튼 클릭
check_url_and_click(driver, By.CLASS_NAME, "btn_login.link_kakao_id")

# 파일에서 로그인 정보 불러오기
login_file = "config_login.txt"
user_id, user_pw = load_login_data(login_file)


# 취소,완료 버튼 이미지 파일 경로
cancel_button_image = r"C:\main_tstroy\cancel_button_image.png"
done_button_image = r"C:\main_tstroy\done_button_image.png"


# 카테고리 파일 경로
category_file = "config_category.txt"
# 카테고리 ID 불러오기
category_id = load_category_id(category_file)


# 메인 실행 함수
def main():
    # API 키 및 설정 파일 로드
    config_file = "config_naver_api.txt"
    api_keys = load_api_keys(config_file)

    client_id = api_keys["client_id"]
    client_secret = api_keys["client_secret"]
    openai_api_key = api_keys["openai_api"]

    # 키워드 파일에서 키워드 읽기
    keyword_file = "C:/main_tstroy/config_keyword.txt"
    keywords = load_keywords(keyword_file)

    first_run = True  # 첫 실행 여부를 확인하는 플래그

    for keyword in keywords:
        print(f"{keyword}에 대한 작업을 시작합니다.")

        # 이미 발행된 키워드인지 확인
        if is_keyword_published(keyword):
            continue  # 발행된 키워드는 건너뛰기

        # 첫 번째 실행일 때만 로그인 및 기본 글쓰기 버튼 클릭
        if first_run:
            # ID 입력란에 pyperclip을 사용하여 로그인 정보 입력 후 로그인
            try:
                id_input = driver.find_element(By.ID, "loginId--1")
                pyperclip.copy(user_id)
                id_input.click()
                id_input.send_keys(webdriver.common.keys.Keys.CONTROL, "v")
                time.sleep(3)
            except Exception as e:
                print(f"ID 입력란을 찾을 수 없습니다: {e}")

            # PW 입력란에 pyperclip을 사용하여 비밀번호 입력
            try:
                pw_input = driver.find_element(By.ID, "password--2")
                pyperclip.copy(user_pw)
                pw_input.click()
                pw_input.send_keys(webdriver.common.keys.Keys.CONTROL, "v")
                time.sleep(3)
            except Exception as e:
                print(f"비밀번호 입력란을 찾을 수 없습니다: {e}")

            # 로그인 버튼 클릭
            try:
                element = driver.find_element(By.CLASS_NAME, "btn_g.highlight.submit")
                element.click()
                time.sleep(10)
            except Exception as e:
                print(f"요소를 클릭할 수 없습니다: {e}")

            # 첫 번째 글쓰기 버튼 클릭
            try:
                write_button = driver.find_element(
                    By.XPATH, "//a[contains(@href, 'newpost')]"
                )
                driver.execute_script(
                    "arguments[0].setAttribute('target', '_top');", write_button
                )
                write_button.click()
                time.sleep(5)
            except UnexpectedAlertPresentException:
                pass  # 팝업 무시하고 넘어감
            except Exception as e:
                print(f"글쓰기 버튼을 클릭할 수 없습니다: {e}")

            first_run = False  # 첫 실행이 끝났으므로 False로 설정
        else:
            # 첫 실행이 아닌 경우 link_write 클래스 클릭
            try:
                write_button = driver.find_element(By.CLASS_NAME, "link_write")
                write_button.click()
                time.sleep(5)
            except Exception as e:
                print(f"link_write 글쓰기 버튼을 클릭할 수 없습니다: {e}")

        # 글 이어쓰기 취소 버튼 클릭
        time.sleep(5)
        find_and_click_button(cancel_button_image)

        # 카테고리 선택
        check_url_and_click(driver, By.ID, "category-btn")
        check_url_and_click(driver, By.ID, category_id)

        # 네이버 블로그 API로 상위 5개의 URL 가져오기
        urls = get_blog_posts(keyword, client_id, client_secret)
        urls_contents = []

        # 각 URL에서 본문 가져오기
        for url, _ in urls:
            content = extract_blog_content(url)
            urls_contents.append((url, content))

        # 본문을 메모장에 저장
        blog_file_path = f"C:/main_tstroy/{keyword}_blog_crawling.txt"
        with open(blog_file_path, "w", encoding="utf-8") as file:
            for url, content in urls_contents:
                file.write(f"URL: {url}\n{content}\n\n")
        print(f"{keyword}에 대한 본문을 {blog_file_path}에 저장했습니다.")

        # 원고 생성 및 2500자 이상일 때까지 반복
        article = create_article(openai_api_key, keyword, urls_contents)

        # 원고 파일로 저장
        output_file = f"C:/main_tstroy/{keyword}_text.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(article)

        # 마크다운 형식으로 변환
        request_markdown_conversion(openai_api_key, article, keyword)

        # 제목 생성 및 저장
        request_title_generation(openai_api_key, keyword)

        # 블로그 제목 붙여넣기
        paste_title_to_blog(driver, keyword)

        # 마크다운 내용 붙여넣기
        paste_markdown_content_to_blog(driver, keyword)

        # 키워드를 tagText에 붙여넣기
        paste_keyword_to_tag_text(driver, keyword)

        # 마크다운 모드로 변경하기
        check_url_and_click(driver, By.ID, "editor-mode-layer-btn-open")
        check_url_and_click(driver, By.ID, "editor-mode-markdown")
        time.sleep(5)
        # 이어서 진행
        find_and_click_button(done_button_image)

        # 마크다운 모드에서 br이 포함된 span 요소를 찾아 엔터를 입력
        time.sleep(10)
        br_element = driver.find_element(
            By.XPATH, "//span[@class='cm-tag' and text()='br']"
        )

        # 해당 요소에 포커스 맞추기 (스크롤 및 클릭)
        time.sleep(5)
        driver.execute_script(
            "arguments[0].scrollIntoView();", br_element
        )  # 화면에 보이게 스크롤
        br_element.click()  # 요소 클릭하여 포커스 맞추기

        # ActionChains로 엔터 키 입력
        time.sleep(3)
        actions = ActionChains(driver)
        actions.move_to_element(br_element).send_keys(Keys.ENTER).perform()

        time.sleep(2)  # 동작이 완료되도록 대기

        check_url_and_click(driver, By.ID, "publish-layer-btn")
        check_url_and_click(driver, By.ID, "publish-btn")
        time.sleep(5)  # 발행 후 잠시 대기

    print("모든 키워드 작업이 완료되었습니다.")


if __name__ == "__main__":
    main()
