# x402 + Cobo CAW minimal paywall demo

This repo runs a local, auditable x402-style payment loop:

1. A provider exposes `GET /paywalled/risk-report`.
2. The first request returns HTTP `402` with a Base64 JSON `PAYMENT-REQUIRED` header.
3. `agent_client.py` decodes the x402 requirement and asks the local CAW adapter to settle.
4. The CAW adapter evaluates the active Pact policy, budget, receiver allowlist, token allowlist, and time/usage window.
5. If allowed, it writes an auditable settlement record with a mock tx hash.
6. The agent retries the original request with `PAYMENT-SIGNATURE`.
7. The provider verifies the settlement and returns the report with `PAYMENT-RESPONSE`.

The CAW layer in this demo is a local adapter in `app/mock_caw.py`. It is intentionally shaped like CAW Pact policy enforcement, but it does not move real funds. To use a live CAW wallet, replace `/caw/settle` with the real CAW CLI/API call and keep the x402 request/retry contract unchanged.

## Run

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the provider and CAW adapter:

```bash
uvicorn app.server:app --reload
```

Run the autonomous agent:

```bash
python agent_client.py
```

Use another service URL when `8000` is busy:

```bash
python agent_client.py --base-url http://127.0.0.1:8001
```

Observe an over-budget denial:

```bash
python deny_example.py
```

Inspect local audit artifacts:

```bash
curl http://127.0.0.1:8000/caw/audit
curl http://127.0.0.1:8000/caw/payments
```

Reset the demo state:

```bash
curl -X POST http://127.0.0.1:8000/caw/reset
```

## Important endpoints

- `GET /paywalled/risk-report?address=...&chain=base`: protected paid API.
- `GET /caw/pact`: active Pact with policies and completion conditions.
- `POST /caw/settle`: local CAW settlement adapter.
- `GET /caw/audit`: policy and settlement audit log.
- `GET /caw/payments`: settlement records.

## Demo policy

The default Pact allows only:

- chain: `BASE_ETH`
- token: `BASE_USDC`
- merchant: `merchant-risk-api`
- receiver: `merchant-risk-api`
- resource prefix: `risk-report:`
- max single transfer before denial: `1.20` USD
- human review threshold: more than `1.00` USD
- rolling 24h budget: `5.00` USD or 5 payments
- total Pact completion: 5 payments, 5 USD, or 24 hours
