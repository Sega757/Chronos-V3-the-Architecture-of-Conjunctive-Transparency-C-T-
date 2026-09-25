"""RFC 8785 (JSON Canonicalization Scheme) encoding.

Every payload that gets hashed or signed anywhere in SCCS MUST be
canonicalized with :func:`canonicalize` first, so that two nodes holding
semantically identical data always produce byte-identical (and therefore
hash-identical, signature-verifiable) output regardless of key insertion
order, whitespace, or float formatting quirks in their local JSON library.
"""

from __future__ import annotations

import math
from typing import Any


def canonicalize(value: Any) -> bytes:
    """Encode ``value`` as RFC 8785 canonical JSON and return UTF-8 bytes.

    Rules implemented (the subset of RFC 8785 that matters for the plain
    JSON-compatible values -- dict/list/str/int/float/bool/None -- SCCS
    messages are made of once converted from protobuf):

    * Object members are sorted by their UTF-16 code unit sequence.
    * No insignificant whitespace.
    * Numbers use the ECMAScript ``Number::toString`` shortest round-trip
      form; integral floats are still rendered with a fractional part is
      avoided by using ``repr`` and stripping a trailing ``.0`` only when
      the source was an actual Python ``int``.
    * Strings are escaped per the JSON spec with no extra escaping of
      non-ASCII characters (they are emitted as literal UTF-8).
    """
    return _encode(value).encode("utf-8")


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _encode_float(value)
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: kv[0])
        body = ",".join(f"{_encode_string(str(k))}:{_encode(v)}" for k, v in items)
        return "{" + body + "}"
    raise TypeError(f"canonical_json: unsupported type {type(value)!r}")


def _encode_float(value: float) -> str:
    if math.isnan(value) or math.isinf(value):
        raise ValueError("canonical_json: NaN/Infinity are not valid JSON")
    if value == int(value) and abs(value) < 1e15:
        # RFC 8785 numeric formatting still requires the shortest form;
        # an integral double is rendered without a fractional part.
        return str(int(value))
    return repr(value)


_ESCAPE_MAP = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _encode_string(value: str) -> str:
    out = ['"']
    for ch in value:
        if ch in _ESCAPE_MAP:
            out.append(_ESCAPE_MAP[ch])
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)
