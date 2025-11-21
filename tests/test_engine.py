from suggester.engine import SuggestionEngine


def test_engine_suggests_export_csv():
    tools = [
        {
            "name": "export_csv",
            "description": "Exporta dados para CSV",
            "keywords": ["exportar", "csv", "arquivo"],
        }
    ]
    eng = SuggestionEngine(tools)

    eng.feed("expor", session_id="s1")
    eng.feed("t", session_id="s1")
    suggestions = eng.feed("ar para csv", session_id="s1")

    assert suggestions, "Should suggest at least one tool"
    assert suggestions[0]["id"] == "export_csv"

