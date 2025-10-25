# TCE Telegram Monitor

Автоматический мониторинг событий на сайте tce.by с уведомлениями в Telegram.

## 🚀 Быстрый старт

### Запуск в Replit

Проект уже настроен и готов к работе:
- Откройте веб-интерфейс по адресу: `https://[ваш-проект].repl.co`
- Нажмите кнопку "Запустить мониторинг"

### Автоматический запуск через GitHub Actions

GitHub Actions будет автоматически запускать скрипт **каждые 10 минут**, проверять наличие новых событий и отправлять уведомления в Telegram.

#### Настройка GitHub Secrets

1. Перейдите в ваш репозиторий на GitHub
2. Откройте **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте два секрета:

   **BOT_TOKEN**
   - Value: ваш токен Telegram бота (получите у @BotFather)
   
   **CHAT_ID**
   - Value: ваш Telegram Chat ID (узнайте через @userinfobot)

5. Сохраните секреты

#### Активация автоматического запуска

После добавления секретов:
1. Перейдите во вкладку **Actions** в вашем репозитории
2. Включите GitHub Actions, если они выключены
3. Workflow "Run TCE Monitor Every 10 Minutes" начнет работать автоматически

Вы также можете запустить его вручную:
- Actions → Run TCE Monitor Every 10 Minutes → Run workflow

## 📋 Конфигурация

Настройки мониторинга можно изменить через переменные окружения в Replit Secrets или GitHub Secrets:

- `SEARCH_TEXT` - первый поисковый запрос (по умолчанию: "Записки юного врача")
- `SEARCH_TEXT_2` - второй поисковый запрос (по умолчанию: "На чёрной")
- `URL` - URL для мониторинга (по умолчанию: "https://tce.by/search.html")
- `THRESHOLD` - минимальное количество событий для уведомления (по умолчанию: 1)
- `THRESHOLD_2` - порог для второго запроса (по умолчанию: 2)

## 🔗 API Endpoints

- `GET /` - главная страница с кнопкой запуска
- `GET /run` - запустить скрипт мониторинга
- `GET /test` - отправить тестовое сообщение в Telegram

## 📊 Как это работает

1. **Selenium** открывает сайт tce.by в headless-режиме
2. Ищет события по заданным поисковым запросам
3. Проверяет даты найденных событий
4. Если найдены события с датами позже заданного порога - отправляет уведомление в Telegram
5. Логи сохраняются в файл `tce_monitor.log`

## 🛠 Технологии

- Python 3.11
- Flask - веб-сервер
- Selenium - автоматизация браузера
- Chromium - headless браузер
- Telegram Bot API - уведомления

## 📝 Структура проекта

```
.
├── .github/
│   └── workflows/
│       └── run_script.yml          # GitHub Actions workflow
├── server.py                       # Flask веб-сервер
├── tce_telegram_monitor.py         # Основной скрипт мониторинга
├── test_telegram.py                # Тест Telegram бота
├── debug_search.py                 # Отладочный скрипт
├── requirements.txt                # Python зависимости
└── README.md                       # Этот файл

```

## ⚙️ Локальная разработка

```bash
# Установите зависимости
pip install -r requirements.txt

# Установите Chromium (Ubuntu/Debian)
sudo apt-get install chromium-browser chromium-chromedriver

# Создайте .env файл
BOT_TOKEN=ваш_токен
CHAT_ID=ваш_chat_id

# Запустите сервер
python server.py

# Или запустите скрипт напрямую
python tce_telegram_monitor.py
```

## 🔐 Безопасность

- Никогда не коммитьте файл `.env` с секретами
- Используйте Replit Secrets или GitHub Secrets для хранения токенов
- `.gitignore` настроен для исключения чувствительных данных

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в файле `tce_monitor.log`
2. Убедитесь, что BOT_TOKEN и CHAT_ID правильно настроены
3. Проверьте, что ваш бот добавлен в чат и имеет права на отправку сообщений
