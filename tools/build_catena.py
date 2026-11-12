#!/usr/bin/env python3
"""THE CATENA AUREA BUILD: the Fathers on the Gospels, as the 1841-45 printing prints them, read by two copies.

    python tools/build_catena.py INPUTS OUTPUT fetch            the box: fetch the pinned layout files, build
    python tools/build_catena.py INPUTS OUTPUT fetch CACHE      the same, taking a file from CACHE when its sha256 is
                                                               the pinned one (a laptop run; the output is identical)

Run by tools/box_build.py from tools/box_builds.txt (run 2026-11-11-fathers-shelf, steps catena and catena2). INPUTS
is the read-only directory of its listed inputs at their repository paths: tools/catena_aurea/authors.json (who may
head an excerpt, and the editors' marks), golden.json (the excerpts read from the page images: the test of this
build), census.json (the volume parts, the two archive.org copies of each, and the pinned sha256 of each copy's ABBYY
layout file), gospel_verses.json (the engine's English verse numbers for every Gospel chapter, the chapters its
English and Latin number otherwise, and the pairs of verses the Latin divides otherwise) and misreadings.json (OCR
forms both copies of one typesetting have been seen to share). It reads no other repository file and touches the
network only for the named archive.org files, each refused unless its sha256 is the pinned one.

For each volume part, for each of its two copies, it parses the ABBYY file streaming (never whole; no external
entity or document type is resolved: expat is never asked to), and per page removes the furniture by its place:
the running head and page number at the top, the footnotes below the text (kept apart as the page's notes), the
margin column (kept apart as the citations beside the excerpts) and a signature line at the foot. The Gospel text is
set larger, so its lines stand further apart than the commentary's (GOSPEL_PITCH); a passage opens on a verse mark
('12.', or a group the printing sets together, '12—15.') or a chapter heading and runs on to the first head, and its
marks give the section after it its verse or range. An excerpt starts only at a head: a run of words the layout flags
as small capitals, naming a form the author table holds, followed by ';' or '.'. Its words are normalized
(whitespace; curly quotation marks to straight ones; a space before ; : , . ? ! removed) and line-end hyphens are
read by one rule: kept where only the hyphenated form occurs elsewhere in the part's text, joined where only the
joined form does, and otherwise the excerpt is held.

THE HOLDS (an excerpt is held, not served, where any applies). Those that catch what two copies of one typesetting
share: a lost hyphen (a line's last word and the next line's first word form a word found elsewhere in the part); a
fused margin word (a word's box crosses the text column's edge); the ligature ae (a word holding ae or its letter);
a character outside letters and the stated punctuation (a figure among them, '109th' as much as '1'), or a listed
misreading; a superscript that is not a footnote mark answered by a footnote on its page; an italic I dropped or misread (an italic run whose first word is
lower case, wherever it opens, or '/', '1', 'l' or 'J' standing before a word in lower case); an unflagged head (a
form the table holds, capitalized and followed by ';' or '.', read as a word); and a head broken across lines (a
line opening on a head after a line ending in '-', unless the two halves in small capitals make a form the table
holds). Those on the two copies: the head not at the same place (page and order) in both, a line-end hyphen neither
form settles, and the words not the same. And a line set at the Gospel's spacing that opens on a number inside an
excerpt (a verse whose mark neither copy read as one): the excerpt cannot be attributed with certainty.

THE VERSE. A section's verse or range is confirmed only where (1) both copies read it alike, (2) the running heads
allow it, (3) it begins at the verse after the end of the section before it in its chapter, as both copies read that
section, a chapter's first section at the chapter's first verse and its last ending at the chapter's last verse, the
verses read as gospel_verses.json lists them, and (4) it overlaps no neighbour; a section that fails any of these is
held. A section in a chapter the engine's English and Latin number otherwise is held (the chapter whole), and so is a
section whose first or last verse is either verse of a listed pair, since Aquinas groups the comments as the Vulgate
divides the text. Mark's CHRYS. is served with the editors' mark the author table quotes from the edition's preface.

THE GOLDEN (golden.json, read from the page images) checks every excerpt it holds: an excerpt is matched to the
golden entry on its leaf whose opening words are most like its own, whoever that entry names as the writer. It lifts
a hold on the words only where copy A, copy B and the golden read the same words, never a hold on a head, a verse or
a disagreement between the copies. Its citation is served where both copies' margin text beside the head agrees
after folding case, opens as a golden citation opens and stops before a Scripture reference, and is otherwise
'citation not confirmed'.

THE STATED PUNCTUATION: . , ; : ? ! ' " ( ) - and the dash U+2014; '&' only in '&c.'.

It exits non-zero, writing nothing, when a file's sha256 is not the pinned one (cached or fetched), when an excerpt
it would serve differs from its golden entry in words, writer or citation, when a golden excerpt's section is
confirmed and its verse differs from the golden's, or when a golden excerpt's opening words would be served inside
another writer's excerpt (its head missed). A verse the golden reads otherwise that is not confirmed is held and
reported. Its output is bytes with '\\n' line ends, sorted keys and no timestamps, so a run on any
machine with the same pinned inputs has the same content hash. Stdlib only.
"""
import collections
import difflib
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

NS = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
URL = 'https://archive.org/download/%s/%s_abbyy.gz'
CATENA = 'tools/catena_aurea/'
INPUTS = tuple(CATENA + n for n in ('authors.json', 'census.json', 'golden.json', 'gospel_verses.json',
                                     'misreadings.json'))
BOOKS = {'Matthew': 'MAT', 'Mark': 'MRK', 'Luke': 'LUK', 'John': 'JHN'}
CHAPTERS = {'Matthew': 28, 'Mark': 16, 'Luke': 24, 'John': 21}
ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
QUOTES = {'‘': "'", '’': "'", '‚': "'", '‛': "'", '“': '"', '”': '"', '„': '"',
          '`': "'", '´': "'"}
PUNCT_ATTACH = set(';:,.?!)]')
STATED = set(".,;:?!'\"()-—")
GOSPEL_PITCH = 1.06       # a line this much further from its neighbours than the page's usual pitch is Gospel text
FUSE = 12                  # pixels: a word reaching this far past the column edge is fused with the margin
HOLD_ORDER = ('head not at the same place', 'head broken across lines', 'chapter held whole', 'verse not confirmed',
              'chapter not confirmed', 'lost hyphen', 'fused margin word', 'ligature ae', 'character or misreading',
              'superscript not a footnote mark', 'italic I', 'unflagged head', 'line-end hyphen undecided',
              'words differ', 'author differs', 'verse not in the running head', 'verse out of order',
              'bounded at a listed pair', 'numbered Gospel line in the words')


