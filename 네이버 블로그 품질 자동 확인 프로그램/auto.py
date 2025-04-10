import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random
import os
import sys
import traceback


# 스크립트 파일의 디렉토리 경로
current_dir = r"C:\main_blogstandard"

# JSON 키 파일 경로
json_key_file = r"C:\main_blogstandard\json\flowing-density-434702-e9-d71bfc242bdc.json"

# Google Sheets API 설정
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

try:
    print(f"JSON 키 파일 경로: {json_key_file}")
    if not os.path.exists(json_key_file):
        raise FileNotFoundError(f"JSON 키 파일을 찾을 수 없습니다: {json_key_file}")

    print("JSON 키 파일 내용 확인 중...")
    with open(json_key_file, 'r') as file:
        print(file.read()[:100] + "...") # 파일 내용의 일부만 출력

    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_file, scope)
    print("credentials 생성 완료")

    client = gspread.authorize(creds)
    print("gspread client 생성 완료")

    # 구글 스프레드시트 열기
    sheet_url = 'https://docs.google.com/spreadsheets/d/1JGGyuzJt-z3HRdMIaGpOg6NhAQ21G4xkdfWnwgzxq7s/edit?gid=0'
    spreadsheet = client.open_by_url(sheet_url)
    print("구글 스프레드시트에 성공적으로 연결되었습니다.")

except Exception as e:
    print(f"Google Sheets 연결 오류: {e}")
    print("상세 오류 정보:")
    traceback.print_exc()
    input("엔터를 눌러 프로그램을 종료하세요...")
    sys.exit(1)

def get_login_credentials(spreadsheet):
    try:
        credentials_sheet = spreadsheet.worksheet('블로그스탠다드 id/pw')
        username = credentials_sheet.acell('A2').value
        password = credentials_sheet.acell('B2').value
        return username, password
    except Exception as e:
        print(f"로그인 정보를 가져오는 중 오류 발생: {e}")
        return None, None

def login_and_search_keywords():
    driver = None
    try:
        print("Chrome 드라이버 초기화 중...")
        driver = webdriver.Chrome()
        print("웹사이트에 접속 중...")
        driver.get("https://blogstand.net/analysis/blog")
        
        print("로그인 정보 가져오는 중...")
        username, password = get_login_credentials(spreadsheet)
        if not username or not password:
            raise ValueError("로그인 정보를 가져올 수 없습니다.")
        
        print("로그인 과정 시작...")
        username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "loginBtn")))
        login_button.click()
        print("로그인 성공!")

        print("키워드 검색 및 결과 기록 시작...")
        keywords_sheet = spreadsheet.worksheet('검수 키워드')
        keywords = keywords_sheet.col_values(2)[1:]  # B2부터 데이터 가져오기
        keywords = [kw for kw in keywords if kw.strip()]  # 빈 문자열 제거
        
        results_sheet = spreadsheet.worksheet('키워드 분석 결과')
        
        # 3행부터 기존 데이터 삭제
        results_sheet.batch_clear(['A3:Z'])
        
        print(f"검색할 키워드 수: {len(keywords)}")
        for index, keyword in enumerate(keywords, start=1):
            print(f"키워드 {index}/{len(keywords)} 검색 중: '{keyword}'")
            keyword_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "keyword")))
            keyword_input.clear()
            keyword_input.send_keys(keyword)
            
            search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "searchBtn")))
            search_button.click()
            
            # 검색 후 5~20초 사이 대기
            sleep_time = random.uniform(5, 20)
            time.sleep(sleep_time)

            print(f"키워드 '{keyword}' 검색 완료, 결과 추출 중...")

            # row-id="1"부터 row-id="10"까지 블로그 레벨 추출
            blog_levels = []
            for row_id in range(1, 11):
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f"div[row-id='{row_id}'] div[col-id='blogLevel']"))
                    )
                    blog_levels.append(element.text)
                except:
                    blog_levels.append("N/A")
            
            print(f"키워드 '{keyword}' 결과 추출 완료, 구글 시트에 기록 중...")

            # 키워드를 A열에 기록 (A3, A4, ...)
            row = index + 2  # 3번째 행부터 시작
            results_sheet.update(f'A{row}', [[keyword]])

            # 결과를 구글 시트의 B3부터 K3까지 각 블로그 레벨 기록
            results_sheet.update(f'B{row}:K{row}', [blog_levels])
            
            print(f"키워드 '{keyword}' 및 결과 기록 완료")
            
            # 검색 후 5~20초 사이 대기
            sleep_time = random.uniform(5, 20)
            time.sleep(sleep_time)

        print("모든 키워드 검색 및 결과 기록이 완료되었습니다.")

    except TimeoutException as e:
        print(f"요소를 찾는 데 시간이 초과되었습니다: {e}")
    except NoSuchElementException as e:
        print(f"요소를 찾을 수 없습니다: {e}")
    except Exception as e:
        print(f"오류 발생: {e}")
        print("상세 오류 정보:")
        traceback.print_exc()
    finally:
        if driver:
            print("브라우저 종료 중...")
            driver.quit()
        print("프로그램 종료.")

if __name__ == "__main__":
    try:
        login_and_search_keywords()
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        print("상세 오류 정보:")
        traceback.print_exc()
    finally:
        input("프로그램을 종료하려면 엔터 키를 누르세요...")
        print("프로그램이 종료되었습니다.")
