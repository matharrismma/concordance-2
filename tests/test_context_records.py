"""The records format (tools/context.py): the parser for docs/harness/RULES.md and BACKLOG.md, the
pointer grammar, the scan, and the private configuration directory it reads.

Every input here is an invented fixture: no real rule, want, repository or name. The private names
are nonsense words, the paths and addresses are made up (the IP addresses come from the ranges kept
for documentation), and the configuration directory is always a temporary one. A failing assertion
prints counts, never a path, because the harness writes failing test ids into the public ledger.
"""
import json
import os
import subprocess
import sys

import pytest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
sys.path.insert(0, TOOLS)
import context as cx  # noqa: E402
import harness as h  # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"
RUN = "2026-01-02-invented-run"


def _cfg(tmp_path, names=None, patterns=None):
    """A Config read through the override from a fresh temporary directory (files only if given)."""
    d = tmp_path / "cfg"
    d.mkdir(exist_ok=True)
    if names is not None:
        (d / "private_names.txt").write_text(names, encoding="utf-8")
    if patterns is not None:
        (d / "secret_patterns.txt").write_text(patterns, encoding="utf-8")
    return cx.load_config({"HARNESS_CONFIG_DIR": str(d)})


# ------------------------------------------------------------------------------- the pointer grammar

GOOD_POINTERS = {
    "LEDGER": f"LEDGER concordance-2 {RUN} 7",
    "FILE": f'FILE witness docs/INVENTED.md {SHA} "an anchor with "inner" quotes"',
    "ORIGIN": "ORIGIN 2026-01-02 lead",
    "OWNER": 'OWNER owner, chat, 2026-01-02 "invented words, quoted"',
}


def test_each_pointer_kind_parses_into_its_fields_and_renders_back_byte_for_byte():
    p = cx.parse_pointer(GOOD_POINTERS["LEDGER"])
    assert (p.kind, p.repo, p.run, p.line) == ("LEDGER", "concordance-2", RUN, 7)
    f = cx.parse_pointer(GOOD_POINTERS["FILE"])
    assert (f.kind, f.repo, f.path, f.sha, f.anchor) == \
        ("FILE", "witness", "docs/INVENTED.md", SHA, 'an anchor with "inner" quotes')
    o = cx.parse_pointer(GOOD_POINTERS["ORIGIN"])
    assert (o.kind, o.date, o.who) == ("ORIGIN", "2026-01-02", "lead")
    w = cx.parse_pointer(GOOD_POINTERS["OWNER"])
    assert (w.kind, w.date, w.words) == ("OWNER", "2026-01-02", "invented words, quoted")
    for kind, text in GOOD_POINTERS.items():
        assert cx.parse_pointer(text).kind == kind
        assert cx.parse_pointer(text).render() == text
    for repo in cx.PUBLIC_REPOS:
        assert cx.parse_pointer(f"LEDGER {repo} {RUN} 1").repo == repo
    for who in ("owner", "lead", "builder-3", "checker-12"):
        assert cx.parse_pointer(f"ORIGIN 2026-01-02 {who}").who == who


def test_owner_and_origin_pointers_are_unresolvable_by_kind():
    got = {k: cx.parse_pointer(t).resolvable for k, t in GOOD_POINTERS.items()}
    assert got == {"LEDGER": True, "FILE": True, "ORIGIN": False, "OWNER": False}


