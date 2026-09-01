# SOP · Steward (money)

**Purpose.** Steward helps a person MANAGE money — it never moves it. It does the honest, deterministic
arithmetic of a household (a budget, a savings rate, cost destroyed = money you did NOT spend) and hands
back a receipt: the engine's math moat applied to your own money. Buying, selling, transferring, paying,
investing stay YOUR action, always.

**Wiring.** Modules: `steward` · `ledger`. Surfaces: `GET /steward` (guidance), `POST /steward/budget`
(sealed into a receipt via `derivation`+`receipts`), `POST /steward/cost-destroyed`, `POST /steward/ask`
(the free-text boundary), and `site/steward.html` (the Steward door). `steward` is pure stdlib
arithmetic; the endpoint seals the budget through the same floor (`ledger.seal_record`) every verdict uses.

## Canary — is it up?
Confirm the identity line and the boundary, in one call each:
```
curl -s https://narrowhighway.com/steward | python -c "import sys,json;d=json.load(sys.stdin);print(d['identity']);print(len(d['does']),'does',len(d['will_not']),'will_not')"
# expect: "Steward — helps you manage your money; it never moves it."  + 3 does + 2 will_not
curl -s -X POST https://narrowhighway.com/steward/ask -H 'content-type: application/json' \
  -d '{"text":"wire money to this account"}' | python -c "import sys,json;print(json.load(sys.stdin)['kind'])"
# expect: move_declined  (the request is refused and handed back to the person)
```
If both pass, Steward is connected AND the money-move boundary is live.

## Operate
No operator action in normal use — a person drives it. `budget(income, expenses)` returns income, total,
net, savings rate, and by-category; the `/steward/budget` endpoint then seals the math in exact integer
cents as a re-checkable receipt. `cost_destroyed(items)` sums money not spent (`was → now`). `guidance()`
states what it does and will not do. **SAFETY:** `money_guardrail(text)` runs on every free-text ask —
a request to buy/sell/transfer/pay/deposit/invest returns `move_declined` with a "do it yourself" pointer;
a request for personalized investment advice returns `advice_declined` (not a licensed advisor). Steward
has NO transact code path at all — refusing is structural, not a filter.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A money-move or advice ask returns normal guidance instead of a refusal | `money_guardrail` not consulted on the path | Every free-text entry must call `steward.money_guardrail(text)` first (see `/steward/ask`) — the guardrail is the boundary |
| `/steward/budget` 500s or emits `Infinity`/`NaN` | a non-finite income (e.g. `"1"+"0"*400`) | Already guarded: `steward._num` rejects non-finite at the one conversion point — confirm the caller routes through it |
| `budget` crashes on `{"expenses": 123}` | a truthy non-list slips past `expenses or []` | Guarded by the `isinstance(expenses, list)` check in `budget`/`cost_destroyed` — keep it |
| Budget returns but carries no `seal` | `derivation`/`receipts` unreachable at seal time | The math still stands (pure); check the floor is importable — the seal is the receipt layer, not the arithmetic |

## Tests
`tests/test_steward.py`, `tests/test_ledger.py` — run
`PYTHONPATH=src python -m pytest tests/test_steward.py tests/test_ledger.py -q` (9 pass in test_steward).
They prove the budget/cost-destroyed math, the non-finite + non-list guards, the sealed-receipt endpoint,
the hard money-move/advice guardrail, and the ledger's tamper-evident hash chain.

## Known issues & support
- **Concierge / swipe-fee model is future work** — supported (a plan exists, not a live gap). The buy-for-you,
  warranty, and receipts flow is designed (loss-leaders + stewardship-of-value: free core, concierge earns
  the swipe fee) but not built. The boundary holds regardless: the engine STEWARDS the swipe, it never
  executes it — the human authorizes every move. (Mirrors the register in `systems.py`: `supported: True`.)

## Refine
Seal `cost_destroyed` into a receipt too — today only `/steward/budget` attaches a `seal`, so "money you
did not spend" is shown but not yet re-checkable. Attach the same `receipts` seal to `/steward/cost-destroyed`,
so every figure Steward returns carries its own proof.
