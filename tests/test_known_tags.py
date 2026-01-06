from app.services.known_tags import atomic_write_known_tags, load_known_tags


def test_atomic_write_known_tags(tmp_path):
    path = tmp_path / "known_tags.json"
    data1 = {"E1": {"alias": "A"}}
    atomic_write_known_tags(path, data1)
    assert path.exists()
    data2 = {"E1": {"alias": "B"}, "E2": {"alias": "C"}}
    atomic_write_known_tags(path, data2)
    loaded = load_known_tags(path)
    assert loaded["E1"]["alias"] == "B"
    assert loaded["E2"]["alias"] == "C"
