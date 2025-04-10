import time
import os
import subprocess
import chromedriver_autoinstaller
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
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# pyautogui가 DPI-aware 모드에서 작동하도록 설정 (Windows)
from ctypes import windll
from function import (
    update_chrome,
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
)

windll.user32.SetProcessDPIAware()

# 크롬 드라이버 자동 설치 또는 업데이트
chromedriver_autoinstaller.install(True)

# 크롬 옵션 설정 (디버깅 포트 사용)
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# Selenium이 디버깅 모드로 실행된 브라우저에 연결
driver = webdriver.Chrome(options=chrome_options)


try:
    write_button = driver.find_element(By.XPATH, "//a[contains(@href, 'newpost')]")
    driver.execute_script("arguments[0].setAttribute('target', '_top');", write_button)
    write_button.click()
    time.sleep(5)
except Exception as e:
    print(f"글쓰기 버튼을 클릭할 수 없습니다: {e}")

# '확인' 텍스트가 포함된 버튼을 기다린 후 클릭하는 코드
try:
    # "확인" 버튼이 로드될 때까지 대기 (최대 10초)
    confirm_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="확인"]'))
    )
    # 버튼 클릭
    confirm_button.click()
    print("확인 버튼 클릭 성공")
except Exception as e:
    print(f"확인 버튼 클릭 중 오류 발생: {e}")
