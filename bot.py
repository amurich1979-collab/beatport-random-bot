"""Telegram bot for randomized Beatport catalog discovery."""

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
    MessageHandler,
    filters,
)

from catalog import GENRES, search_subgenres

LOGGER = logging.getLogger(__name__)
MIN_DATE = date(2004, 1, 1)
GENRE_SLUGS = tuple(GENRES)
PAGE_SIZE = 8


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Используйте дату в формате ГГГГ-ММ-ДД") from error


def validate_range(start: date, end: date, *, today: date | None = None) -> None:
    current = today or date.today()
    if start < MIN_DATE:
        raise ValueError("Начальная дата не может быть раньше 2004-01-01")
    if start > end:
        raise ValueError("Начальная дата должна быть раньше конечной")
    if end > current:
        raise ValueError("Конечная дата не может быть в будущем")


def effective_range(user_data: dict, *, today: date | None = None) -> tuple[date, date]:
    current = today or date.today()
    return user_data.get("date_start", MIN_DATE), user_data.get("date_end", current)


def selected_genres(user_data: dict) -> set[str]:
    return set(user_data.get("genres", ()))


def random_catalog_url(
    genres: set[str] | None = None,
    *,
    start: date = MIN_DATE,
    end: date | None = None,
    subgenre_id: int | None = None,
    rng: random.Random | None = None,
) -> tuple[str, str, date]:
    generator = rng or random
    final_date = end or date.today()
    validate_range(start, final_date, today=max(date.today(), final_date))
    choices = tuple(genres or GENRE_SLUGS)
    if not choices or any(slug not in GENRES for slug in choices):
        raise ValueError("Неизвестный или пустой список жанров")
    slug = generator.choice(choices)
    genre = GENRES[slug]
    day = start + timedelta(days=generator.randint(0, (final_date - start).days))
    query: dict[str, str | int] = {
        "publish_date": f"{day:%Y-%m-%d}:{day:%Y-%m-%d}",
        "page": 1,
        "per_page": 100,
    }
    if subgenre_id is not None:
        query["sub_genre_id"] = subgenre_id
    return (
        f"https://www.beatport.com/genre/{slug}/{genre.id}/tracks?{urlencode(query)}",
        genre.title,
        day,
    )


def filter_summary(user_data: dict) -> str:
    genres = selected_genres(user_data)
    genre_text = (
        "все жанры"
        if not genres
        else ", ".join(GENRES[slug].title for slug in sorted(genres))
    )
    start, end = effective_range(user_data)
    subgenre = user_data.get("subgenre")
    sub_text = f"\nПоджанр: {subgenre['title']}" if subgenre else ""
    return f"Жанры: {genre_text}\nДаты: {start:%d.%m.%Y} — {end:%d.%m.%Y}{sub_text}"


def main_menu(user_data: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎲 Случайный день", callback_data="random")],
            [
                InlineKeyboardButton(
                    "🎛 Жанры (можно несколько)", callback_data="genres:0"
                )
            ],
            [InlineKeyboardButton("🔎 Поджанр", callback_data="subgenres")],
            [InlineKeyboardButton("📅 Даты и год", callback_data="dates-menu")],
            [InlineKeyboardButton("♻️ Сбросить фильтры", callback_data="reset")],
        ]
    )


