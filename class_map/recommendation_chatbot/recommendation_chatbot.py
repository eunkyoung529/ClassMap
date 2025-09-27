from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os

# STEP 1. 크롬 옵션 설정
options = Options()
# options.add_argument('--headless')  # 브라우저 창을 띄우지 않으려면 주석 해제
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# STEP 2. 크롬 드라이버 자동 설치
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# STEP 3. 사이트 접속 (공모전)
url = "https://www.campuspick.com/contest"  # 공모전 페이지
driver.get(url)
time.sleep(3)

SCROLL_PAUSE = 2
last_height = driver.execute_script("return document.body.scrollHeight")

# STEP 4. 무한 스크롤
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("더 이상 로딩할 공모전 없음, 스크롤 종료")
        break
    last_height = new_height

# STEP 5. 공모전 카드 정보 추출
cards = driver.find_elements(By.CSS_SELECTOR, "div.item")
data = []

for idx, card in enumerate(cards):
    if idx >= 200:  # 200개까지만 수집
        print("200개 수집 완료, 종료!")
        break
    try:
        title = card.find_element(By.CSS_SELECTOR, "h2").text.strip()
        org = card.find_element(By.CSS_SELECTOR, "p.company").text.strip()
        deadline = card.find_element(By.CSS_SELECTOR, "span.dday").text.strip()

        category_tags = card.find_elements(By.CSS_SELECTOR, "p.badges span")
        categories = ", ".join([cat.text.strip() for cat in category_tags])
        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

        # 상세 페이지로 이동
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)
        time.sleep(3)

        # 상세 페이지 스크롤 다운
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 본문 내용 추출
        try:
            content = driver.find_element(By.CSS_SELECTOR, "#container article.description").text.strip()
        except Exception as e:
            print("내용 추출 실패:", e)
            content = "내용 없음"

        # 상세 페이지 닫기 후 원래 탭으로 돌아오기
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # 데이터 저장
        data.append({
            "제목": title,
            "주최": org,
            "마감일": deadline,
            "분야": categories,
            "링크": link,
            "내용": content
        })

        print(f"{idx + 1}번째 공모전 수집 완료: {title}")

    except Exception as e:
        print("카드 처리 중 에러 발생:", e)
        continue

# STEP 6. 드라이버 종료
driver.quit()

# STEP 7. CSV 파일로 저장
df = pd.DataFrame(data)
save_path = os.path.join(os.getcwd(), "공모전_200개.csv")
df.to_csv(save_path, index=False, encoding="utf-8-sig")

print(f"공모전 전체 정보 저장 완료! → {save_path}")