class Refuse(Exception):
    """The build refuses: nothing is written."""


# --------------------------------------------------------------------------------------------- small helpers

def fold(s):
    for a, b in QUOTES.items():
        s = s.replace(a, b)
    return s


def key_of(name):
    """A head's comparison key: upper case, without spaces, hyphens, periods and its terminator."""
    return re.sub(r'[\s.\-;:,]', '', fold(name).upper())


def roman(s):
    s = s.strip('.').upper().replace('L', 'L')
    if not s or any(c not in ROMAN for c in s):
        return None
    v = 0
    for a, b in zip(s, s[1:] + ' '):
        v += -ROMAN[a] if b in ROMAN and ROMAN[b] > ROMAN[a] else ROMAN[a]
    return v


def render(words):
    s = ''
    for w in words:
        if not s:
            s = w
        elif w in PUNCT_ATTACH or (w[0] in PUNCT_ATTACH and len(w) <= 2):
            s += w
        else:
            s += ' ' + w
    s = re.sub(r'\s+([;:,.?!])', r'\1', s)
    return re.sub(r"(^|\s)(['\"])\s+(?=\w)", r'\1\2', s)


def tokens(s):
    return re.sub(r'\s+([;:,.?!])', r'\1', fold(s)).split()


def core(w):
    return re.sub(r"^[^\w]+|[^\w]+$", '', fold(w)).lower()


def first_letter(w):
    """A word's first letter as printed (its case kept), after any opening mark; '' where it has none."""
    m = re.search(r'[^\W\d_]', fold(w))
    return m.group(0) if m else ''


def jdump(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1, separators=(',', ': ')) + '\n').encode('utf-8')


# --------------------------------------------------------------------------------------------- inputs

def load_inputs(inputs):
    """The listed inputs (INPUTS, the paths tools/box_builds.txt lists) from the read-only INPUTS directory."""
    def j(name):
        assert CATENA + name in INPUTS
        with open(os.path.join(inputs, *(CATENA + name).split('/')), encoding='utf-8') as fh:
            return json.load(fh)
    authors, golden, census, mis = j('authors.json'), j('golden.json'), j('census.json'), j('misreadings.json')
    verses = j('gospel_verses.json')
    forms = {}
    for a in authors['authors']:
        for f in a['printed_forms']:
            forms[key_of(f['form'])] = a
    return authors, golden, census, mis, forms, verses


# --------------------------------------------------------------------------------------------- fetching

def fetch(ident, sha, cache, work):
    """The item's ABBYY file, by its pinned sha256: from CACHE where it holds the item, else from archive.org. A file
    whose sha256 is not the pinned one, cached or fetched, is a changed source, and the build refuses."""
    dst = os.path.join(work, ident + '_abbyy.gz')
    if cache:
        src = os.path.join(cache, ident, 'abbyy', 'abbyy.gz')
        if os.path.isfile(src):
            got = file_sha(src)
            if got != sha:
                raise Refuse('changed source: %s_abbyy.gz has sha256 %s, pinned %s' % (ident, got, sha))
            return src
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(URL % (ident, ident), headers={'User-Agent': 'catena-build/1.0'})
            h = hashlib.sha256()
            with urllib.request.urlopen(req, timeout=120) as r, open(dst, 'wb') as fh:
                while True:
                    b = r.read(1 << 16)
                    if not b:
                        break
                    h.update(b)
                    fh.write(b)
            got = h.hexdigest()
            if got != sha:
                raise Refuse('changed source: %s_abbyy.gz has sha256 %s, pinned %s' % (ident, got, sha))
            return dst
        except Refuse:
            raise
        except Exception as e:  # noqa: BLE001 - a dropped connection is tried again
            last = e
            time.sleep(5 * (attempt + 1))
    raise Refuse('could not fetch %s: %s' % (ident, last))


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------------------------------- ABBYY, streaming

def pages(path):
    """Yield one page at a time: (leaf, width, height, lines); a line is (l, t, r, b, words); a word is
    [text, l, r, flags, font size]. flags: s smallcaps, i italic, u superscript."""
    n = -1
    page = line = None
    cur = None
    fmt = ('', 0.0)
    root = None

    def flush():
        nonlocal cur
        if cur is not None and line is not None and cur[0]:
            line[4].append(cur)
        cur = None
    with gzip.open(path, 'rb') as fh:
        for ev, el in ET.iterparse(fh, events=('start', 'end')):
            tag = el.tag[len(NS):] if el.tag.startswith(NS) else el.tag
            if root is None:
                root = el
            if ev == 'start':
                if tag == 'page':
                    n += 1
                    page = [n, int(el.get('width', 0)), int(el.get('height', 0)), []]
                elif tag == 'block':
                    pass
                elif tag == 'line':
                    line = [int(el.get('l', 0)), int(el.get('t', 0)), int(el.get('r', 0)), int(el.get('b', 0)), []]
                elif tag == 'formatting':
                    flush()
                    f = ''
                    if el.get('smallcaps') == 'true':
                        f += 's'
                    if el.get('italic') == 'true':
                        f += 'i'
                    if el.get('superscript') == 'true':
                        f += 'u'
                    try:
                        fs = float(el.get('fs') or 0)
                    except ValueError:
                        fs = 0.0
                    fmt = (f, fs)
            else:
                if tag == 'charParams':
                    ch = el.text or ''
                    if ch.strip() == '':
                        flush()
                    else:
                        l, r = int(el.get('l', 0)), int(el.get('r', 0))
                        if cur is None:
                            cur = [ch, l, r, fmt[0], fmt[1]]
                        else:
                            cur[0] += ch
                            cur[2] = max(cur[2], r)
                    el.clear()
                elif tag == 'formatting':
                    flush()
                    el.clear()
                elif tag == 'line':
                    flush()
                    if line is not None and line[4] and page is not None:
                        page[3].append(line)
                    line = None
                    el.clear()
                elif tag == 'page':
                    yield page
                    page = None
                    el.clear()
                    root.clear()


# --------------------------------------------------------------------------------------------- one page's layout

