### app/services/depreciation_calc.py
# 減価償却費を外部サイトから Seleniumを使って自動取得

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
# メモリ使用量間使用
from app.monitor import monitor_memory

@monitor_memory("Seleniumによる減価償却費の取得")
def calculate_depreciation_by_year(
    starting_date: str,
    calc_closing_date: str,
    method: str,
    price: float,
    life: int,
    target_year: str,
    current_volume: float = None,
    total_volume: float = None,
    remaining_value: float = None
) -> float | None:
    """
    指定された条件に基づいて、Selenium経由で減価償却費を自動取得する。
    Returns:
        指定年度の減価償却費（float）または None（取得失敗時）
    """
    driver = None  # finallyでquitするために外で定義

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.binary_location = "/usr/bin/google-chrome"

        service = Service(executable_path="/usr/local/bin/chromedriver")

        print("🌟 Selenium 起動前")
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Selenium 起動成功")

        try:
            driver.get("https://stylefunc287.xsrv.jp/php/dep.php")
            
                
            # 入力フォームの要素取得と入力
            starting_input = driver.find_element(By.ID, "startingDate")
            closing_input = driver.find_element(By.ID, "closingDate")
            driver.execute_script("arguments[0].value = arguments[1]", starting_input, starting_date) # JavaScript を使って値を直接設定する。　フォーマット依存を避ける。　今回アクセスするwebページの日付入力欄のフォーマットは自動入力だと誤入力を起こしてしまう。
            driver.execute_script("arguments[0].value = arguments[1]", closing_input, calc_closing_date)
            # 略式の記述方法 # 入力
            # driver.execute_script("arguments[0].value = arguments[1]", driver.find_element(By.ID, "startingDate"), starting_date)
            # driver.execute_script("arguments[0].value = arguments[1]", driver.find_element(By.ID, "closingDate"), calc_closing_date)

            Select(driver.find_element(By.ID, "cluculateMethod")).select_by_visible_text(method)
            driver.find_element(By.ID, "purchasePrice").send_keys(str(price))
            driver.find_element(By.ID, "usefulLife").send_keys(str(life))

            if method == "生産高比例法":
                driver.find_element(By.ID, "currentVolume").send_keys(str(current_volume or ""))
                driver.find_element(By.ID, "totalVolume").send_keys(str(total_volume or ""))
                driver.find_element(By.ID, "remaining_value").send_keys(str(remaining_value or ""))

            driver.find_element(By.ID, "submit").click()
            time.sleep(2)

            rows = driver.find_elements(By.CSS_SELECTOR, "tbody.record tr")
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 3 and cols[0].text.strip() == target_year:
                    value = cols[2].text.replace(",", "")
                    print(f"✅ 減価償却費取得成功: {value}")
                    return float(value)

            print(f"⚠️ 指定年 {target_year} の減価償却費が見つかりませんでした。")
            return None

        except Exception as e_inner:
            print(f"⚠️ Seleniumページ処理中のエラー: {e_inner}")
            return None

    except Exception as e_outer:
        print(f"❌ Selenium起動エラー: {e_outer}")
        return None

    finally:
        if driver:
            driver.quit()
            print("🛑 Selenium セッション終了")
