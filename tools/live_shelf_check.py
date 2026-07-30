"""THE COMMONS · C1b — the shelf flow walked against the LIVE box, over HTTPS.

Not a unit test, and not a substitute for one. `tests/test_shelves_surface.py` proves the handlers;
this proves the deployed server. A key born on this device, a signature made on this device, bytes
the SERVER minted, and the server's own answers read back — because "correct in the repo" has
never been the same claim as "true on the box".

Two things this deliberately does NOT do:

  * it does not promote anything into the commons — that is a human steward's act, not a probe's;
  * it does not leave its droppings in the live steward queue. Every card it makes is withdrawn at
    the end, which removes it from the views and KEEPS the act with its reason. Nothing is deleted.

    python tools/live_shelf_check.py [https://host]

Exit code is the verdict: 0 all held, 1 something failed.
"""
import base64
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import signing  # noqa: E402

BASE = (sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://narrowhighway.com")


def get(path, **q):
    url = f"{BASE}{path}"
    if q:
        url += "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=45) as r:
        return r.status, json.loads(r.read())


def _sign(signable_b64u, priv_key):
    """Sign the exact bytes the SERVER minted, here on this device. The key never travels."""
    return signing.sign_bytes(base64.urlsafe_b64decode(signable_b64u), priv_key)


def post(path, body):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(),
                                headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def mcp(name, args):
    req = urllib.request.Request(
        f"{BASE}/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": name, "arguments": args}}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read().decode()
    if raw.startswith("event:") or "\ndata: " in raw:
        raw = [ln[6:] for ln in raw.splitlines() if ln.startswith("data: ")][0]
    d = json.loads(raw)
    assert "error" not in d, d["error"]
    return json.loads(d["result"]["content"][0]["text"])


ok = []
bad = []


def check(label, cond, detail=""):
    (ok if cond else bad).append(label)
    print(("  PASS  " if cond else "  FAIL  ") + label + (f"   {detail}" if detail else ""))


priv, pub = signing.generate_keypair()
print(f"key born on this device — public {pub[:16]}…\n")

# 1 · the server mints the bytes, this device signs them
st, sg = get("/drop/signable", member=pub, kind="recipe", subject="Cold-proofed sourdough",
             body="Feed the starter twelve hours ahead. The cold proof is what opens the crumb — "
                  "warm-proofed dough rises faster and bakes tight.", ring="shelf")
check("GET /drop/signable answers with bytes to sign", st == 200 and sg.get("ok"), str(sg)[:120])
sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)

# 2 · stock the shelf
st, r = post("/drop", {"fields": sg["fields"], "signature": sig, "display_name": "Matt Harris"})
check("POST /drop stocks the shelf", st == 200 and r.get("ok"), str(r)[:160])
card_id = r.get("card_id", "")

# 3 · read it back
st, view = get("/shelf", member=pub)
card = (view.get("cards") or [{}])[0]
check("GET /shelf serves it to anyone", st == 200 and view.get("count") == 1, str(view)[:120])
check("the words carry the member's name", "Matt Harris" in json.dumps(card.get("source", {})))
check("authority stays at member tier", card.get("source", {}).get("authority_tier") == "member")

# 4 · a forged signature is refused at the live door
_p2, pub2 = signing.generate_keypair()
_st, sg2 = get("/drop/signable", member=pub2, kind="note", subject="not mine",
               body="Words attributed to someone who never wrote a line of them.")
st, forged = post("/drop", {"fields": sg2["fields"],
                            "signature": signing.sign_bytes(
                                base64.urlsafe_b64decode(sg2["signable"]), priv)})
check("a forged signature is refused (400 + reason)",
      st == 400 and "does not verify" in forged.get("error", ""), str(forged)[:140])
check("the forged drop never landed", get("/shelf", member=pub2)[1].get("count") == 0)

# 5 · no private key on the wire, live
st, keyed = post("/drop", {"fields": dict(sg["fields"], private_key=priv), "signature": "x" * 40})
check("the live door refuses a private key",
      st >= 400 and "private key" in keyed.get("error", "").lower(), str(keyed)[:140])

# 6 · a commons drop waits for a human
_st, sg3 = get("/drop/signable", member=pub, kind="writing", subject="Why the shelf is a key",
               body="An account is a leash. A key is a hand you keep. This is why the library "
                    "never asks who you are.", ring="commons")
_st, held = post("/drop", {"fields": sg3["fields"],
                           "signature": signing.sign_bytes(
                               base64.urlsafe_b64decode(sg3["signable"]), priv),
                           "display_name": "Matt Harris"})
