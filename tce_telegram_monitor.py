#!/usr/bin/env python3
"""
tce_telegram_monitor.py
Мониторит tce.by/search.html по запросам SEARCH_TEXT и SEARCH_TEXT_2
и шлёт сообщение в Telegram, если найдено мероприятие с датой > заданной.
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SEARCH_TEXT = os.getenv("SEARCH_TEXT", "Записки юного врача")
SEARCH_TEXT_2 = os.getenv("SEARCH_TEXT_2", "На чёрной")
URL = os.getenv("URL", "https://tce.by/search.html")

# Пороги
THRESHOLD = int(os.getenv("THRESHOLD", "1"))
THRESHOLD_2 = int(os.getenv("THRESHOLD_2", "2"))

# Логи
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("tce_monitor.log"),
              logging.StreamHandler()])


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


def parse_date_from_row(row):
    """Парсит дату из первой ячейки строки."""
    date_cell = row.find_element(By.CSS_SELECTOR, "td:first-child")
    date_str = date_cell.text.strip()
    try:
        date = datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
        return date
    except Exception:
        return None


def get_count_with_selenium(search_text: str,
                            date_limit: str) -> tuple[int, bool]:
    """Возвращает (количество найденных, есть ли дата > date_limit)"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,800")
    options.add_argument("--ignore-certificate-errors")
    
    # Автоматическое определение пути к Chrome (для GitHub Actions)
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        logging.info("Используется Chrome из CHROME_BIN: %s", chrome_bin)

    service = ChromeService()
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)

        wait = WebDriverWait(driver, 20)
        input_box = wait.until(
            EC.presence_of_element_located((By.NAME, "tags")))
        input_box.clear()
        input_box.send_keys(search_text)

        reload_btn = driver.find_element(By.ID, "reload")
        reload_btn.click()

        try:
            wait_short = WebDriverWait(driver, 10)
            wait_short.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#playbill tbody tr")))
        except TimeoutException:
            logging.info("[%s] Нет результатов -> 0", search_text)
            return 0, False

        rows = driver.find_elements(By.CSS_SELECTOR, "#playbill tbody tr")
        count = len(rows)
        has_future_date = False
        limit_date = datetime.strptime(date_limit, "%Y-%m-%d").date()

        for row in rows:
            date = parse_date_from_row(row)
            if date and date > limit_date:
                has_future_date = True
                break

        logging.info("[%s] Найдено %d тр., дата > %s: %s", search_text, count,
                     date_limit, has_future_date)
        return count, has_future_date

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
    message_parts = []  ### Соберём несколько блоков текста

    try:
        # Поиск по первому запросу
        count1, has_future_date1 = get_count_with_selenium(
            SEARCH_TEXT, "2025-10-27")
        if has_future_date1:
            message_parts.append(f"⚠️ <b>Найдено {count1} мероприятий</b>\n"
                                 f"По запросу: <i>{SEARCH_TEXT}</i>\n"
                                 f"Есть дата > 2025-11-27\n")

        # Поиск по второму запросу
        count2, has_future_date2 = get_count_with_selenium(
            SEARCH_TEXT_2, "2025-11-13")
        if has_future_date2:
            message_parts.append(f"⚠️ <b>Найдено {count2} мероприятий</b>\n"
                                 f"По запросу: <i>{SEARCH_TEXT_2}</i>\n"
                                 f"Есть дата > 2025-11-13\n")

        # Если хоть что-то найдено — отправляем одно сообщение
        if message_parts:
            final_message = "\n".join(message_parts) + f"\n\n{URL}"
            send_telegram(final_message)
        else:
            logging.info("Ничего нового не найдено по обоим запросам.")

    except Exception as e:
        logging.exception("Ошибка при получении данных: %s", e)
        send_telegram(f"❗ Ошибка мониторинга: {e}")


if __name__ == "__main__":
    main_once()
