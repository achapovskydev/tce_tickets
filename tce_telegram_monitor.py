#!/usr/bin/env python3
"""
tce_telegram_monitor.py
Мониторит tce.by/search.html по запросам SEARCH_TEXT и SEARCH_TEXT_2
и шлёт сообщение в Telegram, если количество найденных строк не равно 5 или 4.
"""
import os
import logging
import subprocess
from dotenv import load_dotenv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SEARCH_TEXT = os.getenv("SEARCH_TEXT", "Записки юного врача")
SEARCH_TEXT_2 = os.getenv("SEARCH_TEXT_2", "На чёрной")
URL = os.getenv("URL", "https://tce.by/search.html")

# Ожидаемое количество строк
EXPECTED_COUNT_1 = 5
EXPECTED_COUNT_2 = 4

# Логи
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("tce_monitor.log"), logging.StreamHandler()])

def check_chrome_chromedriver_versions():
    """Проверяет версии Chrome и ChromeDriver."""
    try:
        chrome_version = subprocess.check_output(["google-chrome-stable", "--version"]).decode().strip()
        chromedriver_version = subprocess.check_output(["chromedriver", "--version"]).decode().strip()
        logging.info(f"Chrome: {chrome_version}, ChromeDriver: {chromedriver_version}")
    except Exception as e:
        logging.warning(f"Не удалось проверить версии: {e}")

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        logging.info("Сообщение отправлено в Telegram.")
        return True
    except Exception as e:
        logging.exception("Ошибка отправки в Telegram: %s", e)
        return False

def get_count_with_selenium(search_text: str) -> int:
    """Возвращает количество найденных строк."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,800")
    options.add_argument("--ignore-certificate-errors")

    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        logging.info("Используется Chrome из CHROME_BIN: %s", chrome_bin)

    # Устанавливаем ChromeDriver через webdriver-manager
    driver_path = ChromeDriverManager().install()
    service = ChromeService(executable_path=driver_path)
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)
        wait = WebDriverWait(driver, 20)
        input_box = wait.until(EC.presence_of_element_located((By.NAME, "tags")))
        input_box.clear()
        input_box.send_keys(search_text)
        reload_btn = driver.find_element(By.ID, "reload")
        reload_btn.click()
        try:
            wait_short = WebDriverWait(driver, 10)
            wait_short.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#playbill tbody tr")))
        except TimeoutException:
            logging.info("[%s] Нет результатов -> 0", search_text)
            return 0
        rows = driver.find_elements(By.CSS_SELECTOR, "#playbill tbody tr")
        count = len(rows)
        logging.info("[%s] Найдено %d строк", search_text, count)
        return count
    except WebDriverException as e:
        logging.exception("WebDriver ошибка: %s", e)
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def main_once():
    check_chrome_chromedriver_versions()
    message_parts = []
    try:
        count1 = get_count_with_selenium(SEARCH_TEXT)
        count2 = get_count_with_selenium(SEARCH_TEXT_2)

        if count1 != EXPECTED_COUNT_1:
            message_parts.append(f"⚠️ <b>Изменение по запросу: {SEARCH_TEXT}</b>\n"
                                 f"Ожидалось: {EXPECTED_COUNT_1}, найдено: {count1}\n")
        if count2 != EXPECTED_COUNT_2:
            message_parts.append(f"⚠️ <b>Изменение по запросу: {SEARCH_TEXT_2}</b>\n"
                                 f"Ожидалось: {EXPECTED_COUNT_2}, найдено: {count2}\n")

        if message_parts:
            final_message = "\n".join(message_parts) + f"\n\n{URL}"
            send_telegram(final_message)
        else:
            logging.info("Количество строк соответствует ожидаемому.")
    except Exception as e:
        logging.exception("Ошибка при получении данных: %s", e)
        send_telegram(f"❗ Ошибка мониторинга: {e}")

if __name__ == "__main__":
    main_once()
