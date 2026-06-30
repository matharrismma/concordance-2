# The Gateway — private in, verified out

Put Narrow Highway's two distinctives in front of *any* AI you already use:

- **Private** — strip personal context to stable placeholders before text is sent, reapply it
  after. The data stays on your side.
- **Verified** — turn a claim into a re-checkable receipt (verdict + worked trail + sealed hash).

It runs **at your edge** — in the browser, in your server process, or on a local/sovereign
engine. For privacy that means: *we never have to see your data.* The deterministic layer
(emails, SSNs, cards, IPs, URLs) is stdlib/vanilla and offline; the optional Rampart model
adds names + phone numbers in the browser.

---

## Browser (vanilla JS, zero build)
```html
<script src="https://narrowhighway.org/redact.js"></script>
<script>
  // wrap any LLM/API call: the model never sees the personal details; you get them back
  const ask = Rampart.guard(async (clean) => {
    const r = await fetch("https://some-llm.example/v1/chat", {
      method: "POST", body: JSON.stringify({ prompt: clean })
    });
    return (await r.json()).text;
  });
  const answer = await ask("email Dr. Sarah Johnson at sarah.j@clinic.org");
  // the LLM saw "[GIVEN_NAME_1] [SURNAME_1] … [EMAIL_1]"; `answer` has the real values restored
</script>
```
Add `rampart-ml.js` + the import map (see `index.html`) to also catch names/phones via the
self-hosted Rampart model.

## Server (Python, stdlib)
```python
from concordance.gateway import scrub, restore, guard

clean, mapping = scrub("email me at a@b.com")   # ("email me at [EMAIL_1]", {...})
reply = my_llm(clean)                            # the model never sees the email
final = restore(reply, mapping)                  # reapply locally

safe_llm = guard(my_llm)                          # …or wrap it once
final = safe_llm("email me at a@b.com")           # scrub-in, restore-out
```

## Agents (MCP)
The engine exposes a `redact` tool (alongside `verify`, `search`, `seal_fetch`):
```json
{ "name": "redact", "arguments": { "text": "ssn 123-45-6789 and a@b.com" } }
// -> { "clean": "ssn [SSN_1] and [EMAIL_1]", "mapping": {…}, "count": 2 }
```
You hold the mapping and reveal replies locally. **For true privacy, point your agent at a
LOCAL/sovereign engine** (`python -m concordance mcp`) so the text never leaves your machine —
or use the client libraries above. A hosted engine processes the text transiently and stores
nothing, but the strip is most honest at your edge.

---

## The verified half — hand back a receipt
```bash
curl -s -X POST https://narrowhighway.org/verify -H content-type:application/json \
  -d '{"mode":"equality","params":{"expr_a":"2+2","expr_b":"4","variables":{}}}'
# -> { "verdict":"HOLDS", "trail":[…], "seal":{ "content_hash":"…", "cite_url":"…/seal?hash=…" } }
```
The `cite_url` is permanent and re-checkable — proof, not "trust me." (Claim text is itself
redacted before it's sealed, so the receipt never carries PII.)

## What this is not
The engine **finds and verifies**; it does not generate answers, and it is not a replacement
for real help or professional advice. It is a window, not a wall — a conduit, not the source.
