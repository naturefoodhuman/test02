# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:41:55

"""
Unit tests for secret / token recognizers (E5-C3-S1-T4).

The core deterministic scanner is dependency-light and must pass even when
``presidio_analyzer`` is not installed. Presidio recognizer construction is
checked with optional dependency awareness.
"""

import importlib.util

from _infra.network.privacy_gateway.models import PIIType
from _infra.network.privacy_gateway.recognizers.secret_recognizers import (
    SECRET_PATTERN_SPECS,
    detect_secrets,
    get_secret_recognizers,
)


def _types(text: str) -> set[PIIType]:
    return {entity.type for entity in detect_secrets(text)}


def test_secret_pattern_specs_cover_required_entities():
    covered = {spec.entity_type for spec in SECRET_PATTERN_SPECS}
    assert PIIType.JWT in covered
    assert PIIType.API_KEY in covered
    assert PIIType.ACCESS_TOKEN in covered
    assert PIIType.PRIVATE_KEY in covered
    assert PIIType.COOKIE in covered
    assert PIIType.SESSION_ID in covered
    assert PIIType.OAUTH_TOKEN in covered


def test_detect_jwt():
    text = (
        "token=eyJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    entities = detect_secrets(text)
    assert any(entity.type == PIIType.JWT for entity in entities)
    assert any(entity.recognizer == "regex:jwt" for entity in entities)


def test_detect_github_pat():
    text = "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz123456"
    entities = detect_secrets(text)
    assert any(entity.type == PIIType.API_KEY and "ghp_" in entity.value for entity in entities)


def test_detect_openai_key():
    text = "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyzABCDE1234567890"
    entities = detect_secrets(text)
    assert any(entity.type == PIIType.API_KEY and "sk-proj-" in entity.value for entity in entities)


def test_detect_aws_access_key():
    text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
    entities = detect_secrets(text)
    assert any(entity.type == PIIType.API_KEY and entity.value == "AKIAIOSFODNN7EXAMPLE" for entity in entities)


def test_detect_private_key_header():
    text = "-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n-----END OPENSSH PRIVATE KEY-----"
    entities = detect_secrets(text)
    assert any(entity.type == PIIType.PRIVATE_KEY for entity in entities)


def test_detect_access_token_assignment():
    text = 'access_token="abcdEFGH1234567890abcd"'
    assert PIIType.ACCESS_TOKEN in _types(text)


def test_detect_oauth_bearer():
    text = "Authorization: Bearer ya29.a0AfH6SMAabcdefghijklmnopqrstuvwxyz"
    assert PIIType.OAUTH_TOKEN in _types(text)


def test_detect_cookie_header_and_session_id():
    text = "Cookie: sessionid=abcdef1234567890; csrftoken=tokenvalue123456"
    types = _types(text)
    assert PIIType.COOKIE in types

    session_text = "session_id=abcdef1234567890"
    assert PIIType.SESSION_ID in _types(session_text)


def test_detect_empty_text():
    assert detect_secrets("") == []


def test_detect_results_are_sorted_and_non_overlapping():
    text = (
        "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c "
        "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyzABCDE1234567890"
    )
    entities = detect_secrets(text)
    assert entities == sorted(entities, key=lambda entity: entity.start)
    for left, right in zip(entities, entities[1:]):
        assert left.end <= right.start


def test_get_secret_recognizers_optional_dependency_behavior():
    recognizers = get_secret_recognizers()
    if importlib.util.find_spec("presidio_analyzer") is None:
        assert recognizers == []
    else:
        assert len(recognizers) == len(SECRET_PATTERN_SPECS)
