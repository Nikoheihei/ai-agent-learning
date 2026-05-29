from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_PATH = DATA_DIR / "audit_log.json"
PAYMENTS_PATH = DATA_DIR / "payments.json"
PACT_PATH = DATA_DIR / "pact.json"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


@dataclass
class AuditEntry:
    id: str
    created_at: str
    action: str
    result: Literal["allowed", "denied", "require_approval"]
    principal_id: str
    wallet_id: str
    authz_details: Dict[str, Any]
    request: Dict[str, Any]
    error: Optional[str] = None


class AuditLog:
    def __init__(self, path: Path = AUDIT_LOG_PATH) -> None:
        self.path = path

    def list(self) -> List[Dict[str, Any]]:
        return load_json(self.path, [])

    def append(self, entry: AuditEntry) -> None:
        items = self.list()
        items.append(asdict(entry))
        save_json(self.path, items)


class PaymentStore:
    def __init__(self, path: Path = PAYMENTS_PATH) -> None:
        self.path = path

    def list(self) -> List[Dict[str, Any]]:
        return load_json(self.path, [])

    def create(self, payment: Dict[str, Any]) -> None:
        items = self.list()
        items.append(payment)
        save_json(self.path, items)

    def upsert_by_invoice(self, payment: Dict[str, Any]) -> None:
        items = self.list()
        for idx, item in enumerate(items):
            if item["invoice_id"] == payment["invoice_id"]:
                items[idx] = payment
                save_json(self.path, items)
                return
        items.append(payment)
        save_json(self.path, items)

    def find_by_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        for item in self.list():
            if item["invoice_id"] == invoice_id:
                return item
        return None

    def find_by_payment_id(self, payment_id: str) -> Optional[Dict[str, Any]]:
        for item in self.list():
            if item["payment_id"] == payment_id:
                return item
        return None


class PactStore:
    def __init__(self, path: Path = PACT_PATH) -> None:
        self.path = path
        if not self.path.exists():
            self.reset_default()

    def reset_default(self) -> Dict[str, Any]:
        now = utcnow()
        pact = {
            "pact_id": "pact-demo-001",
            "status": "active",
            "activated_at": iso(now),
            "wallet_id": "wallet-demo-001",
            "principal_id": "agent-demo-001",
            "intent": "Buy up to 5 risk reports on Base within 24 hours from approved merchant endpoints",
            "execution_plan": (
                "1. Request the x402 protected risk API.\n"
                "2. Decode PAYMENT-REQUIRED and pick the exact BASE_USDC offer.\n"
                "3. Ask CAW to settle only if the transfer fits the pact policy.\n"
                "4. Retry the original request with PAYMENT-SIGNATURE and keep the settlement receipt."
            ),
            "completion_conditions": [
                {"type": "tx_count", "threshold": "5"},
                {"type": "amount_spent_usd", "threshold": "5.00"},
                {"type": "time_elapsed", "threshold": "86400"},
            ],
            "policies": [
                {
                    "name": "x402-risk-api-usdc-on-base",
                    "type": "transfer",
                    "rules": {
                        "effect": "allow",
                        "when": {
                            "chain_in": ["BASE_ETH"],
                            "token_in": [{"chain_id": "BASE_ETH", "token_id": "BASE_USDC"}],
                            "destination_address_in": [
                                {"chain_id": "BASE_ETH", "address": "merchant-risk-api"}
                            ],
                            "merchant_id_in": ["merchant-risk-api"],
                            "resource_prefix_in": ["risk-report:"],
                        },
                        "deny_if": {
                            "amount_usd_gt": "1.20",
                            "usage_limits": {
                                "rolling_24h": {"amount_usd_gt": "5.00", "tx_count_gt": 5}
                            },
                        },
                        "review_if": {"amount_usd_gt": "1.00"},
                    },
                }
            ],
        }
        save_json(self.path, pact)
        return pact

    def get(self) -> Dict[str, Any]:
        return load_json(self.path, {})

    def save(self, pact: Dict[str, Any]) -> Dict[str, Any]:
        save_json(self.path, pact)
        return pact


def make_tx_hash() -> str:
    return "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:24]
