"""Contact — the public form that delivers messages straight to the KEEP (the operator window).

No email: each submission is persisted to a durable inbox and surfaced, newest first, at the top of
the keep dashboard (keep.dashboard -> contact.recent). No address is shown on the page. Runnable
with pytest OR `python tests/test_contact.py`.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from concordance.web import contact          # noqa: E402
from concordance.web.api import dispatch      # noqa: E402
from concordance.config import EngineConfig   # noqa: E402

SEC = EngineConfig("secular")
_PAGE = (_ROOT / "site" / "contact.html").read_text(encoding="utf-8")


def _isolate() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="nh_contact_"))
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    return tmp


def test_a_message_is_received_and_persisted():
    tmp = _isolate()
    st, p = dispatch("POST", "/contact", {},
                     {"name": "Ada", "email": "ada@example.com", "subject": "Hi",
                      "message": "A real message."}, SEC)
    assert st == 200 and p.get("ok") is True, (st, p)
    inbox = tmp / "contact_inbox.jsonl"
    assert inbox.exists(), "the message must be persisted (the reliable path)"
    rec = json.loads(inbox.read_text(encoding="utf-8").splitlines()[-1])
    assert rec["message"] == "A real message." and rec["email"] == "ada@example.com"


def test_an_empty_message_is_refused():
    _isolate()
    st, p = dispatch("POST", "/contact", {}, {"name": "x", "message": "   "}, SEC)
    assert st == 400 and "error" in p, (st, p)


def test_the_honeypot_silently_drops_a_bot():
    _isolate()
    before = contact.inbox_count()
    st, p = dispatch("POST", "/contact", {}, {"message": "buy cheap pills", "website": "http://spam"}, SEC)
    assert st == 200 and p.get("ok") is True, "it must look accepted to the bot"
    assert contact.inbox_count() == before, "but nothing is stored — the honeypot dropped it"


def test_a_malformed_email_is_refused():
    _isolate()
    st, _ = dispatch("POST", "/contact", {}, {"email": "not-an-email", "message": "hi"}, SEC)
    assert st == 400


def test_messages_are_delivered_to_the_keep_newest_first():
    """"Straight to the keep": a submitted message surfaces via contact.recent() (what the operator
    window reads), newest first. No email path exists — the persisted inbox IS the delivery."""
    _isolate()
    dispatch("POST", "/contact", {}, {"name": "First", "message": "one"}, SEC)
    dispatch("POST", "/contact", {}, {"name": "Second", "message": "two"}, SEC)
    r = contact.recent(10)
    assert len(r) == 2 and r[0]["name"] == "Second" and r[1]["name"] == "First", r
    assert contact.inbox_count() == 2


def test_the_page_carries_no_address_only_the_endpoint():
    """The operator's decision: no address on the client. The page POSTs to /contact and carries no
    mailto: link — locked so a future edit cannot slip an address back onto the page."""
    assert "mailto:" not in _PAGE, "the contact page must not expose a mailto: link"
    assert "/contact" in _PAGE and 'method:"POST"' in _PAGE.replace(" ", "")


def test_no_real_destination_leaked_into_the_page():
    """Belt-and-suspenders: the only email-looking token allowed on the page is the input's
    placeholder (you@example.com). No other address — and never the me.com destination — appears."""
    found = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", _PAGE))
    assert found <= {"you@example.com"}, f"unexpected address(es) on the contact page: {found}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} contact tests passed — reaches the keeper, hides the address.")
