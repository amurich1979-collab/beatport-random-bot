"""Beatport genre catalog verified against the website on 2026-07-30."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Subgenre:
    id: int
    title: str


@dataclass(frozen=True, slots=True)
class Genre:
    id: int
    title: str
    subgenres: tuple[Subgenre, ...] = ()


def _subs(*items: tuple[int, str]) -> tuple[Subgenre, ...]:
    return tuple(Subgenre(*item) for item in items)


GENRES: dict[str, Genre] = {
    "140-deep-dubstep-grime": Genre(
        95, "140 / Deep Dubstep / Grime", _subs((241, "Grime"))
    ),
    "afro-house": Genre(
        89,
        "Afro House",
        _subs((240, "Afro / Latin"), (273, "3Step"), (274, "Afro Melodic")),
    ),
    "amapiano": Genre(98, "Amapiano"),
    "ambient-experimental": Genre(100, "Ambient / Experimental"),
    "bass-club": Genre(
        85,
        "Bass / Club",
        _subs(
            (196, "Juke / Footwork"),
            (197, "Global Club"),
            (236, "Jersey Club"),
            (237, "Gqom"),
            (238, "Bass/Club"),
            (239, "Reggae / Dancehall"),
            (242, "UK Funky"),
        ),
    ),
    "bass-house": Genre(91, "Bass House"),
    "brazilian-funk": Genre(
        101,
        "Brazilian Funk",
        _subs(
            (275, "Carioca Funk"),
            (276, "Mandelao Funk"),
            (277, "BH Funk"),
            (278, "Melodic Funk"),
            (314, "Eletrofunk"),
        ),
    ),
    "breaks-breakbeat-uk-bass": Genre(
        9, "Breaks / Breakbeat / UK Bass", _subs((209, "Glitch Hop"))
    ),
    "dance-pop": Genre(
        39,
        "Dance / Pop",
        _subs(
            (148, "Pop"),
            (150, "Tropical House"),
            (187, "Future Bass"),
            (254, "Afro Pop"),
            (302, "Latin Dance"),
        ),
    ),
    "deep-house": Genre(12, "Deep House"),
    "dj-tools-acapellas": Genre(
        16,
        "DJ Tools / Acapellas",
        _subs((45, "Loops"), (46, "Acapellas"), (108, "Battle Tools")),
    ),
    "downtempo": Genre(63, "Downtempo", _subs((338, "Lofi"), (339, "Trip-Hop"))),
    "drum-bass": Genre(
        1,
        "Drum & Bass",
        _subs(
            (5, "Liquid"),
            (6, "Jump Up"),
            (66, "Jungle"),
            (174, "Deep"),
            (191, "Halftime"),
        ),
    ),
    "dubstep": Genre(18, "Dubstep", _subs((234, "Melodic Dubstep"), (262, "Midtempo"))),
    "electro-classic-detroit-modern": Genre(94, "Electro (Classic / Detroit / Modern)"),
    "electronica": Genre(
        3, "Electronica", _subs((116, "Ambient"), (210, "Funk / Soul"))
    ),
    "funky-house": Genre(81, "Funky House"),
    "hard-dance-hardcore-neo-rave": Genre(
        8,
        "Hard Dance / Hardcore / Neo Rave",
        _subs(
            (100, "Hardstyle"),
            (120, "Hard House"),
            (121, "Hard Trance"),
            (212, "Uptempo"),
            (213, "Terror"),
            (214, "UK / Happy Hardcore"),
            (215, "Frenchcore"),
            (272, "Neo Rave"),
        ),
    ),
    "hard-techno": Genre(2, "Hard Techno", _subs((270, "Hard Techno"))),
    "house": Genre(
        5, "House", _subs((143, "Acid"), (177, "Soulful"), (315, "Latin House"))
    ),
    "indie-dance": Genre(37, "Indie Dance", _subs((223, "Dark Disco"), (334, "Italo"))),
    "jackin-house": Genre(97, "Jackin House"),
    "latin-electronic": Genre(
        111,
        "Latin Electronic",
        _subs(
            (302, "Latin Dance"),
            (329, "Raptor House"),
            (330, "Tribal / Guaracha"),
            (331, "Electronic Cumbia"),
            (332, "Moombahton"),
        ),
    ),
    "mainstage": Genre(
        96,
        "Mainstage",
        _subs(
            (152, "Big Room"),
            (246, "Electro House"),
            (247, "Future House"),
            (248, "Midtempo"),
            (249, "Speed House"),
            (252, "Future Rave"),
        ),
    ),
    "melodic-house-techno": Genre(
        90,
        "Melodic House & Techno",
        _subs((267, "Melodic House"), (268, "Melodic Techno")),
    ),
    "minimal-deep-tech": Genre(
        14,
        "Minimal / Deep Tech",
        _subs((167, "Bounce"), (188, "Deep Tech"), (316, "Minimal House")),
    ),
    "nu-disco-disco": Genre(
        50, "Nu Disco / Disco", _subs((210, "Funk / Soul"), (243, "Italo"))
    ),
    "organic-house": Genre(93, "Organic House", _subs((233, "Downtempo"))),
    "progressive-house": Genre(15, "Progressive House"),
    "psy-trance": Genre(
        13,
        "Psy-Trance",
        _subs(
            (168, "Full-On"),
            (169, "Progressive Psy"),
            (259, "Psychedelic"),
            (260, "Goa Trance"),
            (261, "Dark & Forest"),
            (263, "Psycore & Hi-Tech"),
        ),
    ),
    "tech-house": Genre(
        11, "Tech House", _subs((257, "Latin Tech"), (302, "Latin Dance"))
    ),
    "techno-peak-time-driving": Genre(
        6,
        "Techno (Peak Time / Driving)",
        _subs((218, "Peak Time"), (219, "Driving"), (328, "Psy-Techno")),
    ),
    "techno-raw-deep-hypnotic": Genre(
        92,
        "Techno (Raw / Deep / Hypnotic)",
        _subs(
            (224, "Deep / Hypnotic"),
            (225, "Raw"),
            (227, "EBM"),
            (228, "Dub"),
            (229, "Broken"),
        ),
    ),
    "trance-main-floor": Genre(
        7,
        "Trance (Main Floor)",
        _subs(
            (27, "Progressive Trance"),
            (29, "Tech Trance"),
            (31, "Hard Trance"),
            (128, "Uplifting Trance"),
            (129, "Vocal Trance"),
        ),
    ),
    "trance-raw-deep-hypnotic": Genre(
        99,
        "Trance (Raw / Deep / Hypnotic)",
        _subs((264, "Raw Trance"), (265, "Deep Trance"), (266, "Hypnotic Trance")),
    ),
    "trap-future-bass": Genre(
        38,
        "Trap / Future Bass",
        _subs((102, "Trap"), (210, "Funk / Soul"), (269, "Baile Funk")),
    ),
    "uk-garage-bassline": Genre(
        86,
        "UK Garage / Bassline",
        _subs(
            (198, "UK Garage"),
            (199, "Bassline"),
            (317, "2-Step"),
            (318, "Speed Garage"),
        ),
    ),
    "african": Genre(
        102,
        "African",
        _subs((279, "Afrobeats"), (280, "Afropop"), (281, "Afro R&B"), (282, "Alte")),
    ),
    "caribbean": Genre(
        103,
        "Caribbean",
        _subs(
            (283, "Reggae"),
            (284, "Dancehall"),
            (285, "Soca"),
            (286, "Dub"),
            (287, "Calypso"),
            (288, "Ska & Rocksteady"),
            (295, "Cumbia"),
            (297, "Merengue"),
            (303, "Latin Pop"),
        ),
    ),
    "country": Genre(
        104, "Country", _subs((289, "Country Pop"), (290, "Country Dance"))
    ),
    "dj-edits": Genre(
        110,
        "DJ Edits",
        _subs(
            (319, "African"),
            (320, "Caribbean"),
            (321, "Country"),
            (322, "Dance"),
            (323, "Hip-Hop"),
            (324, "Latin"),
            (325, "Pop"),
            (326, "R&B"),
            (327, "Rock"),
        ),
    ),
    "hip-hop": Genre(
        105,
        "Hip-Hop",
        _subs(
            (291, "East Coast"),
            (292, "West Coast"),
            (293, "Global"),
            (294, "Southern"),
            (299, "Dembow"),
            (302, "Latin Dance"),
        ),
    ),
    "latin": Genre(
        106,
        "Latin",
        _subs(
            (295, "Cumbia"),
            (296, "Salsa"),
            (297, "Merengue"),
            (298, "Reggaeton"),
            (299, "Dembow"),
            (300, "Regional Mexican"),
            (301, "Bachata"),
            (302, "Latin Dance"),
            (303, "Latin Pop"),
            (304, "Latin Hip-Hop"),
        ),
    ),
    "pop": Genre(
        107,
        "Pop",
        _subs((296, "Salsa"), (305, "K-Pop"), (306, "J-Pop"), (307, "Holiday")),
    ),
    "rb": Genre(108, "R&B", _subs((308, "Funk"), (309, "Soul"))),
    "rock": Genre(
        109,
        "Rock",
        _subs(
            (310, "Indie Rock"), (311, "Metal"), (312, "Punk & Pop Punk"), (313, "Ska")
        ),
    ),
}


def search_subgenres(query: str) -> list[tuple[str, Subgenre]]:
    needle = query.casefold().strip()
    if not needle:
        return []
    return [
        (slug, subgenre)
        for slug, genre in GENRES.items()
        for subgenre in genre.subgenres
        if needle in subgenre.title.casefold()
    ]
