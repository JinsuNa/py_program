import os
import openai
import requests
from bs4 import BeautifulSoup
import urllib3

# SSL 경고 메시지를 무시하는 설정
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    프롬프트 입력
    """
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
 프롬프트 입력
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
        "max_tokens": 3200,
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
    
    글의 요점을 잘 반영한 40자 이하의 짧고 임팩트 있는 제목으로 작성해 주세요.
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


# 메인 실행 함수
def main():
    # API 키 및 설정 파일 로드
    config_file = "config_naver_api.txt"
    api_keys = load_api_keys(config_file)

    client_id = api_keys["client_id"]
    client_secret = api_keys["client_secret"]
    openai_api_key = api_keys["openai_api"]

    # 키워드 파일에서 키워드 읽기
    keyword_file = "config_keyword.txt"
    keywords = load_keywords(keyword_file)

    for keyword in keywords:
        print(f"{keyword}에 대한 작업을 시작합니다.")

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

        # 원고 파일로 저장 (기존 텍스트 지우고 새로 작성)
        output_file = f"C:/main_tstroy/{keyword}_text.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(article)

        # 마크다운 형식으로 변환
        request_markdown_conversion(openai_api_key, article, keyword)

        # 제목 생성 및 저장
        request_title_generation(openai_api_key, keyword)

        print(
            f"'{keyword}' 작업이 완료되었습니다. 다음 키워드로 넘어가려면 Enter를 누르세요..."
        )
        input()


if __name__ == "__main__":
    main()
