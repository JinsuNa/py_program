import subprocess
import sys

# 설치가 필요한 패키지 리스트 (내장 모듈은 제외)
packages = [
    "chromedriver-autoinstaller",
    "pyperclip",
    "pyautogui",
    "requests",
    "urllib3",
    "beautifulsoup4",
    "selenium",
]


# 패키지 설치 함수
def install_packages():
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


if __name__ == "__main__":
    install_packages()
    print("모든 패키지가 성공적으로 설치되었습니다!")
