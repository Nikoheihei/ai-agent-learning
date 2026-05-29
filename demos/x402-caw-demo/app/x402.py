from __future__ import annotations

import base64
import json
from typing import Any, Dict

PAYMENT_REQUIRED_HEADER = "PAYMENT-REQUIRED"
PAYMENT_SIGNATURE_HEADER = "PAYMENT-SIGNATURE"
PAYMENT_RESPONSE_HEADER = "PAYMENT-RESPONSE"


def encode_b64_json(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def decode_b64_json(value: str) -> Dict[str, Any]:
    try:
        decoded = base64.b64decode(value, validate=True)
        payload = json.loads(decoded.decode("utf-8"))
    except Exception as exc:
        raise ValueError("invalid base64 JSON payload") from exc

    if not isinstance(payload, dict):
        raise ValueError("x402 payload must be a JSON object")
    return payload
