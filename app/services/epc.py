from __future__ import annotations

import re
from typing import Optional

HEX_TOKEN_RE = re.compile(r"[0-9a-fA-F]{8,}")


def normalize_epc(raw: Optional[str]) -> str:
    """
    Normalize EPC input by extracting the longest hex token and uppercasing it.
    Returns an empty string when no usable token is found.
    """
    if not raw:
        return ""
    tokens = HEX_TOKEN_RE.findall(raw.strip())
    if not tokens:
        return ""
    longest = max(tokens, key=len)
    return longest.upper()
