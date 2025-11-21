from suggester.tokenizer import tokens, tokens_with_spans


def test_tokens_drop_stopwords_keeps_intent_terms():
    text = "Olá, eu gostaria de exportar meus dados para csv imediatamente"
    result = tokens(text, drop_stopwords=True)
    assert "exportar" in result
    assert "dados" in result
    assert "csv" in result
    assert "eu" not in result
    assert "gostaria" not in result


def test_tokens_with_spans_preserve_order_and_offsets():
    text = "Preciso exportar tabela para csv"
    spans = tokens_with_spans(text)
    tokens_only = [tok for tok, _ in spans]
    assert tokens_only[:3] == ["preciso", "exportar", "tabela"]
    # ensure spans are increasing (no overlaps / preserving order)
    positions = [span for _, span in spans]
    for earlier, later in zip(positions, positions[1:]):
        assert earlier[1] <= later[0]


def test_noise_tokens_removed_by_default():
    assert tokens("123 0000 !!!!") == []
    assert tokens("s3 bucket 0000") == ["s3", "bucket"]

