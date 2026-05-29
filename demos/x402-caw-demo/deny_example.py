from __future__ import annotations

import argparse
import json

import httpx

from app.x402 import PAYMENT_REQUIRED_HEADER, decode_b64_json

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TARGET_ADDRESS = "0x9f1c6b1e4e7b8a2c3d4e5f60718293a4b5c6d7e8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CAW policy denial example.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with httpx.Client(base_url=args.base_url, timeout=20.0) as client:
        client.post("/caw/reset")
        pact = client.get("/caw/pact").json()
        pact["policies"][0]["rules"]["deny_if"]["amount_usd_gt"] = "0.50"
        client.put("/caw/pact", json=pact).raise_for_status()

        print("当前 Pact 已把单笔预算降到 0.50 USDC，用于观察 deny 流程。")
        resp = client.get("/paywalled/risk-report", params={"address": TARGET_ADDRESS, "chain": "base"})
        payment_required = decode_b64_json(resp.headers[PAYMENT_REQUIRED_HEADER])
        requirement = payment_required["accepts"][0]
        settle_resp = client.post("/caw/settle", json=requirement)
        print(json.dumps(settle_resp.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
