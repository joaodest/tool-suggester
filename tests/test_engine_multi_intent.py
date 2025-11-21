from suggester.engine import SuggestionEngine


CATALOG = [
    {
        "name": "export_csv",
        "description": "Exporta dados para arquivos csv",
        "keywords": ["exportar", "csv", "arquivo"],
    },
    {
        "name": "create_report",
        "description": "Gera relatorios automatizados",
        "keywords": ["relatorio", "relatorio mensal", "gerar relatorio"],
    },
    {
        "name": "send_email",
        "description": "Envia emails com anexos",
        "keywords": ["email", "enviar", "mensagem"],
    },
    {
        "name": "multi_tool",
        "description": "Exporta e gera relatorios no mesmo fluxo",
        "keywords": ["exportar", "relatorio"],
    },
]


def test_three_intents_return_three_tools():
    eng = SuggestionEngine(CATALOG[:3], max_intents=3, top_k=5)
    text = "Preciso exportar arquivos, gerar relatorios e enviar email urgente"
    suggestions = eng.submit(text, session_id="multi-1")
    ids = {s["id"] for s in suggestions}
    assert ids == {"export_csv", "create_report", "send_email"}


def test_tool_covering_two_intents_appears_once_with_combined_reason():
    eng = SuggestionEngine(CATALOG, max_intents=3, combine_strategy="sum", top_k=3)
    text = "Consegue exportar dados e gerar relatorio consolidado?"
    suggestions = eng.submit(text, session_id="multi-2")
    assert suggestions, "Should find at least one tool"
    multi_entries = [item for item in suggestions if item["id"] == "multi_tool"]
    assert len(multi_entries) == 1
    reason = multi_entries[0]["reason"]
    assert "exportar" in reason
    assert "relatorio" in reason


def test_without_separators_behaves_like_single_intent():
    eng = SuggestionEngine(CATALOG[:2], max_intents=3)
    text = "Preciso muito exportar os dados agora mesmo"
    suggestions = eng.submit(text, session_id="multi-3")
    assert len(suggestions) == 1
    assert suggestions[0]["id"] == "export_csv"
