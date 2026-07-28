/* Your key is born HERE — on your device, in your browser, and it never leaves.
 *
 * The server refuses to mint identities on purpose: POST /identity/create answers 400 with
 * "identity keys are created on your device — never by the server." That is the covenant's own
 * rule (a key the server generated was never only yours). This module is the other half of that
 * refusal: the part that actually gives you a key.
 *
 * Wire-compatible with src/concordance/signing.py by construction:
 *   public_key / private_key = base64url of the RAW 32 bytes, unpadded  (Ed25519PublicKey
 *   .from_public_bytes / Ed25519PrivateKey.from_private_bytes read exactly that)
 *   sign(bytes) -> base64url of the raw 64-byte signature, which verify_bytes() checks.
 *
 *   NHKeys.create()                  -> {public_key, private_key} | null   (null: no Ed25519 here)
 *   NHKeys.sign(privB64u, bytes)     -> base64url signature | null
 *   NHKeys.signB64uBytes(priv, b64u) -> sign the canonical bytes GET /mesh/signable handed you
 *   NHKeys.available()               -> boolean
 *
 * Stdlib only — WebCrypto, no dependency, no network. Ed25519 in WebCrypto needs a current
 * Firefox / Safari / Chrome; when it is missing we say so plainly instead of quietly falling back
 * to something weaker, because a weaker signature that LOOKS the same is worse than none.
 */
(function (global) {
  "use strict";

  // ── base64url (unpadded), matching signing.py's _b64u_encode/_b64u_decode ──
  function b64u(bytes) {
    var s = "";
    for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function unb64u(s) {
    var t = String(s || "").replace(/-/g, "+").replace(/_/g, "/");
    while (t.length % 4) t += "=";
    var raw = atob(t), out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }

  // Ed25519 raw <-> PKCS#8 / SPKI. WebCrypto will not import raw private bytes, so we wrap them in
  // the one fixed DER prefix Ed25519 uses (RFC 8410) — constant, so no ASN.1 library is needed.
  var PKCS8_PREFIX = new Uint8Array([
    0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70,
    0x04, 0x22, 0x04, 0x20]);

  function pkcs8From(raw32) {
    var der = new Uint8Array(PKCS8_PREFIX.length + 32);
    der.set(PKCS8_PREFIX, 0);
    der.set(raw32, PKCS8_PREFIX.length);
    return der;
  }

  function available() {
    return !!(global.crypto && global.crypto.subtle && global.crypto.getRandomValues);
  }

  async function create() {
    if (!available()) return null;
    try {
      var pair = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
      // export raw 32-byte halves: the public via SPKI's trailing 32 bytes, the private via JWK "d"
      var spki = new Uint8Array(await crypto.subtle.exportKey("spki", pair.publicKey));
      var jwk = await crypto.subtle.exportKey("jwk", pair.privateKey);
      var priv = unb64u(jwk.d);
      if (priv.length !== 32 || spki.length < 32) return null;
      return { public_key: b64u(spki.slice(spki.length - 32)), private_key: b64u(priv) };
    } catch (e) { return null; }   // no Ed25519 in this browser — say so, never substitute
  }

  async function sign(privB64u, bytes) {
    if (!available()) return null;
    try {
      var key = await crypto.subtle.importKey(
        "pkcs8", pkcs8From(unb64u(privB64u)), { name: "Ed25519" }, false, ["sign"]);
      var sig = await crypto.subtle.sign({ name: "Ed25519" }, key, bytes);
      return b64u(new Uint8Array(sig));
    } catch (e) { return null; }
  }

  /* Sign exactly the canonical bytes the engine handed you (GET /mesh/signable ->
     canonical_b64u). Signing the server's own bytes is the point: you can recompute them
     yourself — sorted-key JSON — and the id you get back must match `would_be_id`. */
  async function signB64uBytes(privB64u, canonicalB64u) {
    return sign(privB64u, unb64u(canonicalB64u));
  }

  global.NHKeys = { create: create, sign: sign, signB64uBytes: signB64uBytes,
                    available: available, b64u: b64u, unb64u: unb64u };
})(window);
