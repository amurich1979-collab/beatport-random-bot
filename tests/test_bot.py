import random
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from bot import (
    GENRE_SLUGS,
    LINK_PREVIEW,
    MIN_DATE,
    date_menu,
    effective_range,
    extract_preview_tracks,
    genre_menu,
    main_menu,
    parse_iso_date,
    random_catalog_url,
    subgenre_genre_menu,
    subgenre_menu,
    subgenre_results_menu,
    validate_range,
)
from catalog import GENRES, search_subgenres
from history import HistoryStore


def test_random_catalog_url_uses_selected_genres_and_range():
    url, title, selected_date = random_catalog_url(
        {"house"},
        start=date(2024, 2, 1),
        end=date(2024, 2, 29),
        rng=random.Random(7),
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.path == "/genre/house/5/tracks"
    assert title == "House"
    assert date(2024, 2, 1) <= selected_date <= date(2024, 2, 29)
    expected_date = selected_date.isoformat()
    assert query["publish_date"] == [f"{expected_date}:{expected_date}"]


def test_random_catalog_url_supports_subgenre():
    url, _, _ = random_catalog_url(
        {"tech-house"},
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        subgenre_id=257,
        rng=random.Random(1),
    )
    assert parse_qs(urlparse(url).query)["sub_genre_id"] == ["257"]


def test_random_catalog_url_rejects_unknown_or_empty_explicit_genre():
    with pytest.raises(ValueError, match="Неизвестный"):
        random_catalog_url({"not-a-genre"})


def test_date_validation_and_parsing():
    assert parse_iso_date("2024-02-29") == date(2024, 2, 29)
    validate_range(date(2024, 1, 1), date(2024, 1, 31), today=date(2024, 2, 1))
    with pytest.raises(ValueError, match="формате"):
        parse_iso_date("01.02.2024")
    with pytest.raises(ValueError, match="раньше конечной"):
        validate_range(date(2024, 2, 1), date(2024, 1, 1))


def test_effective_range_defaults_to_full_catalog():
    assert effective_range({}, today=date(2025, 1, 2)) == (MIN_DATE, date(2025, 1, 2))


def test_subgenre_search_is_case_insensitive_and_keeps_parent():
    matches = search_subgenres("LATIN")
    assert (
        "tech-house",
        next(item for item in GENRES["tech-house"].subgenres if item.id == 257),
    ) in matches
    assert all("latin" in subgenre.title.casefold() for _, subgenre in matches)


def test_genre_catalog_matches_current_beatport_menu():
    assert len(GENRES) == 46
    assert GENRES["brazilian-funk"].id == 101
    assert GENRES["latin-electronic"].id == 111
    assert GENRES["downtempo"].id == 63
    assert GENRES["organic-house"].id == 93


def test_genre_menu_callbacks_fit_telegram_limit():
    for page in range(6):
        markup = genre_menu({"genres": [GENRE_SLUGS[0]]}, page)
        callbacks = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
            if button.callback_data
        ]
        assert callbacks
        assert all(len(value.encode()) <= 64 for value in callbacks)


def test_button_menus_expose_dates_and_subgenres_without_commands():
    date_callbacks = {
        button.callback_data
        for row in date_menu().inline_keyboard
        for button in row
        if button.callback_data
    }
    assert {
        "period:30",
        "period:90",
        "period:365",
        "dates-custom",
        "years",
    } <= date_callbacks

    tech_house_callbacks = {
        button.callback_data
        for row in subgenre_menu("tech-house").inline_keyboard
        for button in row
        if button.callback_data
    }
    assert any(value.endswith(":257") for value in tech_house_callbacks)
    assert "subgenre-search" in tech_house_callbacks

    browse_callbacks = {
        button.callback_data
        for row in subgenre_genre_menu(0).inline_keyboard
        for button in row
        if button.callback_data
    }
    assert any(value.startswith("sg:") for value in browse_callbacks)


def test_main_menu_preserves_original_actions_and_adds_filters():
    buttons = [
        (button.text, button.callback_data)
        for row in main_menu({}).inline_keyboard
        for button in row
    ]
    assert buttons[:3] == [
        ("🎲 Случайный релиз", "random-release"),
        ("📀 Релизы за один случайный день", "random-day"),
        ("🎛 Выбрать жанр", "genres:0"),
    ]
    callbacks = {callback for _, callback in buttons}
    assert {"subgenres", "dates-menu", "reset"} <= callbacks


def test_telegram_link_preview_is_enabled_for_cover_cards():
    assert LINK_PREVIEW.is_disabled is False
    assert LINK_PREVIEW.prefer_large_media is True


def test_preview_extraction_keeps_release_and_audio_together():
    html = """
    <script type="application/json">
    {
      "props": {
        "track": {
          "id": 29511152,
          "sample_url":
            "https://geo-samples.beatport.com/track/example.LOFI.mp3",
          "release": {
            "id": 7133629,
            "slug": "especial-do-kamehameha"
          }
        }
      }
    }
    </script>
    """
    assert extract_preview_tracks(html) == [
        (
            "https://www.beatport.com/release/especial-do-kamehameha/7133629",
            "https://geo-samples.beatport.com/track/example.LOFI.mp3",
        )
    ]


def test_preview_extraction_rejects_untrusted_audio_hosts():
    html = """
    <script type="application/json">
    {"sample_url": "https://example.com/not-beatport.mp3",
     "release": {"id": 1, "slug": "wrong"}}
    </script>
    """
    assert extract_preview_tracks(html) == []


def test_subgenre_results_menu_builds_selectable_buttons():
    result = subgenre_results_menu("latin")
    assert result is not None
    text, markup = result
    assert "Найдено" in text
    assert any(
        button.callback_data and button.callback_data.startswith("s:")
        for row in markup.inline_keyboard
        for button in row
    )


def test_lock_file_is_ignored_by_git():
    gitignore = (
        Path(__file__).parents[1].joinpath(".gitignore").read_text(encoding="utf-8")
    )
    assert ".bot.lock" in gitignore


def test_release_history_is_persistent_and_user_specific(tmp_path):
    database = tmp_path / "history.sqlite3"
    first_store = HistoryStore(database)
    first_store.add(10, "https://www.beatport.com/release/one/1")
    first_store.add(10, "https://www.beatport.com/release/one/1")
    first_store.add(20, "https://www.beatport.com/release/two/2")

    second_store = HistoryStore(database)
    assert second_store.urls_for_user(10) == {"https://www.beatport.com/release/one/1"}
    assert second_store.urls_for_user(20) == {"https://www.beatport.com/release/two/2"}

    second_store.clear_user(10)
    assert second_store.urls_for_user(10) == set()
