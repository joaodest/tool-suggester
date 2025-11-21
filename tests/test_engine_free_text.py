from suggester.engine import SuggestionEngine


TOOLS = [
    {
        "name": "export_csv",
        "description": "Exporta dados tabulares",
        "keywords": ["exportar", "csv", "tabela", "dados"],
        "aliases": ["gerar csv", "baixar csv"],
    },
    {
        "name": "plot_chart",
        "description": "Mostra graficos",
        "keywords": ["grafico", "plotar"],
    },
]


def test_sentence_with_multiple_words_returns_suggestion():
    eng = SuggestionEngine(TOOLS)
    suggestions = eng.submit(
        "Ola, eu gostaria de exportar meus dados para csv o quanto antes",
        session_id="s1",
    )
    assert suggestions, "Should find suggestion even in long sentences"
    assert suggestions[0]["id"] == "export_csv"


def test_mixed_languages_still_match_keywords():
    eng = SuggestionEngine(TOOLS)
    suggestions = eng.submit(
        "Need to export essa tabela as csv",
        session_id="s2",
    )
    assert suggestions, "Should suggest export_csv in mixed text"
    assert suggestions[0]["id"] == "export_csv"


def test_sentence_without_anchor_returns_empty():
    eng = SuggestionEngine(TOOLS)
    suggestions = eng.submit("Favor ajudar com relatorio sem citar ferramentas", session_id="s3")
    assert suggestions == []


def test_default_max_intents_limits_to_first_window():
    eng = SuggestionEngine(TOOLS, top_k=5)
    text = "Preciso exportar dados e depois plotar graficos elaborados"
    suggestions = eng.submit(text, session_id="s4")
    assert suggestions
    assert suggestions[0]["id"] == "export_csv"
    assert all(item["id"] != "plot_chart" for item in suggestions)
