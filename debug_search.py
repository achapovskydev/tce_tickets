#!/usr/bin/env python3
"""
Отладочный скрипт - показывает что находит на сайте
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

load_dotenv()
SEARCH_TEXT = os.getenv("SEARCH_TEXT", "Записки юного врача")
URL = os.getenv("URL", "https://tce.by/search.html")

def check_site():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = ChromeService()
    driver = None
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)
        
        wait = WebDriverWait(driver, 20)
        input_box = wait.until(EC.presence_of_element_located((By.NAME, "tags")))
        input_box.clear()
        input_box.send_keys(SEARCH_TEXT)
        
        reload_btn = driver.find_element(By.ID, "reload")
        reload_btn.click()
        
        try:
            wait_short = WebDriverWait(driver, 10)
            wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#playbill tbody tr")))
        except TimeoutException:
            print(f"❌ Нет результатов для '{SEARCH_TEXT}'")
            return
        
        rows = driver.find_elements(By.CSS_SELECTOR, "#playbill tbody tr")
        print(f"✅ Найдено {len(rows)} событий для '{SEARCH_TEXT}':")
        print("=" * 60)
        
        for i, row in enumerate(rows[:10], 1):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    date = cells[0].text.strip()
                    title = cells[1].text.strip()[:50]
                    print(f"{i}. {date} | {title}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    check_site()
