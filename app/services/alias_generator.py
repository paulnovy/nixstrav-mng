from __future__ import annotations

from typing import Iterable, Set

TREE_NAMES = [
    "Dab",
    "Jesion",
    "Buk",
    "Grab",
    "Lipa",
    "Modrzew",
    "Sosna",
    "Swierk",
    "Brzoza",
    "Olcha",
    "Wiaz",
    "Jodla",
    "Topola",
    "Jawor",
    "Kasztan",
    "Platan",
    "Klon",
]

FRUIT_NAMES = [
    "Jagoda",
    "Truskawka",
    "Malina",
    "Porzeczka",
    "Wisnia",
    "Jablko",
    "Sliwka",
    "Agrest",
    "Jezyzna",
    "Brzoskwinia",
    "Morela",
    "Gruszka",
    "Winogrono",
]


def generate_alias(alias_group: str, existing_aliases: Iterable[str]) -> str:
    """
    Generate a unique alias from the configured pool using suffixes when needed.
    """
    pool = TREE_NAMES if alias_group == "male_tree" else FRUIT_NAMES
    existing: Set[str] = {a for a in existing_aliases if a}

    for name in pool:
        if name not in existing:
            return name

    # fallback with suffix
    suffix = 2
    while True:
        for name in pool:
            candidate = f"{name}-{suffix}"
            if candidate not in existing:
                return candidate
        suffix += 1
