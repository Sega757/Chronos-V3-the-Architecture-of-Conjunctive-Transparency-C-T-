from __future__ import annotations

import json
from chronos_common.canonical_json import canonicalize


def test_canonicalize_basic_types():
    data = {
        "str": "hello\nworld\t\"quoted\"",
        "int": 42,
        "float": 3.14159,
        "bool": True,
        "null": None,
        "list": [1, 2, "a"],
    }
    encoded = canonicalize(data)
    assert isinstance(encoded, bytes)
    assert b'"str":"hello\\nworld\\t\\"quoted\\""' in encoded


def test_canonicalize_unicode():
    data = {"text": "hello 🚀 \u03b1\u03b2\u03b3"}
    encoded = canonicalize(data)
    # UTF-8 characters should be emitted literally, unescaped
    assert "hello 🚀 αβγ".encode("utf-8") in encoded


def test_canonicalize_control_chars():
    for i in range(32):
        s = chr(i)
        data = {"char": s}
        encoded = canonicalize(data)
        expected_json_str = json.dumps(s, ensure_ascii=False)
        assert f'"char":{expected_json_str}'.encode("utf-8") in encoded
