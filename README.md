# Beatport Random Bot

Telegram-бот формирует ссылку на каталог треков Beatport за случайный день.
Пользователь может оставить случайный жанр или выбрать один из 32 жанров.

## Почему бот не парсит Beatport

Старые прототипы пытались извлекать ссылки на релизы из HTML. Сейчас Beatport
защищает сайт Cloudflare и отвечает таким скриптам кодом `403`. Официальный API
доступен только одобренным клиентам с API-ключом. Поэтому эта версия формирует
прямую ссылку на страницу каталога и не обходит защиту сайта.

## Запуск

Требуется Python 3.11+ и новый токен Telegram-бота.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:TELEGRAM_BOT_TOKEN="новый-токен-из-BotFather"
python bot.py
```

Команды:

- `/start` — открыть меню и сбросить выбранный жанр;
- `/help` — показать краткую справку.

## Проверки

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Безопасность

Токен хранится только в переменной `TELEGRAM_BOT_TOKEN`. Не добавляйте `.env`
или токен в Git. Токены, когда-либо сохранённые в старых файлах, необходимо
отозвать через BotFather, даже если позже они были удалены из кода.
