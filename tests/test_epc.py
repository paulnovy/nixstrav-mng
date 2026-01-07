from app.services.epc import normalize_epc


def test_normalize_epc_picks_longest_hex_token():
    raw = "xxE2000017221101441890f1abYY"
    assert normalize_epc(raw) == "E2000017221101441890F1AB"


def test_normalize_epc_handles_prefix_and_whitespace():
    raw = "  0xE2000017221101441890f1ab  "
    assert normalize_epc(raw) == "E2000017221101441890F1AB"