def genre_menu(user_data: dict, page: int) -> InlineKeyboardMarkup:
    selected = selected_genres(user_data)
    page_count = (len(GENRE_SLUGS) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, page_count - 1))
    rows = []
    for index in range(page * PAGE_SIZE, min((page + 1) * PAGE_SIZE, len(GENRE_SLUGS))):
        slug = GENRE_SLUGS[index]
        marker = "✅" if slug in selected else "▫️"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{marker} {GENRES[slug].title}", callback_data=f"g:{index}:{page}"
                )
            ]
        )
    navigation = []
    if page:
        navigation.append(InlineKeyboardButton("←", callback_data=f"genres:{page - 1}"))
    navigation.append(
        InlineKeyboardButton(f"{page + 1}/{page_count}", callback_data="noop")
    )
    if page + 1 < page_count:
        navigation.append(InlineKeyboardButton("→", callback_data=f"genres:{page + 1}"))
    rows.extend(
        [
            navigation,
            [
                InlineKeyboardButton(
                    "Очистить жанры", callback_data=f"genres-clear:{page}"
                )
            ],
            [InlineKeyboardButton("Готово", callback_data="menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def year_menu() -> InlineKeyboardMarkup:
    current = date.today().year
    years = list(range(current, max(2003, current - 11), -1))
    rows = [
        [
            InlineKeyboardButton(str(year), callback_data=f"year:{year}")
            for year in years[i : i + 3]
        ]
        for i in range(0, len(years), 3)
    ]
    rows.extend(
        [
            [InlineKeyboardButton("Весь каталог", callback_data="year:all")],
            [InlineKeyboardButton("В меню", callback_data="menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def date_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("30 дней", callback_data="period:30"),
                InlineKeyboardButton("90 дней", callback_data="period:90"),
            ],
            [
                InlineKeyboardButton("365 дней", callback_data="period:365"),
                InlineKeyboardButton("Выбрать год", callback_data="years"),
            ],
            [InlineKeyboardButton("Свой диапазон", callback_data="dates-custom")],
            [InlineKeyboardButton("Весь каталог", callback_data="period:all")],
            [InlineKeyboardButton("В меню", callback_data="menu")],
        ]
    )


def subgenre_menu(slug: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                item.title,
                callback_data=f"s:{GENRE_SLUGS.index(slug)}:{item.id}",
            )
        ]
        for item in GENRES[slug].subgenres
    ]
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    "🔎 Поиск по названию", callback_data="subgenre-search"
                )
            ],
            [InlineKeyboardButton("Убрать поджанр", callback_data="subgenre-clear")],
            [InlineKeyboardButton("В меню", callback_data="menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def subgenre_genre_menu(page: int) -> InlineKeyboardMarkup:
    available = [slug for slug in GENRE_SLUGS if GENRES[slug].subgenres]
    page_count = (len(available) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, page_count - 1))
    rows = [
        [
            InlineKeyboardButton(
                GENRES[slug].title,
                callback_data=f"sg:{GENRE_SLUGS.index(slug)}",
            )
        ]
        for slug in available[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    ]
    navigation = []
    if page:
        navigation.append(
            InlineKeyboardButton("←", callback_data=f"sg-genres:{page - 1}")
        )
    navigation.append(
        InlineKeyboardButton(f"{page + 1}/{page_count}", callback_data="noop")
    )
    if page + 1 < page_count:
        navigation.append(
            InlineKeyboardButton("→", callback_data=f"sg-genres:{page + 1}")
        )
    rows.extend(
        [
            navigation,
            [
                InlineKeyboardButton(
                    "🔎 Поиск по названию", callback_data="subgenre-search"
                )
            ],
            [InlineKeyboardButton("В меню", callback_data="menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def subgenre_results_menu(query: str) -> tuple[str, InlineKeyboardMarkup] | None:
    matches = search_subgenres(query)
    if not matches:
        return None
    rows = [
        [
            InlineKeyboardButton(
                f"{subgenre.title} — {GENRES[slug].title}",
                callback_data=f"s:{GENRE_SLUGS.index(slug)}:{subgenre.id}",
            )
        ]
        for slug, subgenre in matches[:20]
    ]
    rows.extend(
        [
            [InlineKeyboardButton("Искать ещё", callback_data="subgenre-search")],
            [InlineKeyboardButton("В меню", callback_data="menu")],
        ]
    )
    suffix = "\nПоказаны первые 20." if len(matches) > 20 else ""
    return f"Найдено: {len(matches)}{suffix}", InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Beatport Random Bot\n\n" + filter_summary(context.user_data),
            reply_markup=main_menu(context.user_data),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Команды:\n"
            "/year 2024 — ограничить поиск одним годом\n"
            "/dates 2024-01-01 2024-03-31 — диапазон дат\n"
            "/dates reset — сбросить диапазон\n"
            "/subgenre latin — найти и выбрать поджанр\n\n"
            "Если выбрано несколько жанров, при каждом нажатии бот случайно выбирает один из них."
        )


async def year_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Пример: /year 2024")
        return
    year = int(context.args[0])
    current = date.today()
    start = date(year, 1, 1)
    end = min(date(year, 12, 31), current)
    try:
        validate_range(start, end)
    except ValueError as error:
        await update.message.reply_text(str(error))
        return
    context.user_data.update(date_start=start, date_end=end)
    await update.message.reply_text(
        filter_summary(context.user_data), reply_markup=main_menu(context.user_data)
    )


async def dates_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if context.args == ["reset"]:
        context.user_data.pop("date_start", None)
        context.user_data.pop("date_end", None)
    elif len(context.args) == 2:
        try:
            start, end = map(parse_iso_date, context.args)
            validate_range(start, end)
        except ValueError as error:
            await update.message.reply_text(str(error))
            return
        context.user_data.update(date_start=start, date_end=end)
    else:
        await update.message.reply_text("Пример: /dates 2024-01-01 2024-03-31")
        return
    await update.message.reply_text(
        filter_summary(context.user_data), reply_markup=main_menu(context.user_data)
    )


async def subgenre_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Пример: /subgenre latin")
        return
    result = subgenre_results_menu(query)
    if not result:
        await update.message.reply_text("Поджанры не найдены.")
        return
    text, markup = result
    await update.message.reply_text(text, reply_markup=markup)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    pending = context.user_data.pop("pending_input", None)
    text = update.message.text.strip()
    cancel_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Отмена", callback_data="cancel-input")]]
    )
    if pending == "dates":
        parts = text.split()
        if len(parts) != 2:
            context.user_data["pending_input"] = "dates"
            await update.message.reply_text(
                "Нужно две даты через пробел, например:\n2024-01-01 2024-03-31",
                reply_markup=cancel_markup,
            )
            return
        try:
            start_date, end_date = map(parse_iso_date, parts)
            validate_range(start_date, end_date)
        except ValueError as error:
            context.user_data["pending_input"] = "dates"
            await update.message.reply_text(str(error), reply_markup=cancel_markup)
            return
        context.user_data.update(date_start=start_date, date_end=end_date)
        await update.message.reply_text(
            "Диапазон сохранён.\n\n" + filter_summary(context.user_data),
            reply_markup=main_menu(context.user_data),
        )
    elif pending == "subgenre":
        result = subgenre_results_menu(text)
        if not result:
            context.user_data["pending_input"] = "subgenre"
            await update.message.reply_text(
                "Ничего не найдено. Попробуйте другое название.",
                reply_markup=cancel_markup,
            )
            return
        result_text, markup = result
        await update.message.reply_text(result_text, reply_markup=markup)
    else:
        await update.message.reply_text(
            "Все основные действия доступны кнопками:",
            reply_markup=main_menu(context.user_data),
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
        context.user_data.pop("pending_input", None)
        await query.edit_message_text(
            filter_summary(context.user_data), reply_markup=main_menu(context.user_data)
        )
    elif data == "cancel-input":
        context.user_data.pop("pending_input", None)
        await query.edit_message_text(
            "Ввод отменён.\n\n" + filter_summary(context.user_data),
            reply_markup=main_menu(context.user_data),
        )
    elif data == "reset":
        context.user_data.clear()
        await query.edit_message_text(
            "Фильтры сброшены.\n\n" + filter_summary(context.user_data),
            reply_markup=main_menu(context.user_data),
        )
    elif data.startswith("genres:"):
        await query.edit_message_text(
            "Отметьте один или несколько жанров:",
            reply_markup=genre_menu(context.user_data, int(data.split(":")[1])),
        )
    elif data.startswith("genres-clear:"):
        page = int(data.split(":")[1])
        context.user_data.pop("genres", None)
        context.user_data.pop("subgenre", None)
        await query.edit_message_reply_markup(
            reply_markup=genre_menu(context.user_data, page)
        )
    elif data.startswith("g:"):
        _, index_text, page_text = data.split(":")
        slug = GENRE_SLUGS[int(index_text)]
        selected = selected_genres(context.user_data)
        selected.symmetric_difference_update({slug})
        context.user_data["genres"] = sorted(selected)
        context.user_data.pop("subgenre", None)
        await query.edit_message_reply_markup(
            reply_markup=genre_menu(context.user_data, int(page_text))
        )
    elif data == "dates-menu":
        await query.edit_message_text("Выберите период:", reply_markup=date_menu())
    elif data == "dates-custom":
        context.user_data["pending_input"] = "dates"
        await query.edit_message_text(
            "Отправьте две даты одним сообщением:\n2024-01-01 2024-03-31",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Отмена", callback_data="cancel-input")]]
            ),
        )
    elif data.startswith("period:"):
        value = data.split(":")[1]
        if value == "all":
            context.user_data.pop("date_start", None)
            context.user_data.pop("date_end", None)
        else:
            end_date = date.today()
            context.user_data["date_end"] = end_date
            context.user_data["date_start"] = max(
                MIN_DATE, end_date - timedelta(days=int(value) - 1)
            )
        await query.edit_message_text(
            filter_summary(context.user_data), reply_markup=main_menu(context.user_data)
        )
    elif data == "years":
        await query.edit_message_text("Выберите год:", reply_markup=year_menu())
    elif data.startswith("year:"):
        value = data.split(":")[1]
        if value == "all":
            context.user_data.pop("date_start", None)
            context.user_data.pop("date_end", None)
        else:
            year = int(value)
            context.user_data["date_start"] = date(year, 1, 1)
            context.user_data["date_end"] = min(date(year, 12, 31), date.today())
        await query.edit_message_text(
            filter_summary(context.user_data), reply_markup=main_menu(context.user_data)
        )
    elif data == "subgenres":
        selected = selected_genres(context.user_data)
        if len(selected) == 1 and GENRES[next(iter(selected))].subgenres:
            slug = next(iter(selected))
            await query.edit_message_text(
                f"Поджанры: {GENRES[slug].title}",
                reply_markup=subgenre_menu(slug),
            )
        else:
            await query.edit_message_text(
                "Выберите родительский жанр:",
                reply_markup=subgenre_genre_menu(0),
            )
    elif data.startswith("sg-genres:"):
        await query.edit_message_text(
            "Выберите родительский жанр:",
            reply_markup=subgenre_genre_menu(int(data.split(":")[1])),
        )
    elif data.startswith("sg:"):
        slug = GENRE_SLUGS[int(data.split(":")[1])]
        await query.edit_message_text(
            f"Поджанры: {GENRES[slug].title}",
            reply_markup=subgenre_menu(slug),
        )
    elif data == "subgenre-search":
        context.user_data["pending_input"] = "subgenre"
        await query.edit_message_text(
            "Напишите часть названия поджанра, например: latin",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Отмена", callback_data="cancel-input")]]
            ),
        )
    elif data == "subgenre-clear":
        context.user_data.pop("subgenre", None)
        await query.edit_message_text(
            "Поджанр убран.\n\n" + filter_summary(context.user_data),
            reply_markup=main_menu(context.user_data),
        )
    elif data.startswith("s:"):
        _, genre_index, subgenre_id = data.split(":")
        slug = GENRE_SLUGS[int(genre_index)]
        match = next(
            (item for item in GENRES[slug].subgenres if item.id == int(subgenre_id)),
            None,
        )
        if not match:
            await query.edit_message_text(
                "Поджанр больше не существует.",
                reply_markup=main_menu(context.user_data),
            )
            return
        context.user_data["genres"] = [slug]
        context.user_data["subgenre"] = {"id": match.id, "title": match.title}
        await query.edit_message_text(
            filter_summary(context.user_data), reply_markup=main_menu(context.user_data)
        )
    elif data == "random":
        start_date, end_date = effective_range(context.user_data)
        subgenre = context.user_data.get("subgenre")
        url, genre_title, selected_date = random_catalog_url(
            selected_genres(context.user_data),
            start=start_date,
            end=end_date,
            subgenre_id=subgenre["id"] if subgenre else None,
        )
        await query.edit_message_text(
            f"Жанр: {genre_title}\nДата: {selected_date:%d.%m.%Y}"
            + (f"\nПоджанр: {subgenre['title']}" if subgenre else ""),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Открыть Beatport", url=url)],
                    [InlineKeyboardButton("🎲 Ещё", callback_data="random")],
                    [InlineKeyboardButton("В меню", callback_data="menu")],
                ]
            ),
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Unhandled Telegram update", exc_info=context.error)


def build_application(token: str) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("year", year_command))
    application.add_handler(CommandHandler("dates", dates_command))
    application.add_handler(CommandHandler("subgenre", subgenre_command))
    application.add_handler(CallbackQueryHandler(on_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
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
