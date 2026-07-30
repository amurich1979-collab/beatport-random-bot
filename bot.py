"""Telegram bot that opens a random dated Beatport catalog page."""

from __future__ import annotations

import logging
import os
import random
from datetime import date, timedelta
from urllib.parse import urlencode

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

LOGGER = logging.getLogger(__name__)

GENRES: dict[str, tuple[str, int]] = {
    "afro-house": ("Afro House", 89),
    "amapiano": ("Amapiano", 98),
    "bass-club": ("Bass / Club", 85),
    "bass-house": ("Bass House", 91),
    "breaks-breakbeat-uk-bass": ("Breaks / Breakbeat / UK Bass", 9),
    "dance-pop": ("Dance / Pop", 39),
    "deep-house": ("Deep House", 12),
    "dj-tools": ("DJ Tools", 16),
    "drum-bass": ("Drum & Bass", 1),
    "dubstep": ("Dubstep", 18),
    "electro-classic-detroit-modern": ("Electro", 94),
    "electronica": ("Electronica", 3),
    "funky-house": ("Funky House", 81),
    "hard-dance-hardcore-neo-rave": ("Hard Dance / Hardcore", 8),
    "hard-techno": ("Hard Techno", 2),
    "house": ("House", 5),
    "indie-dance": ("Indie Dance", 37),
    "jackin-house": ("Jackin House", 97),
    "mainstage": ("Mainstage", 96),
    "melodic-house-techno": ("Melodic House & Techno", 90),
    "minimal-deep-tech": ("Minimal / Deep Tech", 14),
    "nu-disco-disco": ("Nu Disco / Disco", 50),
    "organic-house-downtempo": ("Organic House / Downtempo", 93),
    "progressive-house": ("Progressive House", 15),
    "psy-trance": ("Psy-Trance", 13),
    "tech-house": ("Tech House", 11),
    "techno-peak-time-driving": ("Techno (Peak Time / Driving)", 6),
    "techno-raw-deep-hypnotic": ("Techno (Raw / Deep / Hypnotic)", 92),
    "trance-main-floor": ("Trance (Main Floor)", 7),
    "trance-raw-deep-hypnotic": ("Trance (Raw / Deep / Hypnotic)", 99),
    "trap-future-bass": ("Trap / Future Bass", 38),
    "uk-garage-bassline": ("UK Garage / Bassline", 86),
}

MIN_DATE = date(2004, 1, 1)


def random_catalog_url(
    genre_slug: str | None = None,
    *,
    today: date | None = None,
    rng: random.Random | None = None,
) -> tuple[str, str, date]:
    """Build a valid Beatport catalog URL for one random date."""
    generator = rng or random
    current_date = today or date.today()
    if current_date < MIN_DATE:
        raise ValueError("today must not be earlier than Beatport's catalog")

    slug = genre_slug or generator.choice(tuple(GENRES))
    if slug not in GENRES:
        raise ValueError(f"Unknown genre: {slug}")

    title, genre_id = GENRES[slug]
    day = MIN_DATE + timedelta(
        days=generator.randint(0, (current_date - MIN_DATE).days)
    )
    query = urlencode(
        {
            "publish_date": f"{day:%Y-%m-%d}:{day:%Y-%m-%d}",
            "page": 1,
            "per_page": 100,
        }
    )
    return (
        f"https://www.beatport.com/genre/{slug}/{genre_id}/tracks?{query}",
        title,
        day,
    )


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎲 Случайный день", callback_data="random_day")],
            [InlineKeyboardButton("🎛 Выбрать жанр", callback_data="genres:0")],
            [InlineKeyboardButton("♻️ Сбросить жанр", callback_data="reset")],
        ]
    )


def genre_menu(page: int) -> InlineKeyboardMarkup:
    page_size = 8
    items = list(GENRES.items())
    page_count = (len(items) + page_size - 1) // page_size
    page = max(0, min(page, page_count - 1))
    rows = [
        [InlineKeyboardButton(title, callback_data=f"genre:{slug}")]
        for slug, (title, _) in items[page * page_size : (page + 1) * page_size]
    ]
    navigation: list[InlineKeyboardButton] = []
    if page:
        navigation.append(InlineKeyboardButton("←", callback_data=f"genres:{page - 1}"))
    navigation.append(
        InlineKeyboardButton(f"{page + 1}/{page_count}", callback_data="noop")
    )
    if page + 1 < page_count:
        navigation.append(InlineKeyboardButton("→", callback_data=f"genres:{page + 1}"))
    rows.extend([navigation, [InlineKeyboardButton("В меню", callback_data="menu")]])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("genre", None)
    if update.message:
        await update.message.reply_text(
            "Я открываю страницу треков Beatport за случайный день. "
            "Можно искать по всему каталогу или сначала выбрать жанр.",
            reply_markup=main_menu(),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Выберите жанр (необязательно), затем нажмите «Случайный день». "
            "Бот формирует ссылку, а список релизов показывает сам Beatport."
        )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    if data == "noop":
        return
    if data == "menu":
        await query.edit_message_text("Выберите действие:", reply_markup=main_menu())
        return
    if data == "reset":
        context.user_data.pop("genre", None)
        await query.edit_message_text("Жанр сброшен.", reply_markup=main_menu())
        return
    if data.startswith("genres:"):
        page = int(data.partition(":")[2])
        await query.edit_message_text("Выберите жанр:", reply_markup=genre_menu(page))
        return
    if data.startswith("genre:"):
        slug = data.partition(":")[2]
        if slug not in GENRES:
            await query.edit_message_text("Неизвестный жанр.", reply_markup=main_menu())
            return
        context.user_data["genre"] = slug
        await query.edit_message_text(
            f"Выбран жанр: {GENRES[slug][0]}",
            reply_markup=main_menu(),
        )
        return
    if data == "random_day":
        url, title, selected_date = random_catalog_url(context.user_data.get("genre"))
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Открыть Beatport", url=url)],
                [InlineKeyboardButton("🎲 Ещё день", callback_data="random_day")],
                [InlineKeyboardButton("В меню", callback_data="menu")],
            ]
        )
        await query.edit_message_text(
            f"Жанр: {title}\nДата: {selected_date:%d.%m.%Y}\n\n"
            "Beatport может показать пустую страницу, если в этот день релизов не было.",
            reply_markup=keyboard,
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Unhandled Telegram update", exc_info=context.error)


def build_application(token: str) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(on_button))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN before starting the bot")
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    build_application(token).run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
