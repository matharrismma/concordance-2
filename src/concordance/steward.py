"""Steward — helps a person MANAGE their money. It never moves it.

The third of the triad: Scribe keeps (the Deck/Journal), Shepherd guides (the conduit), Steward
stewards. Steward does the honest, verifiable arithmetic of a household — a budget, a savings rate,
and COST DESTROYED (money you did NOT spend) — and hands you a receipt (the engine's math moat
applied to your own money).

HARD BOUNDARY (load-bearing): Steward SHOWS and PLANS; it does NOT and WILL NOT move money — no
buying, selling, transferring, paying, depositing, withdrawing, trading, or investing. Those stay
YOUR action. And it gives NO personalized investment advice (it is not a licensed advisor); on those
it points you to act yourself or to a real professional. Value is returned as cost destroyed — money
kept in your currency, not metered by us. Kill rent, not profit.

Sovereign stdlib; deterministic; conduit — it computes and shows, it does not decide for you.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Language that would MOVE money — Steward refuses and points the action back to the person.
_MOVE_WORDS = (
    "buy", "sell", "transfer", "wire", "invest", "trade", "purchase", "send money", "withdraw",
    "deposit", "checkout", "check out", "place an order", "venmo", "paypal", "zelle", "cash app",
    "brokerage", "make a payment", "pay my", "pay the", "move my money", "spend on",
)
# Requests for personalized investment ADVICE — Steward declines (not a licensed advisor).
_ADVICE_WORDS = (
    "should i invest", "should i buy", "good investment", "which stock", "what stock",
    "what should i buy", "pick stocks", "stock pick", "portfolio", "get rich", "double my money",
    "hot tip", "financial advice", "investment advice", "should i sell", "is it a good time to buy",
)

_MOVE_MSG = ("Steward helps you SEE and plan your money — it never moves it. Buying, selling, "
             "transferring, paying, depositing, or investing stays your own action. What I can do: "
             "build a budget, compute your savings rate, and show cost destroyed — with a receipt.")
_ADVICE_MSG = ("I'm not a licensed financial advisor, so I won't give personalized investment "
               "advice — for that, talk to a real professional you trust. What I can do is the "
               "honest arithmetic: a budget, a savings rate, and cost destroyed.")


def money_guardrail(text: str) -> Optional[Dict[str, Any]]:
    """Return a refusal+pointer if the request would move money or asks for investment advice;
    None otherwise. The boundary, enforced — Steward stewards, it does not transact."""
    t = " " + (text or "").lower() + " "
    if any(w in t for w in _ADVICE_WORDS):
        return {"kind": "advice_declined", "message": _ADVICE_MSG,
                "do_yourself": "Consult a licensed financial professional for personalized advice."}
    if any(w in t for w in _MOVE_WORDS):
        return {"kind": "move_declined", "message": _MOVE_MSG,
                "do_yourself": "Move money yourself, in your own bank/app — Steward will never do it for you."}
    return None


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return round(float(x), 2)
    except (TypeError, ValueError):
        return default


def budget(income: Any, expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Deterministic household budget: income, total expenses, net, savings rate, by category.
    Pure arithmetic — the endpoint seals it into a receipt."""
    inc = _num(income)
    items: List[Dict[str, Any]] = []
    for e in (expenses or []):
        if not isinstance(e, dict):
            continue
        amt = _num(e.get("amount"))
        items.append({"label": str(e.get("label", "")), "amount": amt,
                      "category": str(e.get("category") or "other").lower()})
    total = round(sum(i["amount"] for i in items), 2)
    net = round(inc - total, 2)
    by_cat: Dict[str, float] = {}
    for i in items:
        by_cat[i["category"]] = round(by_cat.get(i["category"], 0.0) + i["amount"], 2)
    return {
        "income": inc, "total_expenses": total, "net": net,
        "savings_rate_pct": round(net / inc * 100, 1) if inc > 0 else 0.0,
        "by_category": by_cat, "expenses": items,
        "note": "Steward shows and plans; it never moves your money.",
    }


def cost_destroyed(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Cost destroyed = money you did NOT spend (was → now). The value we return is money KEPT in
    your currency — kill rent, not profit."""
    out: List[Dict[str, Any]] = []
    total = 0.0
    for it in (items or []):
        if not isinstance(it, dict):
            continue
        was, now = _num(it.get("was")), _num(it.get("now"))
        saved = round(was - now, 2)
        total += saved
        out.append({"label": str(it.get("label", "")), "was": was, "now": now, "saved": saved})
    return {"items": out, "total_saved": round(total, 2),
            "note": "Cost destroyed is money not spent — kept in your currency, not metered by us."}


def guidance() -> Dict[str, Any]:
    """What Steward does, and the boundary it will not cross."""
    return {
        "identity": "Steward — helps you manage your money; it never moves it.",
        "does": [
            "build a budget — income, expenses, net, savings rate, by category",
            "show cost destroyed — money you did NOT spend, kept in your currency",
            "hand you a receipt — the arithmetic, verified and re-checkable",
        ],
        "will_not": [
            "move money — buy, sell, transfer, pay, deposit, withdraw, invest (that stays your action)",
            "give personalized investment advice (it is not a licensed advisor — see a professional)",
        ],
        "note": "Value returned as cost destroyed. Kill rent, not profit. A conduit, not your banker.",
    }


__all__ = ["money_guardrail", "budget", "cost_destroyed", "guidance"]