check("a commons drop lands in public_review", held.get("stage") == "public_review", str(held)[:140])
before = get("/commons")[1].get("count", -1)
q = get("/curate/queue")[1]
check("it waits in the steward queue",
      any(i.get("card_id") == held.get("card_id") for i in q.get("items", [])), str(q)[:140])

# 7 · the agent door sees the same store.
# NOTE the count: a stranger's view holds ONE card, not two — the commons drop from step 6 is
# awaiting a steward and is correctly withheld, surfacing only as `awaiting_review`. The first
# draft of this check asserted >= 2 and "failed"; the system was right and the expectation was
# wrong. Check the check.
a_view = mcp("shelf_read", {"member": pub})
check("MCP shelf_read sees what HTTP wrote",
      a_view.get("count") == 1 and a_view.get("awaiting_review") == 1, str(a_view)[:140])
a_q = mcp("curate_queue", {})
check("MCP curate_queue sees the held drop",
      any(i.get("card_id") == held.get("card_id") for i in a_q.get("items", [])))
a_sg = mcp("shelf_signable", {"member": pub, "kind": "field_note",
                              "subject": "Reading a creek for a crossing",
                              "body": "Cross at the wide shallow riffle, never the smooth narrow "
                                      "part — smooth water means deep and fast."})
a_r = mcp("shelf_drop", {"fields": a_sg["fields"],
                         "signature": signing.sign_bytes(
                             base64.urlsafe_b64decode(a_sg["signable"]), priv),
                         "display_name": "Matt Harris"})
check("MCP shelf_drop stocks a shelf through an agent", a_r.get("ok") is True, str(a_r)[:160])
check("and HTTP sees the agent's card", get("/shelf", member=pub)[1].get("count") == 2,
      "one store, two doors")
check("MCP shelf_drop refuses a smuggled key",
      "private key" in str(mcp("shelf_drop", {"fields": dict(a_sg["fields"], private_key=priv),
                                              "signature": "x" * 40}).get("error", "")).lower())

# 8 · llms.txt tells an agent the Commons exists
with urllib.request.urlopen(f"{BASE}/llms.txt", timeout=45) as rr:
    llms = rr.read().decode("utf-8", "ignore")
check("llms.txt documents the Commons",
      "/drop/signable" in llms and "authority_tier: member" in llms)

# 9 · A TYPED NAME IS NOT AUTHORITY. Promoting decides what the whole library amplifies, so it
# needs the steward token — which this probe deliberately does not hold. It must be refused live.
st, bare = post("/curate", {"card_id": held.get("card_id"), "action": "promoted",
                            "steward": "matt", "reason": "trying it without the token"})
check("promoting without the steward token is refused 403",
      st == 403 and "not authorized" in bare.get("error", ""), str(bare)[:140])
check("and nothing was amplified", get("/commons")[1].get("count") == before)

# 10 · leave the box clean — by the MEMBER's own signature, which is the whole point: a member
# never needs anyone's permission to take their own words down. A verification drop left sitting in
# the real steward queue would be a live instrument reporting work nobody asked for. Withdrawing is
# the honest exit: the card leaves the views and the act stays in the record WITH ITS REASON.
for cid in (card_id, held.get("card_id"), a_r.get("card_id")):
    if not cid:
        continue
    st, sg_w = get("/curate/signable", card_id=cid, member=pub)
    if not sg_w.get("ok"):
        print(f"  cleanup {cid[-8:]}: could not prepare — {sg_w.get('error')}")
        continue
    w = post("/curate", {"card_id": cid, "action": "withdrawn", "steward": "the member",
                         "reason": "C1c live verification artifact — withdrawn after the check",
                         "fields": sg_w["fields"],
                         "signature": _sign(sg_w["signable"], priv)})
    print(f"  cleanup withdrawn {cid[-8:]}: ok={w[1].get('ok')} by={w[1].get('by')}")
check("a member withdraws their own cards with their own key",
      get("/shelf", member=pub)[1].get("count") == 0)
check("the steward queue is left clean", get("/curate/queue")[1].get("count") == 0)

print(f"\n  {len(ok)} passed, {len(bad)} failed"
      f"{'' if not bad else ' — ' + ', '.join(bad)}")
print(f"  commons count before any steward acts: {before} (must be 0 for a fresh commons drop)")
print(f"  held card awaiting a human: {held.get('card_id')}")
print(f"  test cards left on the box for this key: {get('/shelf', member=pub)[1].get('count')}")
sys.exit(1 if bad else 0)
