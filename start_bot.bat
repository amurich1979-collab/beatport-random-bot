@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".env" (
    echo Файл .env не найден.
    echo.
    echo 1. Скопируйте .env.example и назовите копию .env
    echo 2. Откройте .env и вставьте новый токен Telegram после знака =
    echo 3. Запустите start_bot.bat снова
    echo.
    pause
    exit /b 1
)

python bot.py
if errorlevel 1 (
    echo.
    echo Бот завершился с ошибкой. Текст ошибки находится выше.
    pause
)
