/*! Narrow Highway — embeddable verification widget.
 *
 * For any app that generates text (an AI draft, a report, a page of copy): call NarrowHighway.embed()
 * with the text and a mount element. It POSTs to /audit — the SAME deterministic engine this whole
 * site runs on — which extracts every unambiguously checkable claim (sums, percentages, pay, interest,
 * dates...), verifies each one, and returns ONE sealed coverage report. This renders that report as a
 * small, honest trust badge: how many claims were checked, how many held, a link to the permanent
 * receipt (/s/<hash>) anyone can re-verify without trusting this widget or this site.
 *
 * Nothing is generated here and nothing is invented: a claim this engine cannot check is reported as
 * NOT checked, never silently passed. Free, no key, no account — CORS-open (see /llms.txt).
 *
 * Usage:
 *   <script src="https://narrowhighway.com/widget.js"></script>
 *   <div id="mount"></div>
 *   <script>
 *     NarrowHighway.embed(theGeneratedText, document.getElementById('mount'));
 *   </script>
 *
 * Or without a mount point, to read the raw report yourself:
 *   const report = await NarrowHighway.check(text);
 */
(function (root) {
  "use strict";

  var API = "https://narrowhighway.com";
  var STYLE_ID = "nh-verify-style";
  var CSS =
    ".nh-verify{all:initial;display:block;font:13px/1.45 -apple-system,\"Segoe UI\",Roboto,sans-serif;" +
    "max-width:360px;border:1px solid #d8dee5;border-radius:10px;padding:.8rem .95rem;" +
    "background:#fafcfd;color:#1b2430}" +
    ".nh-verify *{box-sizing:border-box;font:inherit;color:inherit}" +
    ".nh-verify a{color:#0c6b5f;text-decoration:none}" +
    ".nh-verify a:hover{text-decoration:underline}" +
    ".nh-verify .nh-head{display:flex;align-items:center;gap:.4rem;font-weight:600;margin-bottom:.35rem}" +
    ".nh-verify .nh-dot{width:8px;height:8px;border-radius:50%;flex:none;background:#0c6b5f}" +
    ".nh-verify .nh-dot.warn{background:#b0472b}" +
    ".nh-verify .nh-dot.slate{background:#5f6b78}" +
    ".nh-verify .nh-line{color:#48545f;margin:.15rem 0}" +
    ".nh-verify .nh-foot{margin-top:.5rem;padding-top:.45rem;border-top:1px dashed #d8dee5;" +
    "font-size:.72rem;color:#7c8894}";

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /** Call POST /audit and return the raw sealed coverage report. Never throws for a 4xx/5xx —
   * returns {error: "..."} instead, so a caller's page never breaks because this widget failed. */
  function check(text) {
    return fetch(API + "/audit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: String(text || "") }),
    })
      .then(function (r) {
        return r.json();
      })
      .catch(function (e) {
        return { error: String((e && e.message) || e) };
      });
  }

  /** Build the badge DOM node from an /audit report. Pure — does not mount or fetch anything. */
  function render(report) {
    var wrap = document.createElement("div");
    wrap.className = "nh-verify";
    injectStyle();

    if (!report || report.error) {
      wrap.innerHTML =
        '<div class="nh-line">Verification unavailable right now.</div>' +
        '<div class="nh-foot">narrowhighway.com — a deterministic verification engine</div>';
      return wrap;
    }
    var found = report.claims_found || 0;
    if (!found) {
      wrap.innerHTML =
        '<div class="nh-head"><span class="nh-dot slate"></span>No checkable claim found</div>' +
        '<div class="nh-line">Nothing here matched a pattern this engine can check deterministically ' +
        "(a sum, a percentage, pay, interest, a date…). That is a report about the ENGINE, not the text.</div>" +
        '<div class="nh-foot"><a href="' + API + '" target="_blank" rel="noopener">narrowhighway.com</a>' +
        " — a deterministic verification engine</div>";
      return wrap;
    }
    var held = report.held || 0,
      broken = report.broken || 0,
      unchecked = report.unchecked || 0;
    var dotClass = broken > 0 ? "warn" : "";
    var summary =
      found +
      " claim" +
      (found === 1 ? "" : "s") +
      " checked — " +
      held +
      " held" +
      (broken ? ", " + broken + " broken" : "") +
      (unchecked ? ", " + unchecked + " not checkable" : "");
    var receiptUrl = report.seal && (report.seal.cite_url || report.seal.permanent_ref);
    var receipt = receiptUrl
      ? '<a href="' + esc(receiptUrl) + '" target="_blank" rel="noopener">the permanent receipt →</a>'
      : "not sealed";
    wrap.innerHTML =
      '<div class="nh-head"><span class="nh-dot ' +
      dotClass +
      '"></span>Verified by Narrow Highway</div>' +
      '<div class="nh-line">' +
      esc(summary) +
      "</div>" +
      '<div class="nh-line">' +
      receipt +
      " — re-checkable without trusting this widget.</div>" +
      '<div class="nh-foot">A conduit, not a source · nothing is generated · ' +
      '<a href="' +
      API +
      '" target="_blank" rel="noopener">narrowhighway.com</a></div>';
    return wrap;
  }

  /** The one-call convenience: check(text) then render it into mountEl (appended, not replacing
   * mountEl's other children, so a caller can place it anywhere in an existing layout). Returns the
   * report and the rendered node via a Promise, so a caller can also react to the verdict itself. */
  function embed(text, mountEl) {
    return check(text).then(function (report) {
      var node = render(report);
      if (mountEl && mountEl.appendChild) mountEl.appendChild(node);
      return { report: report, node: node };
    });
  }

  root.NarrowHighway = { check: check, render: render, embed: embed, API: API };
})(typeof window !== "undefined" ? window : this);
