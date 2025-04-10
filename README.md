# AI 기반 블로그 자동화 시스템

## 개요
본 프로젝트는 OpenAI GPT 모델과 Selenium 기반의 자동화 기술을 활용하여, 키워드 분석부터 블로그 원고 생성 및 게시까지 전 과정을 자동화한 시스템입니다. WordPress, Tistory 플랫폼 모두 지원하며, SEO 최적화 요소까지 자동으로 삽입됩니다.

## 주요 기능

- Google Sheet에서 키워드 수집 및 관리
- 블로그 키워드 검색 순위 분석 (BlogStand 기반)
- 관련 블로그 내용 크롤링 (네이버 API 사용)
- GPT-4 모델을 통한 블로그 원고 자동 생성
- 마크다운 변환 및 HTML 스타일 적용
- WordPress / Tistory 자동 로그인 및 포스팅
- Yoast SEO 필드 (focus keyword, meta description) 자동 작성
- 중복 키워드 및 발행 여부 검증

## 기술 스택

- **Python 3.10+**
- **Selenium, pyautogui**: 브라우저 자동화
- **BeautifulSoup, requests**: 웹 크롤링
- **OpenAI GPT-4 API**: 콘텐츠 생성
- **Google Sheets API**: 외부 키워드 연동
- **WordPress REST API**: 게시글 업로드
- **GitHub + Git LFS**: 코드 및 대용량 파일 관리

## 프로그램 별 설명

- python main.py: 티스토리 자동 포스팅
- python publish_wordpress.py: 워드프레스 자동 게시
- python wordpress_seo.py: SEO 필드 자동 수정
- python search_blog.py: 키워드 순위 분석
