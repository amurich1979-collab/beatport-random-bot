import random
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from bot import (
    GENRE_SLUGS,
    MIN_DATE,
    effective_range,
    genre_menu,
    parse_iso_date,
    random_catalog_url,
    validate_range,
)
from catalog import GENRES, search_subgenres


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