BAD_POINTERS = [
    ("file-path-colon-line", "FILE concordance-2 docs/INVENTED.md:12"),
    ("file-path-colon-line-with-sha-and-anchor", f'FILE concordance-2 docs/INVENTED.md:12 {SHA} "anchor"'),
    ("file-short-sha", 'FILE concordance-2 docs/INVENTED.md 0123456 "anchor"'),
    ("file-uppercase-sha", f'FILE concordance-2 docs/INVENTED.md {SHA.upper()} "anchor"'),
    ("file-no-anchor", f"FILE concordance-2 docs/INVENTED.md {SHA}"),
    ("file-empty-anchor", f'FILE concordance-2 docs/INVENTED.md {SHA} ""'),
    ("file-blank-anchor", f'FILE concordance-2 docs/INVENTED.md {SHA} "   "'),
    ("file-unquoted-anchor", f"FILE concordance-2 docs/INVENTED.md {SHA} anchor"),
    ("file-leading-slash", f'FILE concordance-2 /docs/INVENTED.md {SHA} "anchor"'),
    ("file-parent-segment", f'FILE concordance-2 docs/../INVENTED.md {SHA} "anchor"'),
    ("file-dot-segment", f'FILE concordance-2 ./docs/INVENTED.md {SHA} "anchor"'),
    ("file-empty-segment", f'FILE concordance-2 docs//INVENTED.md {SHA} "anchor"'),
    ("file-backslash", f'FILE concordance-2 docs\\INVENTED.md {SHA} "anchor"'),
    ("ledger-timestamp", f"LEDGER concordance-2 {RUN} 2026-01-02T10:00:00+00:00"),
    ("ledger-line-zero", f"LEDGER concordance-2 {RUN} 0"),
    ("ledger-leading-zero", f"LEDGER concordance-2 {RUN} 07"),
    ("ledger-missing-line", f"LEDGER concordance-2 {RUN}"),
    ("ledger-bad-run-id", "LEDGER concordance-2 Invented_Run 7"),
    ("repo-without-a-public-remote", f"LEDGER zorblax-notes {RUN} 7"),
    ("repo-wrong-case", f"LEDGER Concordance-2 {RUN} 7"),
    ("origin-impossible-date", "ORIGIN 2026-02-30 lead"),
    ("origin-short-date", "ORIGIN 26-01-02 lead"),
    ("origin-unknown-filer", "ORIGIN 2026-01-02 someone"),
    ("origin-no-filer", "ORIGIN 2026-01-02"),
    ("owner-other-channel", 'OWNER owner, email, 2026-01-02 "words"'),
    ("owner-other-speaker", 'OWNER lead, chat, 2026-01-02 "words"'),
    ("owner-unquoted-words", "OWNER owner, chat, 2026-01-02 words"),
    ("owner-empty-words", 'OWNER owner, chat, 2026-01-02 ""'),
    ("owner-impossible-date", 'OWNER owner, chat, 2026-13-01 "words"'),
    ("lowercase-kind", f"ledger concordance-2 {RUN} 7"),
    ("unknown-kind", "URL https://example.invalid/x"),
    ("double-space", f"LEDGER  concordance-2 {RUN} 7"),
    ("trailing-text", "ORIGIN 2026-01-02 lead and more"),
    ("trailing-newline", "ORIGIN 2026-01-02 lead\n"),
    ("empty", ""),
]


@pytest.mark.parametrize("text", [t for _, t in BAD_POINTERS], ids=[i for i, _ in BAD_POINTERS])
def test_a_malformed_pointer_is_refused(text):
    with pytest.raises(cx.RecordsError):
        cx.parse_pointer(text)


def test_a_file_pointer_by_line_number_is_refused_by_name():
    with pytest.raises(cx.RecordsError, match="never path:line"):
        cx.parse_pointer(f'FILE concordance-2 docs/INVENTED.md:12 {SHA} "anchor"')
    with pytest.raises(cx.RecordsError, match="never a timestamp"):
        cx.parse_pointer(f"LEDGER concordance-2 {RUN} 2026-01-02T10:00:00+00:00")


def test_a_refusal_never_echoes_the_record():
    with pytest.raises(cx.RecordsError) as e:
        cx.parse_pointer(f"LEDGER zorblax-notes {RUN} 7")
    assert "zorblax" not in str(e.value)
    with pytest.raises(cx.RecordsError) as e:
        cx.parse_rules(MIN_RULE.replace("scope: all", "scope: zorblax-notes") + "- zorblax: x\n")
    assert "zorblax" not in str(e.value)


# ------------------------------------------------------------------------- RULES.md and BACKLOG.md

RULES = f"""# Standing rules (an invented fixture)

Prose before the first entry is the preamble; the parser keeps none of it.

## keep-the-lamp-lit
- scope: all
- source: OWNER owner, chat, 2026-01-02 "keep the lamp lit"
- check: the lamp is lit when the checker looks

> Keep the lamp lit.

## two-part-rule
- check: both parts hold
- scope: witness
- source: FILE witness docs/INVENTED.md {SHA} "First part of the rule."
> First part of the rule.
>
> Second part, after an empty line.
"""

