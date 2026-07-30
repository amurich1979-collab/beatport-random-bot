@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" goto missing_env

python bot.py
if errorlevel 1 goto bot_error
goto end

:missing_env
echo The .env file was not found.
echo.
echo 1. Copy .env.example and rename the copy to .env
echo 2. Open .env and paste the Telegram token after the equals sign
echo 3. Run start_bot.bat again
echo.
pause
exit /b 1

:bot_error
echo.
echo The bot stopped with an error. Read the error message above.
pause
exit /b 1

:end
endlocal
