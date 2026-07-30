import random
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from bot import GENRES, MIN_DATE, genre_menu, random_catalog_url


def test_random_catalog_url_is_bounded_and_uses_genre_id():
    url, title, selected_date = random_catalog_url(
        "house", today=date(2025, 2, 1), rng=random.Random(7)
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.path == "/genre/house/5/tracks"
    assert title == "House"
    assert MIN_DATE <= selected_date <= date(2025, 2, 1)
    expected_date = selected_date.isoformat()
    assert query["publish_date"] == [f"{expected_date}:{expected_date}"]


def test_random_catalog_url_rejects_unknown_genre():
    with pytest.raises(ValueError, match="Unknown genre"):
        random_catalog_url("not-a-genre")


def test_genre_menu_keeps_callback_data_within_telegram_limit():
    for page in range(4):
        markup = genre_menu(page)
        callbacks = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
            if button.callback_data
        ]
        assert callbacks
        assert all(len(value.encode()) <= 64 for value in callbacks)
        assert all(
            value.startswith(("genre:", "genres:")) or value in {"noop", "menu"}
            for value in callbacks
        )


def test_all_genres_have_unique_ids():
    ids = [genre_id for _, genre_id in GENRES.values()]
    assert len(ids) == len(set(ids))