BACKLOG = f"""# Backlog (an invented fixture)

## mend-the-gate
- status: open
- scope: concordance-2
- source: LEDGER concordance-2 {RUN} 3
> Mend the gate before the frost.

## sweep-the-porch
- status: refused
- scope: all
- source: ORIGIN 2026-01-03 lead
> Sweep the porch.
"""


def test_a_rules_entry_carries_its_id_scope_verbatim_text_source_and_check():
    rules = cx.parse_rules(RULES)
    assert [r.id for r in rules] == ["keep-the-lamp-lit", "two-part-rule"]
    a, b = rules
    assert (a.scope, a.text, a.check) == ("all", "Keep the lamp lit.", "the lamp is lit when the checker looks")
    assert a.source == cx.parse_pointer('OWNER owner, chat, 2026-01-02 "keep the lamp lit"')
    assert (b.scope, b.check) == ("witness", "both parts hold")
    assert b.text == "First part of the rule.\n\nSecond part, after an empty line."
    assert (b.source.kind, b.source.anchor) == ("FILE", "First part of the rule.")
    assert (a.line, b.line) == (5, 12)
    assert cx.parse_rules("") == [] and cx.parse_rules("# Only a preamble\n\nNo entry yet.\n") == []


def test_a_backlog_entry_carries_its_id_status_scope_text_and_source():
    wants = cx.parse_backlog(BACKLOG)
    assert [(w.id, w.status, w.scope) for w in wants] == \
        [("mend-the-gate", "open", "concordance-2"), ("sweep-the-porch", "refused", "all")]
    assert wants[0].text == "Mend the gate before the frost."
    assert wants[0].source == cx.parse_pointer(f"LEDGER concordance-2 {RUN} 3")
    assert wants[1].source.kind == "ORIGIN"
    assert cx.STATUSES == ("open", "filed-as-run", "done", "refused")
    for status in cx.STATUSES:
        assert cx.parse_backlog(MIN_WANT.replace("status: open", f"status: {status}"))[0].status == status


def test_parsing_is_unchanged_by_line_endings_and_a_byte_order_mark():
    for text, parse in ((RULES, cx.parse_rules), (BACKLOG, cx.parse_backlog)):
        lf = parse(text)
        for other in (text.replace("\n", "\r\n"), text.replace("\n", "\r"), "\ufeff" + text):
            again = parse(other)
            assert again == lf
            assert [e.line for e in again] == [e.line for e in lf]


MIN_RULE = f"""## a-rule
- scope: all
- source: LEDGER concordance-2 {RUN} 7
- check: it holds
> The words.
"""

MIN_WANT = f"""## a-want
- status: open
- scope: all
- source: LEDGER concordance-2 {RUN} 7
> The want.
"""

BAD_RULES = [
    ("missing-scope", MIN_RULE.replace("- scope: all\n", "")),
    ("missing-source", MIN_RULE.replace(f"- source: LEDGER concordance-2 {RUN} 7\n", "")),
    ("missing-check", MIN_RULE.replace("- check: it holds\n", "")),
    ("missing-text", MIN_RULE.replace("> The words.\n", "")),
    ("duplicate-field", MIN_RULE.replace("- check: it holds\n", "- check: it holds\n- check: again\n")),
    ("unknown-field", MIN_RULE + "- note: extra\n"),
    ("status-in-a-rule", MIN_RULE + "- status: open\n"),
    ("empty-field", MIN_RULE.replace("- check: it holds", "- check:")),
    ("field-without-space", MIN_RULE.replace("- check: it holds", "- check:it holds")),
    ("scope-without-a-public-remote", MIN_RULE.replace("scope: all", "scope: zorblax-notes")),
    ("scope-of-two-repos", MIN_RULE.replace("scope: all", "scope: witness, concordance-2")),
    ("origin-source-in-a-rule", MIN_RULE.replace(f"LEDGER concordance-2 {RUN} 7", "ORIGIN 2026-01-02 lead")),
    ("malformed-source", MIN_RULE.replace(f"LEDGER concordance-2 {RUN} 7", f"LEDGER concordance-2 {RUN}")),
    ("duplicate-id", MIN_RULE + "\n" + MIN_RULE),
    ("uppercase-id", MIN_RULE.replace("## a-rule", "## A-Rule")),
    ("id-with-spaces", MIN_RULE.replace("## a-rule", "## a rule")),
    ("empty-id", MIN_RULE.replace("## a-rule", "## ")),
    ("heading-without-space", MIN_RULE.replace("## a-rule", "##a-rule")),
    ("deeper-heading-inside", MIN_RULE + "### an aside\n"),
    ("title-inside", MIN_RULE + "# a title\n"),
    ("prose-inside-an-entry", MIN_RULE + "Some prose.\n"),
    ("text-split-in-two", MIN_RULE + "\n> More words.\n"),
    ("text-after-a-field", MIN_RULE.replace("- check: it holds\n", "") + "- check: it holds\n> More words.\n"),
    ("text-starts-empty", MIN_RULE.replace("> The words.\n", ">\n> The words.\n")),
    ("text-ends-empty", MIN_RULE.replace("> The words.\n", "> The words.\n>\n")),
    ("text-only-empty", MIN_RULE.replace("> The words.\n", ">\n")),
    ("text-without-space", MIN_RULE.replace("> The words.", ">The words.")),
]


