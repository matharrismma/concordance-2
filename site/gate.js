/* NHGate — the Gate, client side.

   The witness (Scripture, the words, the signposts) opens as the person's own conversation
   turns toward it (Ask/Seek/Knock, Matthew 7:7). On the secular reach a witness request
   returns { gate: "closed" } until that has happened; a page shows the invitation instead of
   a dead end. Once the gate is open (a server-set session flag), the same requests succeed and
   the Word is surfaced in place. We present the path; we never cross it. */
(function () {
  var shown = false;

  // Replace the page's main content with the invitation to open the gate.
  function invite() {
    if (shown) return;
    shown = true;
    var main = document.querySelector('main.wrap') || document.querySelector('main') || document.body;
    var gold = 'color:#c9a24a', serif = 'font-family:Georgia,"Times New Roman",serif';
    main.innerHTML =
      '<div style="max-width:40rem;margin:3rem auto;' + serif + '">' +
        '<div style="' + gold + ';letter-spacing:.34em;text-transform:uppercase;font-size:.68rem">Ask · Seek · Knock</div>' +
        '<h1 style="font-weight:400;font-size:2rem;margin:.6rem 0 .6rem">The Word opens as you seek it</h1>' +
        '<p style="opacity:.8;font-size:1.05rem;line-height:1.75">This is the witness — the Scripture, the ' +
          'original words, the signposts that point to Christ. It opens as your own conversation turns toward ' +
          'it. Ask about God or Scripture, and the way opens; from then on it stays with you.</p>' +
        '<p style="margin:1.8rem 0"><a href="/ask.html" style="' + gold + ';text-decoration:none;border:1px solid ' +
          'rgba(201,162,74,.4);padding:.6rem 1.2rem;border-radius:3px;letter-spacing:.08em">Open the conversation →</a></p>' +
        '<p style="opacity:.55;font-size:.9rem;line-height:1.7;margin-top:2.2rem">Matthew 7:7 — “Ask, and it ' +
          'will be given you. Seek, and you will find. Knock, and it will be opened for you.”</p>' +
      '</div>';
  }

  // True (and shows the invitation) when a fetched Response is a closed gate.
  async function isClosed(resp) {
    if (!resp || resp.status !== 404) return false;
    try {
      var b = await resp.clone().json();
      if (b && b.gate === 'closed') { invite(); return true; }
    } catch (e) {}
    return false;
  }

  window.NHGate = { invite: invite, isClosed: isClosed };
})();
