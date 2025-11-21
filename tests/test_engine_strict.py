from suggester.engine import SuggestionEngine


def test_engine_strict_requires_anchor_for_description_only():
    tools = [
        {
            "name": "export_csv",
            "description": "Exporta dados para CSV",
            "keywords": ["exportar", "csv", "arquivo"],
        },
        {
            "name": "plot_chart",
            "description": "Gera grafico de linhas",
            "keywords": ["grafico", "plotar"],
        },
    ]
    eng = SuggestionEngine(tools)

    # description-only term should not trigger suggestions with require_anchor=True
    assert eng.submit("dados", session_id="s1") == []


def test_engine_prefix_and_anchor_yields_top_hit():
    tools = [
        {
            "name": "export_csv",
            "description": "Exporta dados para CSV",
            "keywords": ["exportar", "csv", "arquivo"],
            "aliases": ["baixar csv"],
        },
    ]
    eng = SuggestionEngine(tools)
    eng.feed("expor", session_id="s2")
    eng.feed("t", session_id="s2")
    suggestions = eng.feed("ar para csv", session_id="s2")
    assert suggestions, "Should suggest at least one tool"
    assert suggestions[0]["id"] == "export_csv"