@pytest.mark.parametrize("text", [t for _, t in BAD_RULES], ids=[i for i, _ in BAD_RULES])
def test_a_malformed_rules_entry_is_refused(text):
    assert cx.parse_rules(MIN_RULE)[0].id == "a-rule"           # the fixture itself parses
    with pytest.raises(cx.RecordsError):
        cx.parse_rules(text)


BAD_WANTS = [
    ("status-outside-the-set", MIN_WANT.replace("status: open", "status: wontfix")),
    ("missing-status", MIN_WANT.replace("- status: open\n", "")),
    ("owner-source-in-a-want", MIN_WANT.replace(f"LEDGER concordance-2 {RUN} 7", 'OWNER owner, chat, 2026-01-02 "w"')),
    ("check-in-a-want", MIN_WANT + "- check: it holds\n"),
    ("duplicate-id", MIN_WANT + "\n" + MIN_WANT),
]


@pytest.mark.parametrize("text", [t for _, t in BAD_WANTS], ids=[i for i, _ in BAD_WANTS])
def test_a_malformed_backlog_entry_is_refused(text):
    assert cx.parse_backlog(MIN_WANT)[0].id == "a-want"
    with pytest.raises(cx.RecordsError):
        cx.parse_backlog(text)


# An entry under a wrong heading sits in the preamble; it must be refused there, never skipped.
HIDDEN = [
    ("rules-entry-under-a-one-hash-heading", cx.parse_rules,
     RULES.replace("## keep-the-lamp-lit", "# keep-the-lamp-lit"), [6, 7, 8, 10], "lamp"),
    ("backlog-entry-under-a-one-hash-heading", cx.parse_backlog,
     BACKLOG.replace("## mend-the-gate", "# mend-the-gate"), [4, 5, 6, 7], "frost"),
    ("indented-field-in-the-preamble", cx.parse_rules,
     "# A title\n  - scope: zorblax-notes\n\n" + MIN_RULE, [2], "zorblax"),
    ("text-in-the-preamble", cx.parse_backlog,
     "# A title\n> A zorblax want with no heading.\n\n" + MIN_WANT, [2], "zorblax"),
]


@pytest.mark.parametrize("parse,text,lines,word", [(p, t, n, w) for _, p, t, n, w in HIDDEN],
                         ids=[i for i, *_ in HIDDEN])
def test_an_entry_body_before_the_first_heading_is_refused_never_skipped(parse, text, lines, word):
    with pytest.raises(cx.RecordsError) as e:
        parse(text)
    assert [p.split(":")[0] for p in e.value.problems] == [f"line {n}" for n in lines]
    assert word not in str(e.value).lower()


def test_a_prose_preamble_still_parses():
    pre = "# A title\n\nSome prose: with a colon.\n- note: a list item\n- a plain list item\n\n"
    assert [r.id for r in cx.parse_rules(pre + MIN_RULE)] == ["a-rule"]
    assert [w.id for w in cx.parse_backlog(pre + MIN_WANT)] == ["a-want"]


def test_a_refusal_names_every_bad_line():
    second = MIN_RULE.replace("## a-rule", "## b-rule").replace("scope: all", "scope: x")
    text = MIN_RULE + "Some prose.\n" + "\n" + second
    with pytest.raises(cx.RecordsError) as e:
        cx.parse_rules(text)
    assert "line 6:" in str(e.value) and "line 9:" in str(e.value)


