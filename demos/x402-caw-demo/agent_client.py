from __future__ import annotations

import argparse
import json

import httpx

from app.x402 import (
    PAYMENT_REQUIRED_HEADER,
    PAYMENT_RESPONSE_HEADER,
    PAYMENT_SIGNATURE_HEADER,
    decode_b64_json,
    encode_b64_json,
)

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TARGET_ADDRESS = "0x9f1c6b1e4e7b8a2c3d4e5f60718293a4b5c6d7e8"


def pick_requirement(payment_required: dict) -> dict:
    for requirement in payment_required.get("accepts", []):
        if requirement.get("scheme") == "exact" and requirement.get("chain_id") == "BASE_ETH":
            return requirement
    raise RuntimeError("No acceptable x402 payment requirement found")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the autonomous x402 + CAW agent demo.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with httpx.Client(base_url=args.base_url, timeout=20.0) as client:
        pact = client.get("/caw/pact").json()
        print("0) 当前 CAW Pact / policy / budget:")
        print(json.dumps(pact, indent=2, ensure_ascii=False))

        print("1) 请求受 x402 保护的 API")
        resp = client.get("/paywalled/risk-report", params={"address": TARGET_ADDRESS, "chain": "base"})
        print("status:", resp.status_code)
        if resp.status_code != 402:
            raise SystemExit(f"Expected 402, got {resp.status_code}: {resp.text}")

        payment_required_header = resp.headers.get(PAYMENT_REQUIRED_HEADER)
        if not payment_required_header:
            raise SystemExit("402 response did not include PAYMENT-REQUIRED")

        payment_required = decode_b64_json(payment_required_header)
        requirement = pick_requirement(payment_required)
        print("2) agent 识别 PAYMENT-REQUIRED 并选择付款条件:")
        print(json.dumps(payment_required, indent=2, ensure_ascii=False))

        print("3) 通过 CAW Pact policy 发起 settlement")
        settle_resp = client.post("/caw/settle", json=requirement)
        settle_data = settle_resp.json()
        print(json.dumps(settle_data, indent=2, ensure_ascii=False))
        if not settle_data.get("ok"):
            raise SystemExit("Payment denied by CAW policy engine")

        invoice_id = requirement["invoice_id"]
        payment_payload = settle_data["payment_payload"]
        print("4) 使用 PAYMENT-SIGNATURE 重试原请求")
        final_resp = client.get(
            "/paywalled/risk-report",
            params={"address": TARGET_ADDRESS, "chain": "base"},
            headers={PAYMENT_SIGNATURE_HEADER: encode_b64_json(payment_payload)},
        )
        print("status:", final_resp.status_code)
        final_resp.raise_for_status()

        settlement_header = final_resp.headers.get(PAYMENT_RESPONSE_HEADER)
        settlement = decode_b64_json(settlement_header) if settlement_header else {}
        print("server PAYMENT-RESPONSE:")
        print(json.dumps(settlement, indent=2, ensure_ascii=False))

        report = final_resp.json()
        print("5) 获取结果:")
        print(json.dumps(report, indent=2, ensure_ascii=False))

        print("6) 拉取审计日志:")
        audit_logs = client.get("/caw/audit").json()
        print(json.dumps(audit_logs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
