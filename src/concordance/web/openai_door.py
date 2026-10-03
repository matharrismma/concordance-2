"""THE OPENAI-COMPATIBLE DOOR — Narrow Highway answered through the shape every chat client already speaks.

Matt, 2026-10-03: "we want to open every door. Every way we can connect and be a mechanism or layer to
interact with current offerings and add real value" — "Lean into the open doors."

A client that speaks the OpenAI chat shape (Open WebUI, LM Studio's remote providers, Continue, a phone
app, a shell script with `openai` installed) points its base URL at narrowhighway.com and asks for the
model "narrow-highway". There is NO MODEL behind this door: the last user message goes through the same
front door a person walks through (ask.respond — crisis first, then the classifier), and the reply is
COMPOSED from the answer's own found text: the message, the lead card's own words with its source, the
Scripture it carries verbatim, the resources, the path's one step, and the seal. Nothing is generated;
the structured answer rides along under `narrow_highway` so an agent can read the verdict, the seal and
the house ending directly. `generated: false` is carried on every reply.

Pure module: render(answer) and completion(...) take dicts and return dicts; the route in api.py does the
HTTP. Streaming (SSE) is one chunk carrying the whole reply, then [DONE] — honest, since nothing here is
produced token by token."""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

MODEL = "narrow-highway"
MODELS = [{"id": MODEL, "object": "model", "created": 1718000000, "owned_by": "narrowhighway.com",
           "note": "no model: a deterministic engine that finds, verifies, cites and seals — never generates"}]


def last_user_text(messages: Any) -> str:
    """The last user turn's text, from the OpenAI messages list (string content or content parts)."""
    if not isinstance(messages, list):
        return ""
    for m in reversed(messages):
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            return c.strip()
        if isinstance(c, list):                      # content parts: [{type: "text", text: ...}, ...]
            parts = [str(p.get("text") or "") for p in c if isinstance(p, dict) and p.get("type") == "text"]
            return " ".join(x for x in parts if x).strip()
    return ""


def _line(label: str, text: Any) -> str:
    t = " ".join(str(text or "").split())
    return f"{label}: {t}" if label and t else t


def render(r: Dict[str, Any]) -> str:
    """The reply, composed only of the answer's own found text, in the order a person reads it."""
    out: List[str] = []
    kind = str(r.get("kind") or "")
    msg = str(r.get("message") or "").strip()
    if msg:
        out.append(msg)
    # a crisis: the resources ARE the answer — first, and nothing after them but the door
    if kind == "crisis":
        for x in r.get("resources") or []:
            if isinstance(x, dict) and x.get("label"):
                out.append(f"• {x['label']}")
        return "\n".join(out)
    # a verdict (CHECK): the verdict, the worked trail, the seal
    if r.get("verdict"):
        out.append(f"Verdict: {r['verdict']}")
        for s in (r.get("trail") or [])[:8]:
            if isinstance(s, dict):
                out.append(f"  {s.get('id', '?')} · {s.get('status', '')} · {' '.join(str(s.get('detail') or '').split())[:300]}")
    # the lead card, in its own words, with its source
    lead = r.get("lead") if isinstance(r.get("lead"), dict) else None
    if lead and (lead.get("excerpt") or lead.get("title")):
        out.append("")
        out.append(f"{lead.get('title') or ''}".strip())
        if lead.get("excerpt"):
            out.append(str(lead["excerpt"]).strip())
        src = lead.get("source") if isinstance(lead.get("source"), dict) else {}
        if src.get("label") or src.get("url"):
            out.append(_line("Source", " ".join(x for x in (src.get("label"), src.get("url")) if x)))
    # Scripture the answer carries, verbatim
    for v in (r.get("scripture") or r.get("romans_road") or [])[:6]:
        if isinstance(v, dict) and v.get("ref") and v.get("text"):
            out.append(f"{v['ref']} — {str(v['text']).strip()}")
    # the other results, by title, so the reader can open them
    rest = [c for c in (r.get("results") or []) if isinstance(c, dict) and c.get("title")]
    if rest and not lead:
        out.append("")
        for c in rest[:5]:
            out.append(f"• {c['title']}" + (f" ({c.get('id')})" if c.get("id") else ""))
    # real help, resources, the path's one step, the seal
    for x in r.get("real_help") or []:
        out.append(f"• {x}")
    for x in r.get("resources") or []:
        if isinstance(x, dict) and x.get("label"):
            out.append(f"• {x['label']}" + (f" — {x['ref']}" if x.get("ref") else ""))
    p = r.get("path") if isinstance(r.get("path"), dict) else {}
    if p.get("step"):
        out.append("")
        out.append(_line("Next", p["step"]))
    seal = r.get("seal") if isinstance(r.get("seal"), dict) else {}
    cite = seal.get("cite_url") or r.get("receipt")
    if cite:
        out.append(_line("Seal", cite))
    h = r.get("house") if isinstance(r.get("house"), dict) else {}
    nxt = h.get("next_step") if isinstance(h.get("next_step"), dict) else {}
    if nxt.get("do") and nxt.get("do") != p.get("step"):
        out.append(_line("One step", nxt["do"]))
    text = "\n".join(x for x in out if x is not None).strip()
    return text or "Nothing found in the keeping for that, and nothing will be invented. Bring a claim, a word, a verse, or a situation."


def completion(answer: Dict[str, Any], *, model: str = MODEL, text: Optional[str] = None) -> Dict[str, Any]:
    """An OpenAI chat.completion object whose content is the rendered reply; the full structured answer
    rides under `narrow_highway`."""
    content = text if text is not None else render(answer)
    return {
        "id": f"chatcmpl-nh-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                  "note": "no model ran; nothing was generated — found, verified, cited, sealed"},
        "generated": False,
        "narrow_highway": answer,
    }


def sse_chunks(comp: Dict[str, Any]) -> List[str]:
    """The streaming form: one chunk with the whole reply, one with the finish reason, then [DONE]."""
    cid, created, model = comp["id"], comp["created"], comp["model"]
    content = comp["choices"][0]["message"]["content"]
    first = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
             "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}]}
    last = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "generated": False, "narrow_highway": comp.get("narrow_highway")}
    return [f"data: {json.dumps(first, ensure_ascii=False)}\n\n",
            f"data: {json.dumps(last, ensure_ascii=False)}\n\n",
            "data: [DONE]\n\n"]
