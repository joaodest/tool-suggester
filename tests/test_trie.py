from suggester.trie import Trie


def test_trie_prefix_terms_basic():
    t = Trie()
    t.bulk_insert(["exportar", "csv", "baixar"])

    assert "exportar" in t.prefix_terms("expor")
    assert "csv" in t.prefix_terms("cs")
    assert "baixar" in t.prefix_terms("bai")