# ------------------------------------------------------------------------------------------ the scan

FLAGGED = [
    ("drive-letter-backslash", "kept in C:\\Work\\notes.txt", "an absolute path"),
    ("drive-letter-slash", "kept in d:/work/notes.txt", "an absolute path"),
    ("git-bash-drive", "kept in /c/Work/notes.txt", "an absolute path"),
    ("home", "kept in /home/someone/notes", "an absolute path"),
    ("users", "kept in /Users/someone/notes", "an absolute path"),
    ("tmp", "written to /tmp/scratch/x", "an absolute path"),
    ("quoted-home", 'cwd="/home/someone"', "an absolute path"),
    ("ipv4", "served on 192.0.2.10:8080", "an IP address"),
    ("ipv4-loopback", "bound to 127.0.0.1.", "an IP address"),
    ("ipv6", "served on 2001:db8::7", "an IP address"),
    ("email", "write to someone@example.invalid", "an e-mail address"),
    ("ssh-default-key", "the key in id_ed25519", "an ssh key file name"),
    ("ssh-public-half", "copy id_rsa.pub across", "an ssh key file name"),
    ("ssh-pem", "load deploy-key.pem first", "an ssh key file name"),
    ("ssh-ppk", "load laptop.ppk first", "an ssh key file name"),
]


@pytest.mark.parametrize("text,kind", [(t, k) for _, t, k in FLAGGED], ids=[i for i, _, _ in FLAGGED])
def test_the_scan_names_the_line_and_the_kind_of_each_hit(tmp_path, text, kind):
    assert cx.scan("a clean first line\n" + text + "\na clean last line\n", _cfg(tmp_path)) == [(2, kind)]


CLEAN = """See https://github.com/someone/witness/blob/master/docs/x.md and docs/home/notes.md.
The configuration lives in ~/.config/harness/secret_patterns.txt, beside tools/harness.py:142.
Opened 2026-11-03T14:00:11+00:00 at 93b4446, version 3.0.0a0, ratio 1:2:3, section 4.2.1.
A run 2026-11-03-assemble-reapply, a step records-format, the identity of a rule, a .pem file.
std::vector and a[::-1] and key:value and ./tmp/x and https://example.invalid/tmp/x and @types/node
"""


def test_the_scan_passes_ordinary_record_text():
    cfg = cx.load_config({"HARNESS_CONFIG_DIR": ""})
    assert cx.scan(CLEAN, cfg) == []


def test_an_octet_over_255_is_not_an_ip_address(tmp_path):
    cfg = _cfg(tmp_path)
    assert cx.scan("not an address: 10.0.0.256\n", cfg) == []
    assert cx.scan("an address: 10.0.0.255\n", cfg) == [(1, "an IP address")]


def test_every_word_in_the_private_names_file_is_a_hit_and_never_echoed(tmp_path):
    cfg = _cfg(tmp_path, names="# invented private names\n\nzorblax-notes\nQuill Feather\n")
    assert cfg.private_names == ("zorblax-notes", "Quill", "Feather")
    text = ("line one\nsee ZORBLAX-NOTES today\nthe quill\nfeather pen\n"
            "zorblax-notesy is another word\nunder_zorblax-notes_dir\n")
    hits = cx.scan(text, cfg)
    assert hits == [(2, "a private name"), (3, "a private name"), (4, "a private name"), (6, "a private name")]
    assert all(w not in repr(hits).lower() for w in ("zorblax", "quill", "feather"))


def test_the_scan_carries_the_harness_secret_patterns_and_the_directory_s_own(tmp_path):
    cfg = _cfg(tmp_path, patterns="# a comment\nzq-[0-9]{4}\n")
    key = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
    assert cx.scan("clean\n" + key + "\ntoken zq-1234\n", cfg) == \
        [(2, "a private key block"), (3, "a locally-declared private pattern")]


def test_the_scan_can_be_narrowed_to_the_private_names_and_secrets(tmp_path):
    cfg = _cfg(tmp_path, names="zorblax\n")
    text = "kept in /home/someone/x\na zorblax here\nbound to 127.0.0.1\n"
    assert cx.scan(text, cfg) == [(1, "an absolute path"), (2, "a private name"), (3, "an IP address")]
    assert cx.scan(text, cfg, kinds=("private-name", "secret")) == [(2, "a private name")]
    with pytest.raises(ValueError):
        cx.scan(text, cfg, kinds=("nonsense",))


