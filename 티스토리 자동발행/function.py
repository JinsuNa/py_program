import time
import os
import subprocess
import chromedriver_autoinstaller
import pyperclip
import pyautogui
import shutil
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
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    NoAlertPresentException,
)

from prompt import load_keywords


# 크롬이 설치된 경로 (윈도우 기본 설치 경로 기준)
chrome_path = r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

# 크롬 드라이버를 덮어쓸 대상 경로 지정
target_path = r"C:\main_tstroy"


def install_and_move_chromedriver(target_path):
    """
    크롬 드라이버를 설치하거나 업데이트한 후, 지정된 경로로 이동시키는 함수.
    """
    # 크롬 드라이버 자동 설치 또는 업데이트
    chromedriver_path = (
        chromedriver_autoinstaller.install()
    )  # 설치된 크롬 드라이버의 경로 반환

    # 설치된 크롬 드라이버 파일 경로
    chromedriver_exe_path = (
        chromedriver_path  # 이 경로는 이미 'chromedriver.exe' 파일 전체 경로입니다
    )

    # 대상 폴더에 덮어쓸 크롬 드라이버 경로 지정
    target_driver_path = os.path.join(target_path, "chromedriver.exe")

    # 파일 덮어쓰기: chromedriver.exe를 target_path로 복사
    if os.path.exists(chromedriver_exe_path):
        shutil.copy(chromedriver_exe_path, target_driver_path)
        print(f"크롬 드라이버가 {target_path}에 덮어쓰기되었습니다.")
    else:
        print("크롬 드라이버 설치 중 오류가 발생했습니다.")


# 요소가 로드될 때까지 기다리는 유틸리티 함수
def wait_for_element(driver, by, identifier, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, identifier))
        )
        return element
    except TimeoutException:
        print(f"요소를 찾을 수 없습니다: {identifier}")
        return None


# 요소가 클릭 가능할 때까지 기다리는 함수
def wait_for_element_to_be_clickable(driver, by, identifier, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, identifier))
        )
        return element
    except TimeoutException:
        print(f"요소를 클릭할 수 없습니다: {identifier}")
        return None


# config_login 파일에서 ID와 비밀번호 불러오기
def load_login_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        # 파일에서 첫 줄 읽어오기 (ID와 비밀번호는 탭으로 구분됨)
        data = file.readline().strip().split("\t")
        if len(data) == 2:
            return data[0], data[1]  # ID와 비밀번호 반환
        else:
            raise ValueError("ID와 비밀번호 형식이 잘못되었습니다.")


# 파일에서 로그인 정보 불러오기
login_file = "config_login.txt"
user_id, user_pw = load_login_data(login_file)


# URL을 확인하고, 그 페이지에서 CSS 클릭하는 함수


def check_url_and_click(driver, by_method, element_id):
    try:
        # 팝업이 있는지 확인하고 닫기
        try:
            alert = driver.switch_to.alert
            print(f"Alert detected: {alert.text}")
            alert.dismiss()  # 팝업 닫기
        except NoAlertPresentException:
            pass  # 팝업이 없으면 무시하고 넘어감

        # 요소를 클릭하는 작업
        current_url = driver.current_url
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by_method, element_id))
        )
        element.click()

    except UnexpectedAlertPresentException:
        try:
            # 팝업이 있으면 닫기
            alert = driver.switch_to.alert
            print(f"Alert Text: {alert.text}")
            alert.dismiss()  # 팝업 닫기
        except NoAlertPresentException:
            pass  # 팝업이 없으면 무시하고 넘어감

        # 팝업을 닫은 후 다시 작업 시도
        current_url = driver.current_url
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by_method, element_id))
        )
        element.click()

    except Exception as e:
        # 모든 예외 처리
        print(f"예외 발생: {e}")


# 버튼 이미지 좌표 찾기
def find_and_click_button(image_path):
    try:
        button_location = pyautogui.locateCenterOnScreen(image_path, confidence=0.5)
        if button_location:
            pyautogui.click(button_location)  # 해당 좌표 클릭
            return True
        else:
            print("버튼을 찾을 수 없습니다.")
            return False
    except Exception as e:
        print(f"오류 발생: {e}")
        return False


