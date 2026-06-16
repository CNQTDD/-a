import logging

from app.knowledge.masking import mask_sensitive_text, safe_knowledge_log_fields


def test_masks_phone_and_identity_number() -> None:
    text = "客户电话13812345678，身份证530102199001011234"
    result = mask_sensitive_text(text)
    assert "13812345678" not in result.text
    assert "530102199001011234" not in result.text
    assert "138****5678" in result.text
    assert result.categories == {"phone", "identity_number"}


def test_masks_email() -> None:
    text = "联系方式：user@example.com"
    result = mask_sensitive_text(text)
    assert "user@example.com" not in result.text
    assert "email" in result.categories


def test_leaves_ordinary_text_unchanged() -> None:
    text = "客户反映套餐费用异常，要求退费处理。"
    result = mask_sensitive_text(text)
    assert result.text == text
    assert result.categories == set()


def test_does_not_false_positive_order_numbers() -> None:
    text = "订单号：2023081500012345"
    result = mask_sensitive_text(text)
    # 18-digit order numbers should not be treated as identity
    assert "identity_number" not in result.categories


def test_mask_email_short_local_part() -> None:
    text = "a@example.com"
    result = mask_sensitive_text(text)
    assert "a@example.com" not in result.text
    assert "a**@example.com" in result.text


def test_masks_configured_address_pattern() -> None:
    text = "客户住址：云南省昆明市五华区人民中路100号，要求上门处理。"
    result = mask_sensitive_text(text, address_patterns=[r"云南省昆明市\S+?号"])
    assert "云南省昆明市五华区人民中路100号" not in result.text
    assert "[地址已脱敏]" in result.text
    assert "address" in result.categories


def test_safe_knowledge_log_fields_exclude_all_raw_sensitive_values(caplog) -> None:
    logger = logging.getLogger("tests.knowledge.masking")
    caplog.set_level(logging.INFO, logger=logger.name)
    raw = (
        "电话13812345678，身份证530102199001011234，邮箱user@example.com，"
        "地址云南省昆明市五华区人民中路100号。"
    )

    fields = safe_knowledge_log_fields(
        raw,
        address_patterns=[r"云南省昆明市\S+?号"],
    )
    logger.info("knowledge_preprocessed %s", fields)

    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert "13812345678" not in rendered
    assert "530102199001011234" not in rendered
    assert "user@example.com" not in rendered
    assert "云南省昆明市五华区人民中路100号" not in rendered
    assert fields["sensitive_categories"] == [
        "address",
        "email",
        "identity_number",
        "phone",
    ]
