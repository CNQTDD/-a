from app.knowledge.chunking import (
    ComplaintChunker,
    RuleChunker,
    SlidingWindowChunker,
)


def test_sliding_window_short_text_is_single_chunk():
    chunker = SlidingWindowChunker(target_size=500, overlap=80)
    result = chunker.chunk("短文本", {"source": "test"})
    assert len(result) == 1
    assert result[0].text == "短文本"


def test_sliding_window_long_text_is_split():
    chunker = SlidingWindowChunker(target_size=100, overlap=20)
    long_text = "测试文本。" * 50
    result = chunker.chunk(long_text, {"source": "test"})
    assert len(result) > 1
    for chunk in result:
        assert len(chunk.text) <= 100


def test_overlap_does_not_duplicate_entire_chunk():
    chunker = SlidingWindowChunker(target_size=80, overlap=30)
    text = "A" * 40 + "。" + "B" * 40
    result = chunker.chunk(text)
    assert len(result) >= 1
    # Overlap should not produce identical chunks
    texts = [c.text for c in result]
    assert len(set(texts)) == len(texts)


def test_rule_chunker_preserves_heading():
    chunker = RuleChunker(max_chunk_size=600)
    text = "## 套餐变更规则\n用户可在合约期内变更套餐，但需支付差价。"
    result = chunker.chunk(text)
    assert len(result) >= 1
    assert result[0].metadata.get("heading") == "套餐变更规则"


def test_rule_chunker_preserves_article_number():
    chunker = RuleChunker(max_chunk_size=600)
    text = "第1条 退费标准：用户有权在7天内申请全额退费。"
    result = chunker.chunk(text)
    assert result[0].metadata.get("article_number") == "1"


def test_complaint_chunker_produces_single_record():
    chunker = ComplaintChunker()
    text = "投诉内容：套餐费用异常，要求核查。"
    result = chunker.chunk(text, {"source_id": "ticket-001"})
    assert len(result) == 1
    assert result[0].metadata.get("record_type") == "complaint"


def test_metadata_includes_region_product_when_provided():
    chunker = SlidingWindowChunker(target_size=300)
    result = chunker.chunk(
        "客户反映套餐变更费用异常。",
        metadata={
            "region": "云南",
            "product": "4G套餐",
            "source_time": "2025-03",
            "effective_at": "2025-01-01",
            "article_number": "3",
        },
    )
    assert result[0].metadata["region"] == "云南"
    assert result[0].metadata["product"] == "4G套餐"
    assert result[0].metadata["effective_at"] == "2025-01-01"
    assert result[0].metadata["article_number"] == "3"
