@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" goto setup_env

:run_bot
python bot.py
if errorlevel 1 goto bot_error
goto end

:setup_env
echo First-time setup
echo.
set /p "BOT_TOKEN=Paste the Telegram bot token and press Enter: "
if not defined BOT_TOKEN goto empty_token
> ".env" echo TELEGRAM_BOT_TOKEN=%BOT_TOKEN%
set "BOT_TOKEN="
echo.
echo The .env file was created. Starting the bot...
echo.
goto run_bot

:empty_token
echo.
echo No token was entered. Run start_bot.bat again.
pause
exit /b 1

:bot_error
echo.
echo The bot stopped with an error. Read the error message above.
pause
exit /b 1

:end
endlocal
