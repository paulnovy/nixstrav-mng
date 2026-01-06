from app.services.alias_generator import TREE_NAMES, generate_alias


def test_generate_alias_uses_suffix_when_pool_exhausted():
    existing = set(TREE_NAMES)
    alias = generate_alias("male_tree", existing)
    assert alias == f"{TREE_NAMES[0]}-2"


def test_generate_alias_picks_first_free():
    existing = {TREE_NAMES[0]}
    alias = generate_alias("male_tree", existing)
    assert alias == TREE_NAMES[1]
