from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .mock_caw import MockCAW
from .storage import PaymentStore, iso, utcnow
from .x402 import (
    PAYMENT_REQUIRED_HEADER,
    PAYMENT_RESPONSE_HEADER,
    PAYMENT_SIGNATURE_HEADER,
    decode_b64_json,
    encode_b64_json,
)

app = FastAPI(title="x402 + CAW Demo")
caw = MockCAW()
payments = PaymentStore()

PRICE_USDC = 1.0
MERCHANT_ID = "merchant-risk-api"
CHAIN_ID = "BASE_ETH"
TOKEN_ID = "BASE_USDC"
PAY_TO = "merchant-risk-api"


class SettleRequest(BaseModel):
    scheme: str = "exact"
    invoice_id: str
    merchant_id: str
    pay_to: str
    amount_usdc: float
    chain_id: str
    token_id: str
    resource: str
    expires_at: Optional[str] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/caw/pact")
def get_pact() -> Dict[str, Any]:
    return caw.get_pact()


@app.put("/caw/pact")
def replace_pact(pact: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "pact": caw.pacts.save(pact)}


@app.post("/caw/reset")
def reset() -> Dict[str, Any]:
    pact = caw.pacts.reset_default()
    caw.audit.path.write_text("[]")
    caw.payments.path.write_text("[]")
    return {"ok": True, "pact": pact}


@app.get("/caw/audit")
def get_audit() -> List[Dict[str, Any]]:
    return caw.get_audit_logs()


@app.get("/caw/payments")
def get_payments() -> List[Dict[str, Any]]:
    return caw.get_payments()


@app.post("/caw/settle")
def settle(req: SettleRequest) -> Dict[str, Any]:
    return caw.settle_payment(req.model_dump())


@app.get("/paywalled/risk-report")
def risk_report(
    address: str,
    chain: str,
    payment_signature: Optional[str] = Header(default=None, alias=PAYMENT_SIGNATURE_HEADER),
) -> Any:
    if chain != "base":
        raise HTTPException(status_code=400, detail="Only base is supported in this demo")

    resource = "risk-report:%s:base" % address

    if not payment_signature:
        invoice_id = "inv-%s" % uuid.uuid4().hex[:10]
        requirement = {
            "x402Version": 2,
            "scheme": "exact",
            "network": "base",
            "asset": "USDC",
            "chain_id": CHAIN_ID,
            "token_id": TOKEN_ID,
            "amount_usdc": PRICE_USDC,
            "maxAmountRequired": str(PRICE_USDC),
            "merchant_id": MERCHANT_ID,
            "payTo": PAY_TO,
            "pay_to": PAY_TO,
            "invoice_id": invoice_id,
            "resource": resource,
            "expires_at": iso(utcnow() + timedelta(minutes=10)),
            "description": "Pay 1 USDC on Base to unlock the risk report",
        }
        payment_required = {
            "x402Version": 2,
            "error": "payment_required",
            "accepts": [requirement],
        }
        return JSONResponse(
            status_code=402,
            content=payment_required,
            headers={PAYMENT_REQUIRED_HEADER: encode_b64_json(payment_required)},
        )

    try:
        payment_payload = decode_b64_json(payment_signature)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    invoice_id = str(payment_payload.get("invoice_id", ""))
    payment = payments.find_by_invoice(invoice_id)
    settlement_response = verify_payment_payload(payment_payload, payment, resource)
    if not settlement_response["ok"]:
        return JSONResponse(
            status_code=402,
            content={"error": "payment_not_settled", "settlement": settlement_response},
            headers={PAYMENT_RESPONSE_HEADER: encode_b64_json(settlement_response)},
        )

    report = {
        "report_id": "report-%s" % address[-6:],
        "queried_address": address,
        "chain": chain,
        "risk_score": 82,
        "summary": [
            "Interacted with a newly deployed contract in the last 7 days",
            "Counterparty graph overlaps with previously flagged addresses",
            "High-value token movement detected across 3 hops",
        ],
        "generated_at": iso(utcnow()),
        "paid_invoice_id": invoice_id,
        "settlement_tx_hash": payment["tx_hash"],
        "payment_id": payment["payment_id"],
    }
    return JSONResponse(
        content=report,
        headers={PAYMENT_RESPONSE_HEADER: encode_b64_json(settlement_response)},
    )


def verify_payment_payload(
    payload: Dict[str, Any],
    payment: Optional[Dict[str, Any]],
    resource: str,
) -> Dict[str, Any]:
    if not payment:
        return {"ok": False, "reason": "Unknown or unsettled invoice"}

    checks = {
        "payment_id": payload.get("payment_id") == payment["payment_id"],
        "tx_hash": payload.get("tx_hash") == payment["tx_hash"],
        "status": payload.get("status") == "settled",
        "amount_usdc": float(payload.get("amount_usdc", -1)) == float(payment["amount_usdc"]),
        "chain_id": payload.get("chain_id") == payment["chain_id"],
        "token_id": payload.get("token_id") == payment["token_id"],
        "pay_to": payload.get("pay_to") == payment["pay_to"],
        "resource": payload.get("resource") == resource,
    }

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return {
            "ok": False,
            "reason": "Payment payload does not match the requested resource",
            "failed_checks": failed,
            "invoice_id": payment["invoice_id"],
        }

    return {
        "ok": True,
        "status": "settled",
        "invoice_id": payment["invoice_id"],
        "payment_id": payment["payment_id"],
        "tx_hash": payment["tx_hash"],
        "audit_id": payment["audit_id"],
    }