HEAD_RE = re.compile(r'GOSPEL|ACCORDING|\bST\.|VER\.|CHAP\.')
SIG_RE = re.compile(r"^(VOL\.?\s*[IVXLivx1l]+\.?.*|[A-Z]{1,2}\s*\d?|\d{1,4})$")
CHAP_RE = re.compile(r'^CHA[P\^]?\.?\s*([IVXLCl]+)\.?$')


def chapter_numeral(m):
    """A chapter heading's roman numeral, reading a final 'L' as the 'I.' the OCR often mistakes it for."""
    if not m:
        return None
    t = m.group(1).replace('l', 'I').upper()
    v = roman(t)
    if t.endswith('L') and len(t) > 1:
        v = roman(t[:-1] + 'I')
    return v


def mode(values, step):
    c = collections.Counter(round(v / step) for v in values)
    return c.most_common(1)[0][0] * step if c else None


def layout(page):
    """A page's body lines, margin entries and footnotes, with the furniture removed by place."""
    n, pw, ph, lines = page
    lines = sorted(lines, key=lambda ln: (ln[1], ln[0]))
    rec = {'n': n, 'h': ph, 'num': None, 'rhead': '', 'lines': [], 'margin': [], 'foot': [], 'marks': []}
    if not lines:
        return rec
    first = ' '.join(w[0] for w in lines[0][4])
    if not CHAP_RE.match(first.strip()) and (HEAD_RE.search(first) or re.match(r'^\d+\s', first)
                                             or re.search(r'\s\d+$', first)):
        rec['rhead'] = first
        m = re.match(r'^(\d+)\s', first) or re.search(r'\s(\d+)$', first)
        if m:
            rec['num'] = int(m.group(1))
        lines = lines[1:]
    if not lines:
        return rec
    sizes = collections.Counter()
    for ln in lines:
        for w in ln[4]:
            sizes[w[4]] += len(w[0])
    body_fs = sizes.most_common(1)[0][0] or 10.0
    width = [ln[2] - ln[0] for ln in lines]
    wide = max(width) if width else 1
    L = mode([ln[0] for ln in lines], 25)
    rr = [ln[2] for ln in lines if ln[2] - ln[0] > wide * 0.6]
    R = mode(rr, 6) if rr else (L + wide)
    lo, hi = L - 20, R + 8

    def avg(ln):
        return sum(w[4] for w in ln[4]) / len(ln[4])
    last_body = max([ln[1] for ln in lines if avg(ln) >= 0.9 * body_fs] or [0])
    foot_from = None
    for ln in lines:
        if ln[1] > last_body and avg(ln) < 0.85 * body_fs and (ln[2] - ln[0]) > (R - L) * 0.4:
            foot_from = ln[1]
            break
    body = []
    for ln in lines:
        if foot_from is not None and ln[1] >= foot_from - 5:
            rec['foot'].append(ln[4])
            continue
        bw, mw = [], []
        for w in ln[4]:
            (mw if (w[1] > hi or w[2] < lo) else bw).append(w)
        if mw:
            rec['margin'].append([ln[1], ' '.join(fold(w[0]) for w in mw)])
        if bw:
            fused = any((w[1] < R - 5 and w[2] > R + FUSE) or (w[2] > L + 5 and w[1] < L - FUSE - 20) for w in bw)
            body.append([ln[1], bw, avg(ln), fused])
    # a signature line at the foot of the text (VOL. I. B; B 2) is furniture
    if body:
        t = ' '.join(w[0] for w in body[-1][1])
        if len(body[-1][1]) <= 5 and SIG_RE.match(t.strip()):
            body = body[:-1]
    for y, bw, a, fused in body:
        text = ' '.join(w[0] for w in bw)
        kind = 'chap' if CHAP_RE.match(text.strip()) else 'body'
        rec['lines'].append({'y': y, 'kind': kind, 'fused': fused, 'text_size': a >= 0.85 * body_fs,
                             'sc': any('s' in w[3] for w in bw),
                             'w': [[w[0], w[3], round(w[4], 1)] for w in bw]})
    # footnote marks: the first word of each footnote paragraph, where it is a mark
    for ws in rec['foot']:
        for w in ws[:1] + [x for x in ws[1:] if 'u' in x[3]]:
            t = fold(w[0]).strip('.')
            if len(t) == 1 or 'u' in w[3]:
                rec['marks'].append(t)
    rec['foot'] = [' '.join(fold(w[0]) for w in ws) for ws in rec['foot']]
    return rec


def item_pages(path, work, ident):
    """Parse one copy streaming; keep its laid-out pages in a scratch file, one page per line."""
    out = os.path.join(work, ident + '.pages.jsonl')
    if os.path.exists(out):
        return out
    tmp = out + '.part'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        for p in pages(path):
            fh.write(json.dumps(layout(p), ensure_ascii=False, separators=(',', ':')) + '\n')
    os.replace(tmp, out)
    return out


