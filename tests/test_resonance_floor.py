"""The resonance floor (ask._covers_the_asking, ask._floor_filter) — the fix for the "human capital
theory" bug — and its companion, the card the asking names by its title (ask._prefer_the_titled_card,
ask._fetch_the_card_the_asking_names). Pure logic, fakes only: these run on a clean clone.

A found answer must cover the asking's rarest (most identifying) token, not just a common one.
These test the pure logic with a tiny fake corpus (its `_by_token` sets the token frequencies), so
they run on a clean clone with no full corpus. The floor's threshold is the corpus's own token
frequencies, so there is nothing to tune — only to validate against the box's full keeping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import ask  # noqa: E402


class _FakeCorpus:
    def __init__(self, by_token):
        self._by_token = by_token


# "capital" is common in the keeping (human capital, capital markets, …); "france" is rarer.
_KEEPING = _FakeCorpus({"capital": ["c1", "c2", "c3", "c4", "c5"], "france": ["c6"],
                        "paris": ["c6"], "theory": ["c1", "c7"], "human": ["c1", "c8"]})


def test_floor_nulls_a_lead_that_misses_the_rarest_token():
    lead = {"title": "Human capital theory (Becker, Mincer)",
            "body": "schooling is an investment with a discounted stream of returns"}
    assert ask._covers_the_asking(lead, "what is the capital of France", _KEEPING) is False


def test_floor_passes_a_lead_that_covers_the_rarest_token():
    lead = {"title": "France", "body": "The capital of France is Paris, on the Seine."}
    assert ask._covers_the_asking(lead, "what is the capital of France", _KEEPING) is True


def test_floor_does_not_suppress_a_thin_asking():
    # a single content token can't discriminate — never suppress on it
    assert ask._covers_the_asking({"title": "x", "body": "y"}, "paris", _KEEPING) is True


def test_floor_does_not_suppress_when_the_keeping_holds_too_little():
    # neither token is in the keeping -> cannot discriminate -> don't suppress
    empty = _FakeCorpus({})
    assert ask._covers_the_asking({"title": "z", "body": ""}, "quokka numbat population", empty) is True


# "hodge" is rare (one chain); "conjecture" is common (every Millennium node). The Hodge-test bug:
# a lead sharing only the rarest token ("hodge") was NOT suppressed, so Bochner's Hodge-THEORY card led.
_HODGE = _FakeCorpus({"hodge": ["h1"], "conjecture": ["m1", "m2", "m3", "m4"],
                      "harmonic": ["h1", "b1"], "cycles": ["h1"]})


def test_floor_nulls_a_lead_sharing_only_the_rarest_token():
    # Bochner (Hodge THEORY): has "hodge", lacks "conjecture" -> only ONE of two -> suppress
    bochner = {"title": "S. Bochner 1946 - Vector fields and Ricci curvature",
               "body": "harmonic forms and the Hodge decomposition of a Riemannian manifold"}
    assert ask._covers_the_asking(bochner, "the Hodge conjecture", _HODGE) is False


def test_floor_passes_a_lead_that_covers_the_name_via_bands():
    # the Hodge-conjecture node carries the distinctive name in its BANDS, not its prose
    floor = {"title": "The Hodge chain - from periods to the classes that are not cycles",
             "body": "Riemann's periods, Lefschetz's (1,1) theorem, Hodge's harmonic integrals",
             "bands": ["hodge", "Hodge conjecture", "algebraic cycles"]}
    assert ask._covers_the_asking(floor, "the Hodge conjecture", _HODGE) is True


# The gate refused the first deploy of the floor (2026-11-01): four discernment charts the question
# plainly named ("what did the stoics believe", "is mormonism christian", ...) were nulled, because a
# chart's subject lives in its discerns_terms ("the stoics"), not its prose ("Stoicism"). A chart leads
# on purpose (_pair_discernment) — the floor must never second-guess the one the asking names.
_STOA = _FakeCorpus({"stoics": ["s1"], "believe": ["b1", "b2", "b3"], "capital": ["c1", "c2"],
                     "france": ["c6"]})
_STOICISM = {"id": "card_foreshadow_stoicism", "shelf": "foreshadows", "title": "Stoicism",
             "body": "Zeno's porch: live according to nature; the Logos; Paul on the Areopagus (Acts 17).",
             "bands": ["foreshadow", "religion", "stoic", "natural law"],
             "extra": {"discerns_terms": ["stoicism", "stoic philosophy", "the stoics"]}}


def test_floor_never_nulls_the_chart_the_asking_names():
    # "stoics" is in no prose/band token, only in the chart's own terms ("the stoics") -> still leads
    assert ask._covers_the_asking(_STOICISM, "what did the stoics believe", _STOA) is True


def test_floor_still_judges_a_chart_the_asking_did_not_name():
    # the same chart on an unrelated asking is judged by coverage like any card -> suppressed
    assert ask._covers_the_asking(_STOICISM, "what is the capital of France", _STOA) is False


def test_floor_counts_a_charts_terms_toward_its_coverage():
    # no whole term is tripped ("ching" is not "tao te ching"), but the TERM's tokens cover the asking's
    # rarest word and the body covers a second -> covered, like _shares_a_word reads a chart
    chart = {"shelf": "foreshadows", "title": "Chinese traditions", "body": "the Way, virtue, the sage",
             "bands": ["daoism", "the way"], "extra": {"discerns_terms": ["tao te ching", "lao tzu"]}}
    keeping = _FakeCorpus({"ching": ["t1"], "virtue": ["v1", "v2", "v3"], "teaching": ["x1", "x2"]})
    assert ask._covers_the_asking(chart, "ching virtue teaching", keeping) is True


# THE FLOOR IS A FILTER (2026-11-01). "the Riemann hypothesis": the connection lift put a differential-
# geometry hub first and the exact-title card second; the floor judged only hits[0] and nulled the whole
# answer. Now every hit is judged, the covering hits stand first (nothing dropped), and the null comes
# only when none covers.
_ZETA = _FakeCorpus({"riemann": ["r1", "r2", "r3"], "hypothesis": ["r1", "r2"], "curvature": ["g1"]})
_DIFF_GEO = {"id": "card_theory_differential_geometry",
             "title": "Differential geometry (curvature measured from inside)",
             "body": "Gauss, Riemann: curvature read from the surface itself"}
_QUESTION = {"id": "card_question_riemann", "title": "The Riemann hypothesis",
             "body": "every non-trivial zero of the zeta function has real part one half"}
_WEIL = {"id": "card_joint_weil_conjectures",
         "title": "The Weil conjectures: the Riemann hypothesis over finite fields", "body": "Deligne 1974"}


def test_filter_leads_with_the_first_hit_that_covers():
    out = ask._floor_filter([_DIFF_GEO, _QUESTION, _WEIL], "the Riemann hypothesis", _ZETA)
    assert [c["id"] for c in out] == ["card_question_riemann", "card_joint_weil_conjectures",
                                      "card_theory_differential_geometry"]


def test_filter_leaves_a_covering_lead_exactly_as_ranked():
    hits = [_QUESTION, _WEIL, _DIFF_GEO]
    assert ask._floor_filter(hits, "the Riemann hypothesis", _ZETA) == hits


def test_filter_nulls_only_when_no_hit_covers():
    human = {"id": "h", "title": "Human capital theory (Becker, Mincer)", "body": "schooling as investment"}
    markets = {"id": "m", "title": "Capital markets", "body": "the pricing of risk"}
    assert ask._floor_filter([human, markets], "what is the capital of France", _KEEPING) == []


def test_filter_keeps_a_thin_asking_whole():
    hits = [{"id": "a", "title": "x", "body": "y"}, {"id": "b", "title": "z", "body": "w"}]
    assert ask._floor_filter(hits, "paris", _KEEPING) == hits


def test_filter_never_demotes_a_chart_a_result_tripped():
    # the question names none of the chart's terms and the chart covers none of the asking's rare words —
    # but a RESULT is a primary source on the practice it discerns, so _pair_discernment lifted it: it
    # leads on purpose, never second-guessed, and the source stands behind it
    chart = {"id": "card_foreshadow_gateway", "shelf": "foreshadows",
             "title": "The Gateway process, under the test",
             "body": "Hemi-Sync and the Monroe Institute, read against Deuteronomy 18",
             "extra": {"discerns_terms": ["astral projection", "out-of-body"]}}
    source = {"id": "card_src_leadbeater", "title": "C. W. Leadbeater - The Astral Plane (astral projection)",
              "body": "how to leave the body at night and travel"}
    keeping = _FakeCorpus({"leave": ["s1", "s2"], "body": ["s1", "s2", "s3"], "night": ["s1"]})
    assert ask._covers_the_asking(chart, "how do i leave my body at night", keeping) is False
    out = ask._floor_filter([chart, source], "how do i leave my body at night", keeping)
    assert [c["id"] for c in out] == ["card_foreshadow_gateway", "card_src_leadbeater"]


# THE ASKING NAMES A CARD BY ITS TITLE (2026-11-01) — the filter's companion. Measured live after the
# filter deployed: "the Riemann hypothesis" led with the Weil finite-field joint. The ranker's nine-fold
# exact-title boost fires on the query AS TYPED, but the found path searched the crafted subject ("riemann
# hypothesis"), the titled card fell out of the six, and the hub lift then put a differential-geometry hub
# over the rest. Retrieval fetches the titled card once; shaping step 4½ keeps it in front.
_RH_HUB = {"id": "card_theory_differential_geometry",
           "title": "Differential geometry (curvature measured from inside)",
           "connections": [{"to_card_id": "card_theory_non_euclidean", "relationship": "cites"}]}
_RH_Q = {"id": "card_question_riemann", "title": "The Riemann hypothesis", "connections": []}
_RH_WEIL = {"id": "card_joint_weil_conjectures",
            "title": "The Weil conjectures (Deligne 1974): the Riemann hypothesis over finite fields"}
_RH_NE = {"id": "card_theory_non_euclidean", "title": "Non-Euclidean geometry",
          "connections": [{"to_card_id": "card_theory_differential_geometry", "relationship": "cites"}]}


def test_the_titled_card_leads_over_a_hub():
    out = ask._prefer_the_titled_card([_RH_HUB, _RH_WEIL, _RH_Q, _RH_NE], "the Riemann hypothesis")
    assert [c["id"] for c in out] == ["card_question_riemann", "card_theory_differential_geometry",
                                      "card_joint_weil_conjectures", "card_theory_non_euclidean"]
    # case and spacing are the ranker's own normalization; a title that merely CONTAINS the asking is not it
    assert ask._prefer_the_titled_card([_RH_WEIL, _RH_Q], "  THE riemann   Hypothesis ")[0]["id"] == "card_question_riemann"
    assert ask._prefer_the_titled_card([_RH_HUB, _RH_WEIL], "the Riemann hypothesis") == [_RH_HUB, _RH_WEIL]


def test_the_titled_card_is_never_a_pronunciation_headword():
    pron = {"id": "card_src_pron_messiah", "shelf": "pronunciation", "title": "messiah"}
    hymn = {"id": "card_hymn_messiah", "title": "Messiah (Handel)"}
    assert ask._prefer_the_titled_card([hymn, pron], "messiah") == [hymn, pron]


def test_shaping_keeps_the_titled_card_ahead_of_the_hub_lift(monkeypatch):
    """Through the whole shaping (steps 3-4½): the hub lift moves the connected hub to the front, and
    the titled card is then restored over it. Discernment (step 5) reads the live corpus's watch; an
    empty keeping has no charts, so it leaves the order as step 4½ made it."""
    class _NoCharts:
        cards = {}
    monkeypatch.setattr(ask.corpus, "default_corpus", lambda: _NoCharts())
    out = ask._shape_found_hits([_RH_Q, _RH_WEIL, _RH_HUB, _RH_NE], "the Riemann hypothesis", practical=False)
    assert out[0]["id"] == "card_question_riemann"
    assert {c["id"] for c in out} == {"card_question_riemann", "card_joint_weil_conjectures",
                                      "card_theory_differential_geometry", "card_theory_non_euclidean"}


def test_retrieval_fetches_the_card_the_asking_names(monkeypatch):
    """The subject search ("riemann hypothesis") lacked the titled card; one search on the asking as
    typed brings it, and only it — the rest of that search is discarded."""
    calls = []

    def _fake_search(q, limit=25, **kw):
        calls.append(q)
        return [_RH_Q, {"id": "card_other", "title": "something else"}]
    monkeypatch.setattr(ask.corpus, "search", _fake_search)
    out = ask._fetch_the_card_the_asking_names([_RH_WEIL, _RH_HUB], "the Riemann hypothesis",
                                               "riemann hypothesis", practical=False)
    assert [c["id"] for c in out] == ["card_question_riemann", "card_joint_weil_conjectures",
                                      "card_theory_differential_geometry"]
    assert calls == ["the Riemann hypothesis"]


def test_retrieval_never_searches_twice_without_cause(monkeypatch):
    """No second search for a question (no title is a question), a how-to, an asking that IS its
    subject, a long asking, a pool that already holds the titled card, or an empty pool."""
    def _never(q, limit=25, **kw):
        raise AssertionError("searched the asking as typed without cause: %r" % q)
    monkeypatch.setattr(ask.corpus, "search", _never)
    pool = [_RH_WEIL, _RH_HUB]
    f = ask._fetch_the_card_the_asking_names
    assert f(pool, "what is the Riemann hypothesis", "riemann hypothesis", False) == pool
    assert f(pool, "the Riemann hypothesis", "riemann hypothesis", True) == pool
    assert f(pool, "riemann hypothesis", "riemann hypothesis", False) == pool
    long = "the " + " ".join(["word"] * 13)
    assert f(pool, long, long.replace("the ", ""), False) == pool
    assert f([_RH_Q, _RH_WEIL], "the Riemann hypothesis", "riemann hypothesis", False) == [_RH_Q, _RH_WEIL]
    assert f([], "the Riemann hypothesis", "riemann hypothesis", False) == []


# THE ATTRIBUTION LEADS (2026-11-01). Measured live: "who composed the Messiah" led with the etymology row
# for the word, while WordNet's entry one seat back says "an oratorio composed by Handel in 1742"; "who wrote
# Pilgrims Progress" led with six connector cards (the map's edges) while Bunyan's book sits on the classics
# shelf, each section cited "John Bunyan, Pilgrim's Progress (1678)". The subject of "who <verb> X" is X; the
# ANSWER is X's attribution — the card about X that names who made it, or the work itself cited to its author.
_MESSIAH_ETYM = {"id": "card_src_etym_messiah", "shelf": "etymology", "title": "messiah",
                 "body": "messiah: etymology (Webster 1913) — n.: [Heb. mashiakh anointed, fr. mashakh to anoint. Cf. Messias.]"}
_MESSIAH_WORD = {"id": "card_src_word_messiah", "shelf": "dictionary", "title": "messiah",
                 "body": "messiah: (noun) any expected deliverer — syn: christ · (noun) the awaited king of the Jews "
                         "· (noun) an oratorio composed by Handel in 1742"}
_EASTON_MESSIAH = {"id": "card_enc_easton_messiah", "shelf": "encyclopedia", "title": "Messiah",
                   "body": "(Heb. mashiah), in all the thirty-nine instances of its occurring in the Old Testament, "
                           "is rendered by the LXX. 'Christos.'"}
_BUNYAN = {"id": "card_n_7f68f4020306", "shelf": "classics",
           "title": "Pilgrim's Progress §297: I saw also in my dream, that when the Shepherds perceived that they were wayfaring men,...",
           "body": "I saw also in my dream, that when the Shepherds perceived that they were wayfaring men, they also put questions to them",
           "source": {"label": "John Bunyan, Pilgrim's Progress (1678)", "ref": "§297"}}


def _edge(n):
    return {"id": "card_c_%d" % n, "shelf": "connections", "body": "the pilgrims went on",
            "title": "Pilgrim's Progress §%d: CHR. → Pilgrim's Progress §%d: CHR." % (n, n + 1)}


def _no_search(*a, **k):
    raise AssertionError("searched without cause: %r %r" % (a, k))


def test_attribution_leads_with_the_card_that_names_the_composer(monkeypatch):
    monkeypatch.setattr(ask.corpus, "search", _no_search)          # the pool already holds it: no search
    out = ask._attribution_leads([_MESSIAH_ETYM, _MESSIAH_WORD, _EASTON_MESSIAH], "who composed the Messiah", "messiah")
    assert [c["id"] for c in out] == ["card_src_word_messiah", "card_src_etym_messiah", "card_enc_easton_messiah"]
    # already leading: untouched
    hits = [_MESSIAH_WORD, _MESSIAH_ETYM]
    assert ask._attribution_leads(hits, "who composed the Messiah", "messiah") == hits


def test_attribution_never_leads_with_a_map_edge_and_fetches_the_work(monkeypatch):
    calls = []

    def _fake(q, limit=25, shelves=None, **kw):
        calls.append((q, bool(shelves) and "classics" in shelves))
        return [_BUNYAN]
    monkeypatch.setattr(ask.corpus, "search", _fake)
    edges = [_edge(212), _edge(23), _edge(148)]
    out = ask._attribution_leads(edges, "who wrote Pilgrims Progress", "pilgrims progress")
    assert out[0]["id"] == "card_n_7f68f4020306"
    assert out[0]["source"]["label"].startswith("John Bunyan")        # the work, cited to its author
    assert [c["id"] for c in out[1:]] == [c["id"] for c in edges]      # nothing dropped
    assert calls == [("pilgrims progress", True)]                      # ONE search, the works shelves


def test_attribution_is_inert_off_an_authorship_question(monkeypatch):
    monkeypatch.setattr(ask.corpus, "search", _no_search)
    hits = [_MESSIAH_ETYM, _MESSIAH_WORD]
    assert ask._attribution_leads(hits, "what is the messiah", "messiah") == hits
    assert ask._attribution_leads(hits, "who said blessed are the meek", "blessed meek") == hits   # a quotation: another door
    assert ask._attribution_leads([], "who composed the Messiah", "messiah") == []


def test_attribution_leaves_the_hits_when_nothing_carries_it(monkeypatch):
    monkeypatch.setattr(ask.corpus, "search", lambda *a, **k: [])
    # a novel ABOUT the theft of the painting: a works-shelf card, "by <Name>" in its header — but its title
    # never names the subject, so it is not the painter; the hits stand as they were (a miss stays a miss)
    novel = {"id": "card_src_book_43733", "shelf": "gutenberg",
             "title": "Das Geheimnis der Gioconda: Das Tagebuch des Diebes — Ernst Schwitzky",
             "body": "Das Geheimnis der Gioconda, by Ernst Bernhard Joseph Theodor Schwitzky (in de). Subjects: Art thefts -- Fiction"}
    assert ask._attribution_leads([novel, _EASTON_MESSIAH], "who painted the Mona Lisa", "mona lisa") == [novel, _EASTON_MESSIAH]


def test_by_name_prose_counts_as_the_attribution(monkeypatch):
    monkeypatch.setattr(ask.corpus, "search", _no_search)
    portrait = {"id": "card_src_word_mona_lisa", "shelf": "dictionary", "title": "mona lisa",
                "body": "mona lisa: (noun) a portrait by Leonardo da Vinci"}     # no "paint" word: "by <Name>" carries it
    out = ask._attribution_leads([_EASTON_MESSIAH, portrait], "who painted the Mona Lisa", "mona lisa")
    assert out[0]["id"] == "card_src_word_mona_lisa"
    assert ask._carries_the_attribution(_MESSIAH_WORD, "messiah", "composed") is True
    assert ask._carries_the_attribution(_MESSIAH_ETYM, "messiah", "composed") is False
    assert ask._carries_the_attribution(_edge(1), "pilgrims progress", "wrote") is False   # an edge, never


def test_the_noun_form_is_the_same_question():
    assert ask._authorship_verb("who was the composer of the Messiah") == "composed"
    assert ask._authorship_verb("Who wrote Pilgrim's Progress?") == "wrote"
    assert ask._authorship_verb("who is the author of Hebrews") == "wrote"
    assert ask._authorship_verb("who is the messiah") is None
    assert ask._authorship_verb("who said it is finished") is None
