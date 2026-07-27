/* Covenant identity — the browser client. Derives the SAME Ed25519 keypair as src/concordance/
 * covenant.py, byte-for-byte, using only WebCrypto (no vendored crypto; CSP-safe; secure-context).
 * The verses (and any generated key) NEVER leave the device — only a public key / signature do.
 *
 *   NHCovenant.publicId(verses[, passphrase])  -> hex public key (the identity handle)
 *   NHCovenant.sign(verses, message[, pass])   -> hex Ed25519 signature over `message`
 *   NHCovenant.generate()                       -> {seedHex (BACK THIS UP), publicHex}  (full-entropy sovereign key)
 *   NHCovenant.fromSeedHex(hex)                 -> {publicHex, sign(message)}            (restore a sovereign key)
 */
(function (global) {
  "use strict";
  var SALT = new TextEncoder().encode("narrowhighway/covenant/v1");
  var ITER = 600000, MIN = 4;

  // The 66, in canonical order — the 1-based position is the ordinal used in derivation (must match
  // src/concordance/covenant.py::_BOOKS exactly).
  var BOOKS = [
    ["Genesis", ["gen","ge","gn"]], ["Exodus", ["ex","exo","exod"]], ["Leviticus", ["lev","le","lv"]],
    ["Numbers", ["num","nu","nm","nb"]], ["Deuteronomy", ["deut","dt","de"]], ["Joshua", ["josh","jos","jsh"]],
    ["Judges", ["judg","jdg","jg","jdgs"]], ["Ruth", ["rth","ru"]], ["1 Samuel", ["1sam","1sa","1sm","1s"]],
    ["2 Samuel", ["2sam","2sa","2sm","2s"]], ["1 Kings", ["1kings","1kgs","1ki","1kg"]],
    ["2 Kings", ["2kings","2kgs","2ki","2kg"]], ["1 Chronicles", ["1chron","1chr","1ch"]],
    ["2 Chronicles", ["2chron","2chr","2ch"]], ["Ezra", ["ezr","ez"]], ["Nehemiah", ["neh","ne"]],
    ["Esther", ["esth","est","es"]], ["Job", ["jb"]], ["Psalms", ["psalm","ps","psa","psm","pss"]],
    ["Proverbs", ["prov","pro","prv","pr"]], ["Ecclesiastes", ["eccl","ecc","ec","qoh"]],
    ["Song of Solomon", ["song","songofsongs","sos","so","canticles","cant"]], ["Isaiah", ["isa","is"]],
    ["Jeremiah", ["jer","je","jr"]], ["Lamentations", ["lam","la"]], ["Ezekiel", ["ezek","eze","ezk"]],
    ["Daniel", ["dan","da","dn"]], ["Hosea", ["hos","ho"]], ["Joel", ["joe","jl"]], ["Amos", ["am","amo"]],
    ["Obadiah", ["obad","ob"]], ["Jonah", ["jon","jnh"]], ["Micah", ["mic","mc"]], ["Nahum", ["nah","na"]],
    ["Habakkuk", ["hab","hb"]], ["Zephaniah", ["zeph","zep","zp"]], ["Haggai", ["hag","hg"]],
    ["Zechariah", ["zech","zec","zc"]], ["Malachi", ["mal","ml"]], ["Matthew", ["matt","mt","mat"]],
    ["Mark", ["mrk","mk","mr"]], ["Luke", ["luk","lk"]], ["John", ["jn","jhn","joh"]], ["Acts", ["act","ac"]],
    ["Romans", ["rom","ro","rm"]], ["1 Corinthians", ["1cor","1co","1c"]], ["2 Corinthians", ["2cor","2co","2c"]],
    ["Galatians", ["gal","ga"]], ["Ephesians", ["eph","ephes"]], ["Philippians", ["phil","php","pp"]],
    ["Colossians", ["col","co"]], ["1 Thessalonians", ["1thess","1thes","1th"]],
    ["2 Thessalonians", ["2thess","2thes","2th"]], ["1 Timothy", ["1tim","1ti","1tm"]],
    ["2 Timothy", ["2tim","2ti","2tm"]], ["Titus", ["tit","ti"]], ["Philemon", ["philem","phm","pm"]],
    ["Hebrews", ["heb","hb"]], ["James", ["jas","jm","ja"]], ["1 Peter", ["1pet","1pe","1pt","1p"]],
    ["2 Peter", ["2pet","2pe","2pt","2p"]], ["1 John", ["1john","1jn","1jo","1j"]],
    ["2 John", ["2john","2jn","2jo","2j"]], ["3 John", ["3john","3jn","3jo","3j"]], ["Jude", ["jud","jd"]],
    ["Revelation", ["rev","re","rv","apocalypse","apoc"]]
  ];
  var ALIAS = {};
  BOOKS.forEach(function (b, i) {
    [b[0].toLowerCase().replace(/ /g, "")].concat(b[1]).forEach(function (f) {
      ALIAS[f.toLowerCase().replace(/\s+/g, "")] = i + 1;
    });
  });
  var REF = /^\s*([0-9]?\s*[A-Za-z][A-Za-z ]*?)\s*(\d{1,3})\s*(?:[:.\s]\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?)?\s*$/;

  function canonical(ref) {
    var m = REF.exec(ref || "");
    if (!m) throw new Error("not a verse reference: " + ref);
    var num = ALIAS[m[1].toLowerCase().replace(/\s+/g, "")];
    if (!num) throw new Error("unknown book: " + m[1]);
    var out = num + " " + parseInt(m[2], 10);
    if (m[3]) { out += ":" + parseInt(m[3], 10); if (m[4]) out += "-" + parseInt(m[4], 10); }
    return out;
  }

  function material(verses, passphrase) {
    var set = [];
    (verses || []).forEach(function (v) { var c = canonical(v); if (set.indexOf(c) < 0) set.push(c); });
    set.sort();
    if (set.length < MIN) throw new Error("need at least " + MIN + " distinct verses (got " + set.length + ")");
    return new TextEncoder().encode(set.join("\n") + "\x00" + (passphrase || ""));
  }

  function toHex(a) { return Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join(""); }
  function b64urlToBytes(s) {
    s = s.replace(/-/g, "+").replace(/_/g, "/"); while (s.length % 4) s += "=";
    var bin = atob(s), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }
  var PKCS8 = new Uint8Array([0x30,0x2e,0x02,0x01,0x00,0x30,0x05,0x06,0x03,0x2b,0x65,0x70,0x04,0x22,0x04,0x20]);

  async function seedFrom(bytes) {
    var base = await crypto.subtle.importKey("raw", bytes, "PBKDF2", false, ["deriveBits"]);
    var bits = await crypto.subtle.deriveBits({ name: "PBKDF2", salt: SALT, iterations: ITER, hash: "SHA-256" }, base, 256);
    return new Uint8Array(bits);
  }
  async function keypairFromSeed(seed) {
    var der = new Uint8Array(PKCS8.length + 32); der.set(PKCS8); der.set(seed, PKCS8.length);
    var priv = await crypto.subtle.importKey("pkcs8", der, { name: "Ed25519" }, true, ["sign"]);
    var jwk = await crypto.subtle.exportKey("jwk", priv);
    return { priv: priv, publicHex: toHex(b64urlToBytes(jwk.x)) };
  }
  async function signWith(priv, message) {
    var sig = await crypto.subtle.sign({ name: "Ed25519" }, priv, new TextEncoder().encode(message || ""));
    return toHex(new Uint8Array(sig));
  }

  async function publicId(verses, passphrase) { return (await keypairFromSeed(await seedFrom(material(verses, passphrase)))).publicHex; }
  async function sign(verses, message, passphrase) {
    var kp = await keypairFromSeed(await seedFrom(material(verses, passphrase)));
    return signWith(kp.priv, message);
  }
  async function generate() {
    var seed = crypto.getRandomValues(new Uint8Array(32)), kp = await keypairFromSeed(seed);
    return { seedHex: toHex(seed), publicHex: kp.publicHex };   // seedHex is the backup — guard it
  }
  async function fromSeedHex(hex) {
    var seed = new Uint8Array(hex.match(/.{2}/g).map(function (h) { return parseInt(h, 16); }));
    var kp = await keypairFromSeed(seed);
    return { publicHex: kp.publicHex, sign: function (m) { return signWith(kp.priv, m); } };
  }

  global.NHCovenant = { canonical: canonical, publicId: publicId, sign: sign, generate: generate, fromSeedHex: fromSeedHex };
})(window);
