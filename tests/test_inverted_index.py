from suggester.inverted_index import InvertedIndex


def test_inverted_index_anchor_and_scoring():
    idx = InvertedIndex()

    tool1_terms = {
        "name": ["export_csv"],
        "description": ["exporta", "dados", "csv"],
        "keywords": ["exportar", "csv", "arquivo"],
        "aliases": ["baixar csv"],
    }
    tool2_terms = {
        "name": ["plot_chart"],
        "description": ["gera", "grafico"],
        "keywords": ["grafico", "plotar"],
        "aliases": [],
    }

    idx.add_tool("export_csv", tool1_terms)
    idx.add_tool("plot_chart", tool2_terms)

    # Query: complete term "exportar" and expanded term "csv"
    ranked = idx.query(
        complete_terms={"exportar"},
        expanded_terms={"csv"},
        require_anchor=True,
        top_k=3,
        min_score=1.0,
    )
    assert ranked, "Should return suggestions"
    assert ranked[0][0] == "export_csv"

    # Only description term should not match when require_anchor=True
    ranked_desc = idx.query(
        complete_terms={"dados"},
        expanded_terms=set(),
        require_anchor=True,
        top_k=3,
    )
    assert ranked_desc == []

