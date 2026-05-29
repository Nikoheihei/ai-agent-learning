from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .storage import AuditEntry, AuditLog, PactStore, PaymentStore, iso, make_tx_hash, utcnow


@dataclass
class PolicyDecision:
    allowed: bool
    result: str
    denial_code: Optional[str]
    reason: str
    policy_names: List[str]
    requires_approval: bool = False


class MockCAW:
    def __init__(self) -> None:
        self.audit = AuditLog()
        self.pacts = PactStore()
        self.payments = PaymentStore()

    def get_pact(self) -> Dict[str, Any]:
        return self.pacts.get()

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        return self.audit.list()

    def get_payments(self) -> List[Dict[str, Any]]:
        return self.payments.list()

    def _sum_window(self, seconds: int) -> Tuple[float, int]:
        now = utcnow()
        total = 0.0
        count = 0
        for payment in self.payments.list():
            created_at = datetime.fromisoformat(payment["created_at"])
            if (now - created_at).total_seconds() <= seconds:
                total += float(payment["amount_usdc"])
                count += 1
        return total, count

    def _completion_decision(self, pact: Dict[str, Any]) -> Optional[PolicyDecision]:
        if pact.get("status") != "active":
            return PolicyDecision(
                False,
                "denied",
                "PACT_NOT_ACTIVE",
                "Pact is %s" % pact.get("status", "missing"),
                [],
            )

        payments = self.payments.list()
        spent = sum(float(payment["amount_usdc"]) for payment in payments)
        activated_at = datetime.fromisoformat(pact["activated_at"])
        elapsed = (utcnow() - activated_at).total_seconds()

        for condition in pact["completion_conditions"]:
            condition_type = condition["type"]
            threshold = condition["threshold"]
            if condition_type == "tx_count" and len(payments) >= int(threshold):
                return PolicyDecision(False, "denied", "PACT_TX_COUNT_COMPLETE", "Pact tx count completed", [])
            if condition_type == "amount_spent_usd" and spent >= float(threshold):
                return PolicyDecision(False, "denied", "PACT_SPEND_COMPLETE", "Pact spend amount completed", [])
            if condition_type == "time_elapsed" and elapsed >= float(threshold):
                return PolicyDecision(False, "denied", "PACT_TIME_ELAPSED", "Pact time window elapsed", [])
        return None

    def _matches_when(self, request: Dict[str, Any], when: Dict[str, Any]) -> bool:
        if request["chain_id"] not in when.get("chain_in", [request["chain_id"]]):
            return False

        token_refs = when.get("token_in")
        if token_refs and not any(
            ref["chain_id"] == request["chain_id"] and ref["token_id"] == request["token_id"]
            for ref in token_refs
        ):
            return False

        destinations = when.get("destination_address_in")
        if destinations and not any(
            ref["chain_id"] == request["chain_id"] and ref["address"] == request["pay_to"]
            for ref in destinations
        ):
            return False

        merchants = when.get("merchant_id_in")
        if merchants and request["merchant_id"] not in merchants:
            return False

        prefixes = when.get("resource_prefix_in")
        if prefixes and not any(request["resource"].startswith(prefix) for prefix in prefixes):
            return False

        return True

    def _limit_hit(self, request: Dict[str, Any], limits: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        amount = float(request["amount_usdc"])

        if "amount_gt" in limits and amount > float(limits["amount_gt"]):
            return True, "Amount exceeds token-denominated limit"

        if "amount_usd_gt" in limits and amount > float(limits["amount_usd_gt"]):
            return True, "Amount exceeds USD limit"

        rolling_24h = limits.get("usage_limits", {}).get("rolling_24h")
        if rolling_24h:
            spent_24h, tx_count_24h = self._sum_window(86400)
            if "amount_usd_gt" in rolling_24h and spent_24h + amount > float(rolling_24h["amount_usd_gt"]):
                return True, "Amount exceeds rolling 24h USD budget"
            if "tx_count_gt" in rolling_24h and tx_count_24h + 1 > int(rolling_24h["tx_count_gt"]):
                return True, "Transaction count exceeds rolling 24h limit"

        return False, None

    def evaluate_payment(self, request: Dict[str, Any]) -> PolicyDecision:
        pact = self.get_pact()
        if request.get("expires_at") and utcnow() > datetime.fromisoformat(request["expires_at"]):
            return PolicyDecision(
                False,
                "denied",
                "PAYMENT_REQUIREMENT_EXPIRED",
                "x402 payment requirement expired",
                [],
            )

        completion_decision = self._completion_decision(pact)
        if completion_decision:
            return completion_decision

        matched_policy_names: List[str] = []
        review_reasons: List[str] = []

        for policy in pact["policies"]:
            if policy["type"] != "transfer":
                continue

            rules = policy["rules"]
            if rules["effect"] != "allow":
                continue

            if not self._matches_when(request, rules.get("when", {})):
                continue

            matched_policy_names.append(policy["name"])

            deny_hit, deny_reason = self._limit_hit(request, rules.get("deny_if", {}))
            if deny_hit:
                return PolicyDecision(
                    False,
                    "denied",
                    "POLICY_DENY_LIMIT",
                    deny_reason or "Denied by pact policy",
                    matched_policy_names,
                )

            review_hit, review_reason = self._limit_hit(request, rules.get("review_if", {}))
            if review_hit or rules.get("always_review"):
                review_reasons.append(review_reason or "Owner approval required by pact policy")

        if not matched_policy_names:
            return PolicyDecision(
                False,
                "denied",
                "NO_MATCHING_POLICY",
                "No pact policy matched the requested transfer",
                [],
            )

        if review_reasons:
            return PolicyDecision(
                False,
                "require_approval",
                None,
                review_reasons[0],
                matched_policy_names,
                requires_approval=True,
            )

        return PolicyDecision(True, "allowed", None, "Payment allowed", matched_policy_names)

    def settle_payment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        pact = self.get_pact()
        existing_payment = self.payments.find_by_invoice(request["invoice_id"])
        if existing_payment:
            return {
                "ok": True,
                "idempotent": True,
                "payment": existing_payment,
                "payment_payload": self._payment_payload(existing_payment, pact, request),
            }

        decision = self.evaluate_payment(request)

        audit_entry = AuditEntry(
            id="audit-%s" % make_tx_hash()[2:10],
            created_at=iso(utcnow()),
            action="payment.settle",
            result=decision.result,
            principal_id=pact["principal_id"],
            wallet_id=pact["wallet_id"],
            authz_details={
                "denial_code": decision.denial_code,
                "reason": decision.reason,
                "pact_id": pact["pact_id"],
                "invoice_id": request["invoice_id"],
                "matched_policies": decision.policy_names,
            },
            request=request,
            error=None if decision.allowed else decision.reason,
        )
        self.audit.append(audit_entry)

        if not decision.allowed:
            return {
                "ok": False,
                "result": decision.result,
                "denial_code": decision.denial_code,
                "reason": decision.reason,
                "audit_id": audit_entry.id,
            }

        tx_hash = make_tx_hash()
        payment = {
            "payment_id": "pay-%s" % tx_hash[2:10],
            "invoice_id": request["invoice_id"],
            "merchant_id": request["merchant_id"],
            "pay_to": request["pay_to"],
            "amount_usdc": request["amount_usdc"],
            "chain_id": request["chain_id"],
            "token_id": request["token_id"],
            "principal_id": pact["principal_id"],
            "wallet_id": pact["wallet_id"],
            "tx_hash": tx_hash,
            "created_at": iso(utcnow()),
            "status": "settled",
            "audit_id": audit_entry.id,
            "pact_id": pact["pact_id"],
            "policy_names": decision.policy_names,
        }
        self.payments.upsert_by_invoice(payment)
        return {"ok": True, "payment": payment, "payment_payload": self._payment_payload(payment, pact, request)}

    def _payment_payload(
        self,
        payment: Dict[str, Any],
        pact: Dict[str, Any],
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "x402Version": 2,
            "scheme": request.get("scheme", "exact"),
            "invoice_id": payment["invoice_id"],
            "payment_id": payment["payment_id"],
            "tx_hash": payment["tx_hash"],
            "status": payment["status"],
            "amount_usdc": payment["amount_usdc"],
            "chain_id": payment["chain_id"],
            "token_id": payment["token_id"],
            "pay_to": payment["pay_to"],
            "resource": request["resource"],
            "payer": {
                "principal_id": pact["principal_id"],
                "wallet_id": pact["wallet_id"],
            },
            "caw_authorization": {
                "pact_id": pact["pact_id"],
                "audit_id": payment["audit_id"],
                "policy_names": payment.get("policy_names", []),
            },
        }