def load_pages(path):
    recs = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            recs.append(json.loads(line))
    # THE GOSPEL LINES: the Gospel text is set larger, so its lines stand further apart than the commentary's. The
    # commentary's usual distance is the copy's median line distance (the commentary fills most pages), or the
    # page's own where that is smaller still; a line whose distance to the text lines above and below (where there
    # are any on its page) is at least GOSPEL_PITCH times that is a Gospel line.
    gaps_all = []
    for r in recs:
        ys = [ln['y'] for ln in r['lines'] if ln['text_size']]
        gaps_all += [ys[k + 1] - ys[k] for k in range(len(ys) - 1)]
    gaps_all.sort()
    whole = gaps_all[len(gaps_all) // 2] if gaps_all else 0
    for r in recs:
        tl = [ln for ln in r['lines'] if ln['text_size']]
        ys = [ln['y'] for ln in tl]
        gaps = sorted(ys[k + 1] - ys[k] for k in range(len(ys) - 1))
        own = gaps[len(gaps) // 2] if gaps else whole
        pitch = min(own, whole) if whole else own
        for k, ln in enumerate(tl):
            up = ys[k] - ys[k - 1] if k > 0 else None
            down = ys[k + 1] - ys[k] if k + 1 < len(ys) else None
            if ln['kind'] == 'body' and not ln['sc'] and pitch and (up is not None or down is not None) and                     all(g is None or g >= GOSPEL_PITCH * pitch for g in (up, down)):
                ln['kind'] = 'gospel'
        # a commentary-sized gap inside a Gospel passage (one line between two Gospel lines) is still the Gospel
        for k in range(1, len(tl) - 1):
            if tl[k]['kind'] == 'body' and not tl[k]['sc'] and tl[k - 1]['kind'] == tl[k + 1]['kind'] == 'gospel':
                tl[k]['kind'] = 'gospel'
    # printed page numbers from the running heads: the local mode of (number - leaf)
    offs = {r['n']: r['num'] - r['n'] for r in recs if r['num'] is not None and r['num'] < 2000}
    for r in recs:
        win = [offs[k] for k in range(r['n'] - 6, r['n'] + 7) if k in offs]
        if win:
            m, c = collections.Counter(win).most_common(1)[0]
            r['pg'] = r['n'] + m if c >= 2 else r['num']
        else:
            r['pg'] = None
    return recs


# --------------------------------------------------------------------------------------------- one copy, one part

def walk(recs, first, last, chap0, forms, opens_in=None):
    """The excerpts of one copy over printed pages first..last: heads, words (with line positions), verses."""
    exs, unattributed = [], 0
    # a volume part opens at a chapter heading; a cut that opens inside a chapter names it (opens_in)
    chapter, chap_ok = (chap0 - 1 if opens_in is None else opens_in), True
    run = None          # the Gospel run open now: [(c, v) first, (c, v) last]
    rng = None          # the range the excerpts below belong to
    in_run = False
    cur = None
    heading_seen = True  # a chapter heading since the last Gospel run that began at verse 1
    last_v = 0
    inside = [r for r in recs if r.get('pg') is not None and first <= r['pg'] <= last]
    named = [chapter_numeral(re.search(r'CHA[P\^]?\.?\s*([IVXLCl]+)\.?\s*$', r.get('rhead') or '')) for r in inside]
    pages_seen = {}
    sections = []       # every Gospel passage's verse or range, in the order the copy prints them (None: unread)
    printed = {norm_head(f['form']) for au in forms.values() for f in au['printed_forms']}
    prev_tail = None    # the last word of the line before: a head broken across lines ends it with '-'
    for idx, r in enumerate(inside):
        # an even page's running head names its chapter: where it and the next running head that names one both say
        # the next chapter, the count moves on (a heading the OCR missed); one misread running head moves nothing
        rc = named[idx]
        if rc is not None and rc == chapter + 1:
            later = next((x for x in named[idx + 1:] if x is not None), None)
            if later == rc:
                chapter, heading_seen = rc, True
        pages_seen[r['pg']] = {'chapter': chapter, 'rhead_verses': rhead_verses(r.get('rhead') or ''),
                               'chap_start': False}
        for li, ln in enumerate(r['lines']):
            text = ' '.join(w[0] for w in ln['w']).strip()
            tail_before, prev_tail = prev_tail, (ln['w'][-1] if ln['w'] and ln['kind'] != 'chap' else None)
            if ln['kind'] == 'chap':
                pages_seen[r['pg']]['chap_start'] = True
                parsed = chapter_numeral(CHAP_RE.match(text))
                if parsed is not None and chapter <= parsed <= chapter + 1:
                    chapter = parsed            # the heading's own numeral, where it follows on
                else:
                    chapter += 1                # an unread numeral: the next chapter
                pages_seen[r['pg']]['chapter'] = chapter
                heading_seen, last_v = True, 0
                if not in_run:
                    run, in_run = [None, None], True
                cur = None
                continue
            # a verse mark: '12.', or a group of verses printed together, '12—15.' (the genealogy prints them so)
            m = VERSE_MARK.match(text + ' ')
            # a Gospel passage opens on a numbered verse (or a chapter heading); a wide-set line that opens on no
            # number outside a passage is the commentary's
            if ln['kind'] == 'gospel' and (in_run or m):
                if not in_run:
                    run, in_run = [None, None], True
                if m:
                    v, v_end = mark_verses(m)
                    if m.group(1) == '1' and last_v > 1 and not heading_seen:
                        chapter += 1            # verse 1 again with no heading read: a missed heading
                    heading_seen = False
                    last_v = v_end
                    if run[0] is None:
                        run[0] = (chapter, v)
                    run[1] = (chapter, v_end)
                cur = None
                continue
            # THE PASSAGE RUNS ON TO THE FIRST HEAD: the commentary after the Gospel text always opens with a head, so
            # every line before it is still the passage, whatever its spacing; a verse number opening one of those
            # lines extends the passage
            if in_run and m:
                v, v_end = mark_verses(m)
                if run[1] is not None and run[1][1] < v <= run[1][1] + 3:
                    run[1] = (chapter, v_end)
                    last_v = v_end
            # A LINE SET AT THE GOSPEL'S SPACING THAT OPENS ON A NUMBER, outside a passage, is a verse whose mark
            # was not read ('65 Pilate', no stop): its words join the excerpt, which cannot be attributed with
            # certainty and is held
            if ln['kind'] == 'gospel' and not in_run and cur is not None and re.match(r'\d', text):
                cur['numbered_wide_line'] = True
            ws = ln['w']
            i = 0
            while i < len(ws):
                text_w, flags, fs = ws[i]
                if 's' in flags:
                    j = i
                    while j < len(ws) and 's' in ws[j][1]:
                        j += 1
                    head = ' '.join(w[0] for w in ws[i:j])
                    nxt = ws[j][0] if j < len(ws) else ''
                    term = ';' if (head.endswith(';') or nxt.startswith(';')) else ('.' if head.endswith('.') else '')
                    k = key_of(head)
                    # A HEAD BROKEN ACROSS LINES: a line that opens on a head after a line ending in '-' holds the
                    # head's second half (PSEUDO- | CHRYS.). Its first half in small capitals is joined to it and
                    # taken out of the excerpt before; otherwise the head is read but held, never served as the half
                    # (the line-end hyphen is dropped where the table holds the name whole, THEOPHYL., and kept
                    # only where it holds it with no whole form, PSEUDO-CHRYS.)
                    broken = False
                    if i == 0 and tail_before is not None and fold(tail_before[0]).endswith('-') and term:
                        half = fold(tail_before[0])
                        whole = [h for h in (half[:-1] + head, half + head) if norm_head(h) in printed]
                        if 's' in tail_before[1] and whole:
                            head = whole[0]
                            k = key_of(head)
                            if cur is not None and cur['toks'] and cur['toks'][-1][0] == tail_before[0]:
                                cur['toks'].pop()
                        else:
                            broken = True
                    if term and k in forms:
                        if in_run:
                            in_run = False
                            rng = (run[0], run[1]) if run[0] is not None else None
                            sections.append(rng)
                        cur = {'page': r['pg'], 'leaf': r['n'], 'head': head, 'key': k, 'author': forms[k],
                               'range': rng, 'chapter_ok': chap_ok, 'toks': [], 'margin': [], 'broken': broken,
                               'sec': len(sections) - 1}
                        exs.append(cur)
                        cur['margin'] = margin_block(r, ln['y'])
                        i = j
                        if i < len(ws) and ws[i][0] in (';', '.'):
                            i += 1
                        continue
                if in_run:
                    pass                        # the passage's own words, before the commentary's first head
                elif cur is None:
                    unattributed += 1
                else:
                    cur['toks'].append([text_w, flags, r['n'], li, i == 0, i == len(ws) - 1, ln['fused'],
                                        r['marks']])
                i += 1
    return exs, unattributed, pages_seen, sections


VERSE_MARK = re.compile(r'^(?:Ver\.?\s*)?([0-9lI]{1,3})(?:\s*[—–-]\s*([0-9lI]{1,3})\s*[.,]|\s*[.,\-])\s')


def mark_verses(m):
    """A verse mark's first and last verse ('12.' is 12 and 12; '12—15.' is 12 and 15; the OCR's l and I are 1)."""
    a = int(m.group(1).replace('l', '1').replace('I', '1'))
    b = int(m.group(2).replace('l', '1').replace('I', '1')) if m.group(2) else a
    return a, (b if b >= a else a)


def rhead_verses(rh):
    """An odd page's running head, 'VER. 12-15. ST. MATTHEW. 31': the verses the page comments on, or None."""
    m = re.match(r'^\s*V\S{0,3}[.,]?\s*(.*?)(?:\bST\b|\bS\s*T\b|GOS|$)', rh)
    if not m:
        return None
    nums = [int(x) for x in re.findall(r'\d{1,3}', m.group(1)) if 0 < int(x) < 200]
    if not nums:
        return None
    return (nums[0], nums[1] if len(nums) > 1 else nums[0])


def margin_block(r, y):
    """The margin lines that begin on the head's line and run on below it without a gap."""
    ms = sorted(r['margin'])
    gap = 0.035 * (r.get('h') or 4000)
    block, last = [], None
    for my, mt in ms:
        if last is None:
            if abs(my - y) < gap / 2.5:
                block.append(mt)
                last = my
        elif my - last < gap:
            block.append(mt)
            last = my
        else:
            break
    return block


def vocab(recs_list, first, last):
    c = collections.Counter()
    for recs in recs_list:
        for r in recs:
            if r.get('pg') is None or not (first <= r['pg'] <= last):
                continue
            for ln in r['lines']:
                ws = ln['w']
                for idx, w in enumerate(ws):
                    t = fold(w[0])
                    if t.endswith('-') and idx == len(ws) - 1:
                        continue
                    k = core(t)
                    if k:
                        c[k] += 1
    return c


def words_of(ex, voc, mis):
    """(words, holds, undecided hyphens) of one copy's excerpt."""
    toks = ex['toks']
    out, holds, undecided = [], set(), []
    i = 0
    while i < len(toks):
        t, flags, leaf, li, first, last, fused, marks = toks[i]
        w = fold(t)
        if 'u' in flags:
            if w.strip('.') in marks and len(w.strip('.')) <= 2:
                i += 1
                continue
            holds.add('superscript not a footnote mark')
        if fused and (first or last):
            holds.add('fused margin word')
        if 'æ' in w.lower() or 'Æ' in w or 'ae' in w.lower():
            holds.add('ligature ae')
        bad = [ch for ch in w if not (ch.isalpha() or ch in STATED)]      # a figure is outside the set
        if (bad and w != '&c.') or core(w) in mis or w in mis:
            holds.add('character or misreading')
        if w in ('1', 'l', '/', 'J') and i + 1 < len(toks) and first_letter(toks[i + 1][0]).islower():
            holds.add('italic I')
        # an italic run whose first word is lower case, wherever it opens: in this printing a dropped italic I opens
        # a quotation in mid-sentence ('It follows, I was an hungred'), and quotations open with a capital
        if 'i' in flags and (i == 0 or 'i' not in toks[i - 1][1]) and first_letter(w).islower():
            holds.add('italic I')
        if 's' not in flags and w[:1].isupper() and (w.endswith(';') or w.endswith('.')) and key_of(w) in FORMS_KEYS:
            holds.add('unflagged head')
        if w.endswith('-') and len(w) > 1 and last and i + 1 < len(toks):
            nxt = fold(toks[i + 1][0])
            a, b = core(w[:-1]), re.sub(r"[^\w]+$", '', nxt).lower()
            hy, jo = voc.get(a + '-' + b, 0), voc.get(a + b, 0)
            if hy and not jo:
                out.append(w + nxt)
            elif jo and not hy:
                out.append(w[:-1] + nxt)
            else:
                undecided.append((len(out), w[:-1], nxt))
                out.append(w[:-1] + nxt)
            i += 2
            continue
        if last and i + 1 < len(toks) and not re.search(r'[^\w]$', w):
            a, b = core(w), core(toks[i + 1][0])
            if a and b and first_letter(toks[i + 1][0]).islower() and voc.get(a + b, 0):
                holds.add('lost hyphen')
        out.append(w)
        i += 1
    return out, holds, undecided


FORMS_KEYS = set()


# --------------------------------------------------------------------------------------------- one part, both copies

def rhead_allows(page, rng, copies):
    """The running heads must allow the range, and at least one must speak. An odd page's own 'VER. a-b.' bounds it; an
    even page is bounded by the page before's first verse and the page after's last. A chapter's first page carries
    no running head: it opens at verse 1, and the next odd page's head gives its last verse. Pages in another
    chapter say nothing. Every copy whose heads can be read must allow the range; a range none speaks to is not
    confirmed."""
    (c1, v1), (c2, v2) = rng

    def first_of(pages, p):
        x = pages.get(p)
        if not x or x['chapter'] != c2:
            return None
        if x['rhead_verses']:
            return x['rhead_verses'][0]
        return 1 if x.get('chap_start') else None

    def last_of(pages, p):
        x = pages.get(p)
        if not x or x['chapter'] != c2:
            return None
        if x['rhead_verses']:
            return x['rhead_verses'][1]
        if x.get('chap_start'):
            return last_of(pages, p + 2)
        return None
    spoke = False
    for pages in copies:
        if page % 2:
            a, b = first_of(pages, page), last_of(pages, page)
        else:
            a, b = first_of(pages, page - 1), last_of(pages, page + 1)
        if a is None or b is None:
            continue
        spoke = True
        if v2 > b or (c1 == c2 and v1 < a):
            return False
    return spoke


def verse_label(gospel, rng):
    if not rng:
        return None
    (c1, v1), (c2, v2) = rng
    if (c1, v1) == (c2, v2):
        return '%s %d:%d' % (gospel, c1, v1)
    if c1 == c2:
        return '%s %d:%d-%d' % (gospel, c1, min(v1, v2), max(v1, v2))
    return '%s %d:%d-%d:%d' % (gospel, c1, v1, c2, v2)


BOOK_ABBR = set("""gen ex exod lev num deut josh judg ruth sam kings chron ezra neh esth job ps psalm prov eccl eccles cant
is isa jer lam ez ezek dan hos joel amos obad jon mic nah hab zeph hag zech mal matt mark marc luke luc john joan acts
rom cor gal eph phil col thess tim tit philem heb jas james pet jude rev apoc tob wisd ecclus bar mac""".split())
SCRIPTURE = re.compile(r"^(?:[1-3]\s+)?([A-Za-z]+)\.?$")
OPENERS = set()


def citation(ex):
    """The excerpt's source as its margin gives it: from the first word that opens a citation (a form the golden's
    citations open with) up to, not including, a Scripture reference; None when the margin holds no such opening."""
    toks = ' '.join(ex['margin']).split()
    start = None
    for i, t in enumerate(toks):
        if core(t) in OPENERS:
            start = i
            break
    if start is None:
        return None
    out = []
    for i in range(start, len(toks)):
        t = toks[i]
        m = SCRIPTURE.match(t)
        if i > start and m and m.group(1).lower() in BOOK_ABBR and i + 1 < len(toks) and                 re.match(r"^([0-9]+|[ivxlc]+)[.,]", toks[i + 1]) and (i == start or toks[i - 1].lower() != 'in'):
            break
        out.append(t)
    # a citation names a work after its writer (Hom., Ep., de ..., in ..., ubi sup.); one whose second word is a
    # bare number, or that holds a stray mark, has lost a line or a word in the OCR, and is not confirmed
    if len(out) < 2 or not re.match(r"^[A-Za-z]", out[1]) or             any(not re.fullmatch(r"[A-Za-zæÆ]+\.?,?|[0-9]+[.,]?|[ivxlcIVXLC]+\.?,?|\(?[A-Za-z]+\.?\)?\.?,?", t) for t in out):
        return None
    return ' '.join(out)


def section_order(secs, i, verses):
    """Conditions (3) and (4) for section i of one copy's sections, read against the engine's verse numbers for the
    Gospel ({chapter: [verses as they stand]}): [] where it begins at the verse after the section before it in its
    chapter (a chapter's first section at the chapter's first verse), the chapter's last section ends at the chapter's
    last verse, and it overlaps neither neighbour; otherwise the reasons. An unread neighbour confirms nothing."""
    if i < 0 or i >= len(secs) or secs[i] is None:
        return ['verse not read']
    (c1, v1), (c2, v2) = secs[i]
    if c1 not in verses or c2 not in verses or v1 not in verses[c1] or v2 not in verses[c2]:
        return ["verse not in the engine's chapter"]
    if (c2, v2) < (c1, v1) or c2 > c1 + 1:
        return ['range not in order']
    prev = secs[i - 1] if i > 0 else 'start'
    nxt = secs[i + 1] if i + 1 < len(secs) else 'end'
    if prev is None or nxt is None:
        return ['a neighbour unread']
    out = []
    vs = verses[c1]
    if prev != 'start' and prev[1][0] == c1:
        k = vs.index(prev[1][1]) if prev[1][1] in vs else None
        if k is None or k + 1 >= len(vs) or vs[k + 1] != v1:
            out.append('does not follow the section before')
    elif v1 != vs[0]:
        out.append('does not open its chapter')
    if prev != 'start' and prev[1][0] > c1:
        out.append('after a later chapter')
    if (nxt == 'end' or nxt[0][0] > c2) and v2 != verses[c2][-1]:
        out.append('does not close its chapter')
    if prev != 'start' and prev[1] >= (c1, v1):
        out.append('overlaps the section before')
    if nxt != 'end' and nxt[0] <= (c2, v2):
        out.append('overlaps the section after')
    return out


def neighbours(secs, i):
    """The sections before and after section i, as one copy reads them."""
    return (secs[i - 1] if 0 < i <= len(secs) else 'start', secs[i + 1] if 0 <= i < len(secs) - 1 else 'end')


def build_part(key, part, recs_a, recs_b, forms, mis, golden_by_leaf, gospel_verses):
    gospel = part['gospel']
    first, last = part['printed_pages']
    chap0 = roman(part['chapters'].split('-')[0])
    ea, ua, pa, sa = walk(recs_a, first, last, chap0, forms, part.get('opens_in_chapter'))
    eb, ub, pb, sb = walk(recs_b, first, last, chap0, forms, part.get('opens_in_chapter'))
    verses = {int(c): vs for c, vs in gospel_verses['chapters'][gospel].items()}
    whole = {h['chapter'] for h in gospel_verses['held_whole'] if h['gospel'] == gospel}
    at_pair = {(p['chapter'], v) for p in gospel_verses['pairs'] if p['gospel'] == gospel for v in p['verses']}
    voc = vocab([recs_a, recs_b], first, last)
    sm = difflib.SequenceMatcher(None, [(e['page'], e['key']) for e in ea], [(e['page'], e['key']) for e in eb],
                                 autojunk=False)
    pair = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                pair[i] = j
    served, held = [], collections.Counter()
    all_holds = collections.Counter()
    golden_checks = []
    verse_disputes = []
    cit_unconfirmed = 0
    golden_held = []
    golden_holds = []
    sections_confirmed = set()
    matched = set()
    for i, a in enumerate(ea):
        g = golden_by_leaf.get(a['leaf'], [])
        wa, ha, ua_ = words_of(a, voc, mis)
        holds = set(ha)
        b = None
        if i not in pair or (i + 1 < len(ea) and (i + 1) in pair and pair[i + 1] != pair[i] + 1):
            holds.add('head not at the same place')
        else:
            b = eb[pair[i]]
        if a.get('numbered_wide_line') or (b is not None and b.get('numbered_wide_line')):
            holds.add('numbered Gospel line in the words')
        if a['broken'] or (b is not None and b['broken']):
            holds.add('head broken across lines')
        if b is not None:
            wb, hb, ub_ = words_of(b, voc, mis)
            holds |= hb
            if a['range'] != b['range'] or a['range'] is None:
                holds.add('verse not confirmed')
            if not (a['chapter_ok'] and b['chapter_ok']):
                holds.add('chapter not confirmed')
            if ua_ or ub_:
                holds.add('line-end hyphen undecided')
            if tokens(render(wa)) != tokens(render(wb)):
                holds.add('words differ')
        text = render(wa)
        # the golden entry for this excerpt: the one on its leaf whose opening words are most like its own, whoever
        # the golden names as its author (so a head read as the wrong writer is a mismatch, never an unchecked pass)
        gmatch = None
        if g:
            best = max(g, key=lambda ge: difflib.SequenceMatcher(None, tokens(ge['words'])[:40], tokens(text)[:40],
                                                                   autojunk=False).ratio())
            if difflib.SequenceMatcher(None, tokens(best['words'])[:40], tokens(text)[:40], autojunk=False).ratio() > 0.5:
                gmatch = best
        # the golden settles: where the page image check holds the same words both copies give, a hold
        # about those words is lifted (never a disagreement between the copies, a head or a verse)
        if gmatch is not None and b is not None:
            settled = {'lost hyphen', 'fused margin word', 'ligature ae', 'character or misreading',
                       'superscript not a footnote mark', 'italic I', 'unflagged head', 'line-end hyphen undecided'}
            if holds & settled and not (holds - settled - {'words differ'}):
                ga = golden_words_for(wa, ua_, gmatch)
                gb = golden_words_for(wb, ub_, gmatch)
                if ga is not None and gb is not None and tokens(ga) == tokens(gb) == tokens(gmatch['words']):
                    text = ga
                    holds = set()
        # THE VERSE IS CONFIRMED only where (1) both copies read it alike, (2) the running heads allow it, (3) it
        # begins at the verse after the section before it in its chapter, as both copies read that section, and (4)
        # it overlaps no neighbour; the chapters the engine's English and Latin number otherwise are held whole, and
        # a section bounded at a pair of verses the Latin divides otherwise is held
        confirmed = False
        if b is not None and a['range'] is not None and a['range'] == b['range']:
            (c1, v1), (c2, v2) = a['range']
            heads_ok = rhead_allows(a['page'], a['range'], (pa, pb))
            if not heads_ok:
                holds.add('verse not in the running head')
            order = section_order(sa, a['sec'], verses) + section_order(sb, b['sec'], verses)
            if neighbours(sa, a['sec']) != neighbours(sb, b['sec']):
                order.append('neighbours read otherwise')
            if order:
                holds.add('verse out of order')
            confirmed = heads_ok and not order
            if c1 in whole or c2 in whole:
                holds.add('chapter held whole')
            if (c1, v1) in at_pair or (c2, v2) in at_pair:
                holds.add('bounded at a listed pair')
            # the golden's verse, read from the page image: a confirmed verse that differs from it refuses the
            # build; one not confirmed is held, and the difference reported
            if gmatch is not None and verse_label(gospel, a['range']) != gmatch['verse']:
                if confirmed:
                    golden_checks.append([gmatch['id'], ['verse']])
                else:
                    verse_disputes.append([gmatch['id'], gmatch['verse'], verse_label(gospel, a['range'])])
        if confirmed:
            sections_confirmed.add((a['sec'], b['sec']))
        for h in holds:
            all_holds[h] += 1
        if gmatch is not None:
            matched.add(gmatch['id'])
        if holds:
            held[min(holds, key=HOLD_ORDER.index)] += 1
            if gmatch is not None:
                golden_held.append([gmatch['id'], min(holds, key=HOLD_ORDER.index)])
                golden_holds.append([gmatch['id'], sorted(holds, key=HOLD_ORDER.index)])
            continue
        ca, cb = citation(a), citation(b)
        cit = ca if (ca and cb and ca.lower() == cb.lower()) else None
        if cit is None:
            cit_unconfirmed += 1
        exc = {'author_as_printed': norm_head(a['head']), 'author_key': a['author']['key'], 'page': a['page'],
               'verse': verse_label(gospel, a['range']), 'range': [list(a['range'][0]), list(a['range'][1])],
               'text': text, 'citation': cit if cit else 'citation not confirmed'}
        # an ascription the edition's editors dispute in this volume part travels with the excerpt (Mark's CHRYS.)
        mark = (a['author'].get('editors_mark_in_parts') or {}).get(key)
        if mark:
            exc['editors_mark'] = {k: mark[k] for k in ('quote', 'and', 'and_of', 'where', 'page_image')}
        if gmatch is not None:
            problems = []
            if tokens(text) != tokens(gmatch['words']):
                problems.append('words')
            if exc['author_as_printed'] != gmatch['author_as_printed']:
                problems.append('author')
            if cit is not None and (gmatch['citation'] or '').lower() != cit.lower():
                problems.append('citation')
            golden_checks.append([gmatch['id'], problems])
        served.append(exc)
    # a golden excerpt no head here matched: where its opening words sit inside an excerpt served, its head was
    # missed and its words would be served under another writer's name; that is a mismatch, and the build refuses
    unmatched = sorted({e['id'] for es in golden_by_leaf.values() for e in es} - matched)
    by_id = {e['id']: e for es in golden_by_leaf.values() for e in es}
    for gid in unmatched:
        opening = ' '.join(tokens(by_id[gid]['words'])[:8])
        for exc in served:
            if len(opening.split()) == 8 and ' %s ' % opening in ' %s ' % ' '.join(tokens(exc['text'])):
                golden_checks.append([gid, ['words served under %s, page %s' % (exc['author_as_printed'], exc['page'])]])
    leaf_keys = collections.defaultdict(set)
    for a in ea:
        leaf_keys[a['leaf']].add(a['key'])
    no_head = [[gid, 'a head of that name read on its leaf in copy A, its opening words unlike'
                if key_of(by_id[gid]['author_as_printed']) in leaf_keys[by_id[gid]['leaf']]
                else 'no head of that name read on its leaf in copy A'] for gid in unmatched]
    counts = {'heads_copy_a': len(ea), 'heads_copy_b': len(eb), 'served': len(served), 'held': sum(held.values()),
              'held_by_first_hold': dict(held), 'holds_applying': dict(all_holds),
              'citation_not_confirmed': cit_unconfirmed, 'unattributed_words_copy_a': ua,
              'sections_copy_a': len(sa), 'sections_copy_b': len(sb), 'sections_confirmed': len(sections_confirmed),
              'golden_verse_disputes': verse_disputes, 'golden_held_by_first_hold': golden_held,
              'golden_holds': golden_holds, 'golden_no_head_matched': no_head}
    return served, counts, golden_checks


def norm_head(h):
    h = re.sub(r'[;:.,\s]+$', '', fold(h)).upper()
    h = re.sub(r'-\s+', '-', h)
    return re.sub(r'\s+', ' ', h)


def golden_words_for(words, undecided, ge):
    """The excerpt's words with its undecided line-end hyphens read as the golden reads them, if it can."""
    gt = tokens(ge['words'])
    out = list(words)
    for pos, a, b in undecided:
        joined, hyph = a + b, a + '-' + b
        if fold(joined) in gt or tokens(joined)[0] in gt:
            out[pos] = joined
        elif fold(hyph) in gt or tokens(hyph)[0] in gt:
            out[pos] = hyph
        else:
            return None
    return render(out)


# --------------------------------------------------------------------------------------------- main

def main(argv):
    if len(argv) not in (3, 4) or argv[2] != 'fetch':
        print('usage: build_catena.py INPUTS OUTPUT fetch [CACHE]', file=sys.stderr)
        return 2
    inputs, out = argv[0], argv[1]
    cache = argv[3] if len(argv) == 4 else None
    work = os.path.abspath('catena-work')
    os.makedirs(work, exist_ok=True)
    try:
        result = build(inputs, work, cache)
    except Refuse as e:
        print('REFUSED: %s' % e, file=sys.stderr)
        return 1
    files, report = result
    for rel, data in sorted(files.items()):
        p = os.path.join(out, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as fh:
            fh.write(data)
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps(report['totals'], sort_keys=True))
    return 0


def prime(golden, mis, forms):
    """Set the forms an unflagged head is read by and the words a citation opens with; return the misreadings."""
    FORMS_KEYS.clear()
    FORMS_KEYS.update(forms)
    OPENERS.clear()
    for e in golden['excerpts']:
        if e.get('citation'):
            OPENERS.add(core(e['citation'].split()[0]))
    return set(m['ocr'] for m in mis['misreadings']) | set(core(m['ocr']) for m in mis['misreadings'])


def build(inputs, work, cache):
    authors, golden, census, mis, forms, gospel_verses = load_inputs(inputs)
    misset = prime(golden, mis, forms)
    gby = collections.defaultdict(lambda: collections.defaultdict(list))
    for e in golden['excerpts']:
        gby[e['item']][e['leaf']].append(e)
    served_all = collections.defaultdict(list)
    report = {'parts': {}, 'golden_checked': [], 'golden_mismatch': [],
              'verses': {'held_whole': ['%s %d' % (h['gospel'], h['chapter']) for h in gospel_verses['held_whole']],
                         'pairs': ['%s %d:%d/%d' % (p['gospel'], p['chapter'], p['verses'][0], p['verses'][1])
                                   for p in gospel_verses['pairs']]}}
    parsed = {}
    for key in sorted(census['parts']):
        part = census['parts'][key]
        a, b = part['copy_a'], part['copy_b']
        recs = []
        for ident in (a, b):
            if ident not in parsed:
                sha = census['items'][ident]['layout_files']['abbyy_gz']['sha256_fetched_2026_11_11']
                src = fetch(ident, sha, cache, work)
                parsed[ident] = item_pages(src, work, ident)
                if src.startswith(work):
                    os.remove(src)
            recs.append(load_pages(parsed[ident]))
        golden_by_leaf = dict(gby.get(a, {}))
        served, counts, checks = build_part(key, part, recs[0], recs[1], forms, misset, golden_by_leaf,
                                            gospel_verses)
        del recs
        report['parts'][key] = counts
        for gid, problems in checks:
            (report['golden_mismatch'] if problems else report['golden_checked']).append([gid, problems] if problems else gid)
        for e in served:
            served_all[part['gospel']].append(e)
    if report['golden_mismatch']:
        raise Refuse('golden mismatch: %s' % json.dumps(report['golden_mismatch']))
    files = {}
    books = []
    for gospel, code in BOOKS.items():
        by_ch = collections.defaultdict(lambda: collections.defaultdict(list))
        for e in served_all.get(gospel, []):
            (c1, v1), (c2, v2) = e['range']
            for c in range(c1, c2 + 1):
                by_ch[c][(c1, v1, c2, v2)].append(e)
        chapters = sorted(by_ch)
        books.append({'code': code, 'name': gospel, 'commonName': gospel, 'chapters': CHAPTERS[gospel],
                      'chapters_with_excerpts': chapters})
        for c in chapters:
            blocks = []
            for (c1, v1, c2, v2), exs in sorted(by_ch[c].items()):
                lo = v1 if c1 == c else 1
                hi = v2 if c2 == c else 999
                blocks.append({'chapter': c1, 'verse': min(v1, v2) if c1 == c2 else v1, 'end_chapter': c2,
                               'verse_end': max(v1, v2) if c1 == c2 else v2, 'covers_in_this_chapter': [lo, hi],
                               'range': exs[0]['verse'], 'excerpts': [
                                   {k: x[k] for k in ('author_as_printed', 'author_key', 'citation', 'editors_mark',
                                                      'page', 'text') if k in x}
                                   for x in exs]})
            files['%s/%d.json' % (code, c)] = jdump({'source': 'catena-aurea', 'book': gospel, 'chapter': c, 'blocks': blocks})
    files['_books.json'] = jdump(books)
    used = sorted({x['author_key'] for v in served_all.values() for x in v})
    akeys = {a['key']: a for a in authors['authors']}
    files['_authors.json'] = jdump({k: {f: akeys[k].get(f) for f in ('identified_as', 'kind', 'edition_table_name', 'dates', 'language')}
                                    for k in used})
    totals = {'served': sum(p['served'] for p in report['parts'].values()),
              'held': sum(p['held'] for p in report['parts'].values()),
              'golden_served_and_equal': len(report['golden_checked'])}
    report['totals'] = totals
    files['_build.json'] = jdump(report)
    return files, report


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
