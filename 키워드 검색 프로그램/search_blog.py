import requests
from bs4 import BeautifulSoup
import openai



# 네이버 블로그 검색 API로 상위 5개의 URL을 추출하는 함수
def get_blog_posts(keyword):
    url = f"https://openapi.naver.com/v1/search/blog.json?query={keyword}&display=5&sort=sim"

    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        urls = [item["link"] for item in data["items"]]
        return urls
    else:
        print(f"Error: {response.status_code}")
        return []


# URL에서 블로그 게시물의 본문을 추출하는 함수
def extract_blog_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # 1. 첫 번째 시도: 주로 사용되는 네이버 블로그 본문 컨테이너
    content = soup.find("div", class_="se-main-container")

    # 2. 두 번째 시도: 다른 블로그 템플릿에서 사용하는 본문 구조
    if not content:
        content = soup.find("div", class_="se_component_wrap sect_dsc")

    # 3. 세 번째 시도: 만약 iframe 내부에 블로그 본문이 있을 경우
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
        return content.get_text(strip=True)
    return "내용을 찾을 수 없습니다."


# GPT-4를 사용하여 블로그 게시글을 생성하는 함수
def generate_blog_post(urls_contents, keyword):
    # 프롬프트 구성
    prompt = f"""
    프롬프트 입력
    """

    # URL에서 추출한 본문을 프롬프트에 추가
    for i, (url, content) in enumerate(urls_contents, start=1):
        prompt += f"\n\nURL {i}: {url}\n내용 {i}: {content[:1000]}\n"

    # GPT-4 API 호출
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # GPT-4 모델 사용
        messages=[
            {"role": "system", "content": "You are a professional legal writer."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3000,  # 출력되는 글의 길이에 맞게 토큰 수 조정
    )

    return response.choices[0].message["content"].strip()


# 메인 함수
def main():
    # 검색할 키워드 설정
    keyword = "친양자입양서류"

    # 1. 블로그 검색 API로 상위 5개의 URL 추출
    urls = get_blog_posts(keyword)

    if not urls:
        print("블로그 URL을 가져오지 못했습니다.")
        return

    # 2. 각 URL에서 본문을 추출하여 저장
    contents = []
    for url in urls:
        content = extract_blog_content(url)
        contents.append((url, content[:3000]))  # 본문이 길 경우 500자만 사용

    # 3. GPT-4를 통해 대조 분석 후 새로운 블로그 게시글 작성
    new_blog_post = generate_blog_post(contents, keyword)

    # 4. 결과 출력
    print("Generated Blog Post (in Korean):")
    print(new_blog_post)


# 이 파일이 직접 실행될 때만 main 함수 호출
if __name__ == "__main__":
    main()