# 텍스트 파일에서 카테고리 ID 불러오기
def load_category_id(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        category_id = file.readline().strip()  # 파일에서 첫 번째 줄을 읽어옴
        return category_id


# 이미 발행된 키워드인지 확인하는 함수
def is_keyword_published(keyword, directory="C:/main_tstroy"):
    # 발행된 키워드에 해당하는 마크다운 파일 경로
    markdown_file_path = os.path.join(directory, f"{keyword}_markdown.txt")

    # 파일이 존재하면 이미 발행된 키워드로 간주
    if os.path.exists(markdown_file_path):
        print(f"'{keyword}'는 이미 발행된 키워드입니다. 다음 키워드로 이동합니다.")
        return True
    else:
        return False


# 이미 발행된 키워드인지 확인하는 함수
def is_keyword_published(keyword, directory="C:/main_tstroy"):
    # 발행된 키워드에 해당하는 마크다운 파일 경로
    markdown_file_path = os.path.join(directory, f"{keyword}_markdown.txt")

    # 파일이 존재하면 이미 발행된 키워드로 간주
    if os.path.exists(markdown_file_path):
        print(f"'{keyword}'는 이미 발행된 키워드입니다. 다음 키워드로 이동합니다.")
        return True
    else:
        return False


# 네이버 API 및 OpenAI API 키 불러오기
def load_api_keys(file_path):
    api_data = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file.readlines():
            key, value = line.strip().split("\t=\t")
            api_data[key] = value.strip('"')
    return api_data


# 네이버 블로그 검색 API로 상위 5개의 URL을 추출하는 함수
def get_blog_posts(keyword, client_id, client_secret):
    url = f"https://openapi.naver.com/v1/search/blog.json?query={keyword}&display=5&sort=sim"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        data = response.json()
        urls = [(item["link"], item["title"]) for item in data["items"]]
        print(f"{keyword}에 대한 상위 5개의 URL을 성공적으로 가져왔습니다: {urls}")
        return urls
    else:
        print(f"Error: {response.status_code}")
        print(f"Response Body: {response.text}")
        return []


# URL에서 블로그 게시물의 본문을 추출하는 함수
def extract_blog_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")

    # 네이버 블로그 본문 컨테이너 탐색
    content = soup.find("div", class_="se-main-container")
    if not content:
        content = soup.find("div", class_="se_component_wrap sect_dsc")

    if not content:
        iframe = soup.find("iframe", {"id": "mainFrame"})
        if iframe:
            iframe_url = "https://blog.naver.com" + iframe["src"]
            iframe_response = requests.get(iframe_url, headers=headers)
            iframe_soup = BeautifulSoup(iframe_response.text, "html.parser")
            content = iframe_soup.find("div", class_="se-main-container")
            if not content:
                content = iframe_soup.find("div", class_="se_component_wrap sect_dsc")

    if content:
        clean_content = content.get_text(strip=True).replace("\u200b", "")
        return clean_content
    return "내용을 찾을 수 없습니다."


# 키워드 메모장에서 가져오기
def load_keywords(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines()]



# 프롬프트 구성 함수 (원고 작성용)
def generate_prompt(a_value, urls_contents, previous_article=None):
    prompt = f"""
# 프롬프트 입력

    if previous_article:
        prompt += f"\n\n이전에 생성된 원고:\n{previous_article}\n\n이 원고에 **중요** **공백제외 2500자 이상이 되도록**, 수정하거나, 첨가하여 원고를 작성해주세요 하지만 공백제외2500자가 되었다고 딱 끊어버리는게 아니라 말은 전부 끝내고 출력해줘."
    for i, (url, content) in enumerate(urls_contents, start=1):
        prompt += f"\n\nURL {i}: {url}\n내용 {i}: {content[:1000]}\n"

    return prompt


# GPT로 원고 생성 함수
def create_article(api_key, a_value, urls_contents):
    previous_article = None

    # 2500자 이상일 때까지 반복
    while True:
        prompt = generate_prompt(a_value, urls_contents, previous_article)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a professional legal writer."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 3200,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )

        if response.status_code == 200:
            article = response.json()["choices"][0]["message"]["content"].strip()
            char_count = len(article.replace(" ", ""))  # 공백 제외 글자 수 검사
            print(f"글자 수가 부족하여 gpt 혼내는 중..... (공백 제외): {char_count}")

            if char_count >= 2500:
                return article  # 2500자 이상일 때 반환
            else:
                print("다시 요청합니다.")
                previous_article = article
        else:
            print(f"Error: {response.status_code}")
            print(f"Response Body: {response.text}")
            return ""


# GPT에게 마크다운 변환 요청
def request_markdown_conversion(api_key, article, keyword):
    markdown_prompt = f"""
    '{article}'의 내용을 수정하지 않고 그대로 <div> 태그 안에 넣고, 시작 부분에는 <br><br>을 추가해.
    대제목(#)은 <h1>, 소제목(##)은 <h2>로 변환하며, <h1>,<h2>에만 다음 스타일을 적용해:
    (border-style: solid; border-width: 0px 0px 1px 14px; border-color: #ee3030; background-color: #fff; padding: 10px 10px; letter-spacing: -1px; color: #000; margin: 1em 0 20px; font-size: 1.44em; line-height: 1.48;)
    각각의 <h1>과 <h2> 앞에는 반드시 <br><br> 태그를 추가해.
    모바일 최적화를 위해 적절한 <h>, <span>, <p>, <br> 태그를 사용해, 그리고 <p> 태그만 line-height: 1.75;로 설정해줘.
    글의 흐름에 맞게 적절한 위치에 <ul>, <ol>, <li> 태그를 삽입해.
    <li> 태그에 margin-top 10px;, margin-bottom 10px; 를 넣어줘.
    대제목과 소제목을 기반으로, 본문 최상단에 목차를 <table> 형식으로 만들어줘.
    목차는 <a> 태그로 각 항목이 본문 내의 해당 id로 연결되도록 설정해. 
    대제목은 id="section1", 소제목은 id="section1_1", id="section1_2", id="section1_3" 와 같은 형식으로 설정해.
    목차에있는 <a>태그에 margin-top 10px;, margin-bottom 10px; 를 넣어줘.

    **중요**: 코드 블록이나 코드 설명 없이, 마크다운 형식으로 적용된 **최종 결과물만 반환**해. 
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a professional markdown converter."},
            {"role": "user", "content": markdown_prompt},
        ],
        "max_tokens": 4000,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )

    if response.status_code == 200:
        markdown_article = response.json()["choices"][0]["message"]["content"].strip()
        markdown_file_path = f"C:/main_tstroy/{keyword}_markdown.txt"
        with open(markdown_file_path, "w", encoding="utf-8") as file:
            file.write(markdown_article)
        print(f"{keyword}의 마크다운 파일이 {markdown_file_path}에 저장되었습니다.")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response Body: {response.text}")


# GPT에게 제목 생성 요청
def generate_title(api_key, article_content):
    title_prompt = f"""
    다음 글을 기반으로 적합한 블로그 제목을 만들어 주세요:
    
    {article_content}
    
    글의 요점을 잘 반영한 40자 이하의 짧고 임팩트 있는 제목으로 작성해 주세요. 그리고 제목에 특수기호는 절대 쓰면 안돼
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional blog title generator.",
            },
            {"role": "user", "content": title_prompt},
        ],
        "max_tokens": 50,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )

    if response.status_code == 200:
        generated_title = response.json()["choices"][0]["message"]["content"].strip()
        return generated_title
    else:
        print(f"Error: {response.status_code}")
        print(f"Response Body: {response.text}")
        return ""


# 파일에서 {keyword}_text.txt 내용 읽기 및 제목 생성 요청
def request_title_generation(api_key, keyword):
    text_file_path = f"C:/main_tstroy/{keyword}_text.txt"

    # 파일 내용 읽기
    with open(text_file_path, "r", encoding="utf-8") as file:
        article_content = file.read()

    # 제목 생성 요청
    generated_title = generate_title(api_key, article_content)

    print(f"'{keyword}'에 대한 생성된 제목: {generated_title}")

    # 제목을 별도의 파일로 저장
    title_file_path = f"C:/main_tstroy/{keyword}_title.txt"
    with open(title_file_path, "w", encoding="utf-8") as file:
        file.write(generated_title)
    print(f"'{keyword}'에 대한 제목이 {title_file_path}에 저장되었습니다.")


# 제목 파일에서 제목을 읽어와 제목 입력란에 붙여넣기
def paste_title_to_blog(driver, keyword):
    title_file_path = f"C:/main_tstroy/{keyword}_title.txt"

    try:
        # 파일에서 제목 읽기
        with open(title_file_path, "r", encoding="utf-8") as file:
            blog_title = file.read().strip()

        # 제목 입력란이 나타날 때까지 기다림
        title_input = wait_for_element(driver, By.ID, "post-title-inp")
        if title_input:
            pyperclip.copy(blog_title)
            title_input.click()
            title_input.send_keys(Keys.CONTROL, "v")  # 붙여넣기 수행
            time.sleep(5)  # 2초 대기
        else:
            print("제목 입력란을 찾을 수 없습니다.")
    except Exception as e:
        print(f"제목 입력란을 찾을 수 없거나 파일을 읽을 수 없습니다: {e}")


# 마크다운 파일 내용을 id가 'editor-tistory'인 텍스트 입력란에 붙여넣기
def paste_markdown_content_to_blog(driver, keyword):
    try:
        # 메모장에서 텍스트 읽어오기
        markdown_file_path = f"C:/main_tstroy/{keyword}_markdown.txt"
        with open(markdown_file_path, "r", encoding="utf-8") as file:
            markdown_content = file.read()

        # 'editor-tistory_ifr'이라는 id를 가진 iframe으로 전환
        wait_for_element(
            driver, By.ID, "editor-tistory_ifr"
        )  # iframe이 나타날 때까지 기다림
        driver.switch_to.frame("editor-tistory_ifr")

        # pyperclip을 사용하여 클립보드에 텍스트 복사
        pyperclip.copy(markdown_content)

        # iframe 내부에서 텍스트 입력할 위치 찾기
        textarea = wait_for_element(
            driver, By.ID, "tinymce"
        )  # textarea가 나타날 때까지 기다림
        if textarea:
            textarea.click()  # 텍스트 영역 클릭하여 포커스

            # 텍스트를 붙여넣기 (CTRL + V)
            textarea.send_keys(Keys.CONTROL, "v")

            # 작업을 마쳤으면 다시 기본 페이지로 돌아옴
            driver.switch_to.default_content()

            time.sleep(5)  # 대기 시간 추가
        else:
            print("텍스트 입력란을 찾을 수 없습니다.")

    except Exception as e:
        print(f"마크다운 내용을 입력할 수 없습니다: {e}")


# 현재 작업 중인 키워드를 tagText 입력란에 붙여넣기
def paste_keyword_to_tag_text(driver, keyword):
    try:
        # pyperclip을 사용해 현재 작업 중인 키워드를 클립보드에 복사
        pyperclip.copy(keyword)

        # id가 tagText인 입력란 요소가 나타날 때까지 기다림
        tag_input = wait_for_element(driver, By.ID, "tagText")
        if tag_input:
            tag_input.click()  # 입력란 클릭하여 포커스

            # 붙여넣기 수행 (CTRL + V)
            tag_input.send_keys(Keys.CONTROL, "v")
            time.sleep(5)  # 2초 대기
        else:
            print("태그 입력란을 찾을 수 없습니다.")
    except Exception as e:
        print(f"키워드를 tagText 입력란에 입력할 수 없습니다: {e}")