# ----------------------------------------------------------------- the private configuration directory

def _plant(root):
    """A configuration directory under `root` whose words would hit if it were ever read."""
    d = root / ".config" / "harness"
    d.mkdir(parents=True)
    (d / "private_names.txt").write_text("plantedname\n", encoding="utf-8")
    (d / "secret_patterns.txt").write_text("planted-[0-9]+\n", encoding="utf-8")
    return d


def test_the_directory_is_the_override_when_set_else_home_and_works_without_files(monkeypatch, tmp_path):
    home = tmp_path / "home"
    planted = _plant(home)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("HARNESS_CONFIG_DIR", raising=False)
    assert cx.config_dir() == str(planted)
    assert cx.scan("a plantedname\nplanted-7\n", cx.load_config()) == \
        [(1, "a private name"), (2, "a locally-declared private pattern")]
    monkeypatch.setenv("HARNESS_CONFIG_DIR", str(tmp_path / "absent"))
    assert cx.config_dir() == str(tmp_path / "absent")
    cfg = cx.load_config()
    assert cfg.private_names == () and len(cfg.secret_patterns) == len(h.SECRET_PATTERNS)
    assert cx.scan("a plantedname\nplanted-7\n", cfg) == []
    monkeypatch.setenv("HARNESS_CONFIG_DIR", "")          # set but empty: no directory at all, no fallback
    assert cx.config_dir() is None
    assert cx.scan("a plantedname\nplanted-7\n", cx.load_config()) == []


# Runs in a child process: records every path the process opens or lists from the moment the hook
# is in (Python's audit events), then loads the configuration and scans stdin.
_PROBE = r"""
import json, os, sys
seen = []
def _hook(event, args):
    if event in ("open", "os.listdir", "os.scandir") and args:
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)):
            seen.append(os.path.abspath(os.fsdecode(p)))
sys.addaudithook(_hook)
sys.path.insert(0, sys.argv[1])
import context
cfg = context.load_config()
hits = context.scan(sys.stdin.buffer.read().decode("utf-8"), cfg)
sys.stdout.write(json.dumps({"seen": seen, "hits": hits, "dir": cfg.dir}))
"""


def _under(path, root):
    path, root = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root))
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def test_with_the_override_set_the_real_directory_is_never_opened(tmp_path):
    real = os.path.join(os.path.expanduser("~"), ".config", "harness")   # this machine's, where it may exist
    home = tmp_path / "home"
    planted = _plant(home)                                                 # a stand-in that surely exists
    cfg = tmp_path / "cfg"
    cfg.mkdir()
    (cfg / "private_names.txt").write_text("zorblax\n", encoding="utf-8")
    (cfg / "secret_patterns.txt").write_text("zq-[0-9]{4}\n", encoding="utf-8")
    env = dict(os.environ)
    env.update({"HOME": str(home), "USERPROFILE": str(home), "HARNESS_CONFIG_DIR": str(cfg),
                "HARNESS_SECRET_PATTERNS": str(cfg / "secret_patterns.txt")})
    r = subprocess.run([sys.executable, "-I", "-B", "-c", _PROBE, TOOLS], cwd=str(tmp_path), env=env,
                       input="a zorblax\na plantedname\na zq-1234\na planted-99\n".encode("utf-8"),
                       capture_output=True, timeout=300)
    last = (r.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
    assert r.returncode == 0, "the probe failed: " + last.split(":")[0][:80]     # the exception's name only
    out = json.loads(r.stdout.decode("utf-8"))
    seen = out["seen"]
    n_real = sum(_under(p, real) for p in seen)
    n_planted = sum(_under(p, str(planted)) for p in seen)
    read = sorted(os.path.basename(p) for p in seen if _under(p, str(cfg)))
    assert n_real == 0, "the real configuration directory was opened"
    assert n_planted == 0, "the home configuration directory was opened under the override"
    assert read == ["private_names.txt", "secret_patterns.txt"]           # the hook saw the reads it should
    assert [tuple(x) for x in out["hits"]] == [(1, "a private name"), (3, "a locally-declared private pattern")]
    assert out["dir"] == str(cfg)
