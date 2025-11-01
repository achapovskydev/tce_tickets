#!/usr/bin/env python3
"""
tce_telegram_monitor.py

Мониторит tce.by/search.html по запросам SEARCH_TEXT и SEARCH_TEXT_2
и шлёт сообщение в Telegram, если количество найденных строк не равно 5 или 4.
"""

import os
import stat
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
import platform
import re

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
    handlers=[logging.FileHandler("tce_monitor.log"), logging.StreamHandler()]
)


def check_chrome_chromedriver_versions():
    """Проверяет версии Chrome и (если есть) chromedriver в PATH."""
    try:
        chrome_version = subprocess.check_output(["google-chrome-stable", "--version"]).decode().strip()
        logging.info("Chrome: %s", chrome_version)
    except Exception as e:
        logging.warning("Не удалось получить версию Chrome: %s", e)

    try:
        chromedriver_version = subprocess.check_output(["chromedriver", "--version"]).decode().strip()
        logging.info("Chromedriver (system): %s", chromedriver_version)
    except Exception:
        logging.info("Chromedriver в PATH не найден или недоступен (это нормально при использовании webdriver-manager).")


def make_executable_if_needed(path: str):
    """Если путь указывает на бинарный файл, сделать его исполняемым."""
    try:
        if os.path.exists(path) and not os.path.isdir(path):
            st = os.stat(path)
            # добавляем бит исполнимости для текущего пользователя
            os.chmod(path, st.st_mode | stat.S_IXUSR)
            logging.debug("Установлен бит исполняемости для %s", path)
    except Exception as e:
        logging.warning("Не удалось установить права исполняемости для %s: %s", path, e)


def is_likely_executable_candidate(filename: str) -> bool:
    """
    Определяем, является ли имя файла кандидатом на исполняемый chromedriver.
    Приоритет — точное совпадение 'chromedriver' / 'chromedriver.exe'.
    Также допускаем имена содержащие 'chromedriver' без точечного суффикса (чтобы не захватить файлы-нотиссы).
    """
    name = os.path.basename(filename).lower()
    if name in ("chromedriver", "chromedriver.exe"):
        return True
    # допускаем варианты вроде chromedriver-linux64 (без расширения), но отбрасываем файлы с точкой в конце имени (например THIRD_PARTY_NOTICES.chromedriver)
    if "chromedriver" in name and "." not in name:
        return True
    return False


def resolve_chromedriver_path(driver_path: str) -> str:
    """
    webdriver-manager иногда возвращает путь к директории с бинарями.
    Если это директория — пытаемся найти исполняемый chromedriver внутри неё.
    Возвращаем путь к исполняемому файлу.
    """
    logging.info("Raw webdriver-manager path: %s", driver_path)
    # Если указали прямо файл — убедимся, что это бинарь, и сделаем его исполняемым.
    if os.path.isfile(driver_path):
        make_executable_if_needed(driver_path)
        # проверим, не выглядит ли файл как заметка / txt
        basename = os.path.basename(driver_path).lower()
        if is_likely_executable_candidate(basename) or os.access(driver_path, os.X_OK):
            logging.info("Используется chromedriver бинарь: %s", driver_path)
            return driver_path
        # если файл не исполняемый и не совпадает по имени, попробуем поиск в родительской директории
        driver_dir = os.path.dirname(driver_path)
    else:
        driver_dir = driver_path

    if not os.path.isdir(driver_dir):
        raise FileNotFoundError(f"Ожидалась директория с драйвером, но её нет: {driver_dir}")

    # Ищем кандидатов по имени и по факту исполняемости
    candidates = []
    for root, _, files in os.walk(driver_dir):
        for f in files:
            full = os.path.join(root, f)
            if is_likely_executable_candidate(f):
                candidates.append(full)
    # Если не нашли явных кандидатов по имени — попробуем отобрать по правам/размеру и отсутствию "notice"/"third_party"
    if not candidates:
        for root, _, files in os.walk(driver_dir):
            for f in files:
                lf = f.lower()
                if "notice" in lf or "third_party" in lf or lf.endswith(".txt") or lf.endswith(".md"):
                    continue
                full = os.path.join(root, f)
                # отфильтруем явно маленькие файлы
                try:
                    if os.path.getsize(full) < 2048:
                        continue
                except Exception:
                    continue
                candidates.append(full)

    if not candidates:
        raise FileNotFoundError(f"Не найден исполняемый chromedriver в директории {driver_dir}")

    # Сортируем кандидатов: предпочитаем точное имя chromedriver, затем исполняемые файлы
    def score(path):
        name = os.path.basename(path).lower()
        s = 0
        if name in ("chromedriver", "chromedriver.exe"):
            s += 100
        if os.access(path, os.X_OK):
            s += 50
        # отрицание для файлов с точкой (чтобы отсеять THIRD_PARTY_NOTICES.chromedriver)
        if "." in name and not name.endswith(".exe"):
            s -= 20
        # чуть выше — большие файлы приятнее
        try:
            s += min(20, os.path.getsize(path) // 1024)
        except Exception:
            pass
        return -s  # для сортировки по убыванию

    candidates = sorted(candidates, key=score)

    chosen = candidates[0]
    make_executable_if_needed(chosen)

    logging.info("Выбран chromedriver: %s", chosen)
    return chosen


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

    raw_driver_path = ChromeDriverManager().install()
    driver_binary = resolve_chromedriver_path(raw_driver_path)

    service = ChromeService(executable_path=driver_binary)
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
            wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#playbill tbody tr")))
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
            message_parts.append(
                f"⚠️ <b>Изменение по запросу: {SEARCH_TEXT}</b>\n"
                f"Ожидалось: {EXPECTED_COUNT_1}, найдено: {count1}\n"
            )

        if count2 != EXPECTED_COUNT_2:
            message_parts.append(
                f"⚠️ <b>Изменение по запросу: {SEARCH_TEXT_2}</b>\n"
                f"Ожидалось: {EXPECTED_COUNT_2}, найдено: {count2}\n"
            )

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
