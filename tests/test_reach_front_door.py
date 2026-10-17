"""THE REACH (issue #11, 2026-10-16). Thirteen domain verifiers were built, registered and pinned, and a person's
sentence never reached one of them: audit.extract had no extractor for their claim shapes. Now eleven of them are
reached from plain phrasings — every true claim HOLDS, every false twin BREAKS, and a clause with prose mixed into
it extracts NOTHING (whole-clause parsing only, the logic front door's bar). Two are left unreached on purpose:
pressure_fighting takes a 14-field closed-set observation and retrieval takes id lists — neither is a sentence.
Runs with no corpus."""
from __future__ import annotations

import os
import tempfile

TMP = tempfile.mkdtemp(prefix="nh-reach-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)

from concordance.audit import audit, extract  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig("secular")
_MATE = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"      # fool's mate
_STALE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"


def _v(text: str) -> str:
    return audit(text, CFG, seal=False, index=False, card=False)["verdict"]


def _names(text: str) -> set:
    return {s["extractor"] for s in extract(text)}


def test_linear_algebra_literals_parsed_whole():
    assert _v("the determinant of [[1,2],[3,4]] is -2") == "HOLDS"
    assert _v("det([[2,0],[0,3]]) = 6") == "HOLDS"
    assert _v("the trace of [[1,2],[3,4]] is 5") == "HOLDS"
    assert _v("the dot product of [1,2,3] and [4,5,6] is 32") == "HOLDS"
    assert _v("[1,2,3] · [4,5,6] = 32") == "HOLDS"
    assert _v("the magnitude of [3,4] is 5") == "HOLDS"
    assert _v("the angle between [1,0] and [0,1] is 90 degrees") == "HOLDS"
    assert _v("the 3x3 identity matrix has trace 3") == "HOLDS"
    assert _v("the determinant of the 4x4 identity matrix is 1") == "HOLDS"
    assert _v("the determinant of [[1,2],[3,4]] is 2") == "BROKEN"
    assert _v("the dot product of [1,2,3] and [4,5,6] is 30") == "BROKEN"
    assert _v("the 3x3 identity matrix has trace 4") == "BROKEN"
    assert extract("the determinant of [[1,2],[3,4]] and the weather is -2") == []
    assert extract("the determinant of [[1,2,3],[4,5,6]] is 0") == []           # not square: refused, never guessed


def test_chess_reaches_the_perft_proven_engine():
    assert _v("in the starting position, e2e4 is a legal move") == "HOLDS"
    assert _v("e2e5 is not a legal move from the starting position") == "HOLDS"
    assert _v("from the starting position g1f3 is legal") == "HOLDS"
    assert _v(f"the position {_MATE} is checkmate") == "HOLDS"
    assert _v(f"the position {_STALE} is a stalemate") == "HOLDS"
    assert _v(f"the position {_STALE} is not checkmate") == "HOLDS"
    assert _v("in the starting position, e2e5 is a legal move") == "BROKEN"
    assert _v("e1e2 is a legal move from the starting position") == "BROKEN"
    assert _v(f"the position {_STALE} is checkmate") == "BROKEN"
    assert extract("in the starting position, the knight e2e4 is a legal move") == []


def test_condensed_matter_constants_through_h_e_and_alpha():
    assert _v("the von Klitzing constant is 25812.807 ohms") == "HOLDS"
    assert _v("the von Klitzing constant is 25.812807 kΩ") == "HOLDS"
    assert _v("the Josephson constant is 483597.8 GHz/V") == "HOLDS"
    assert _v("the Josephson constant is 483.5978 THz per volt") == "HOLDS"
    assert _v("by the Dulong-Petit law the molar heat capacity of a solid is about 24.9 J/(mol K)") == "HOLDS"
    assert _v("the Dulong-Petit limit is 3R = 24.94 J/mol/K") == "HOLDS"
    assert _v("at filling factor 2 the Hall resistance is 12906.4 ohms") == "HOLDS"
    assert _v("the nu = 1 quantum Hall plateau is at 25812.8 ohms") == "HOLDS"
    assert _v("the von Klitzing constant is 25000 ohms") == "BROKEN"
    assert _v("the Josephson constant is 400000 GHz/V") == "BROKEN"
    assert _v("the Dulong-Petit limit is 12 J/(mol K)") == "BROKEN"
    assert _v("at filling factor 2 the Hall resistance is 25812.8 ohms") == "BROKEN"
    assert extract("the von Klitzing constant of the sample is 25812.807 ohms") == []


def test_cybersecurity_tables_and_entropy():
    assert _v("a /24 subnet has 254 usable hosts") == "HOLDS"
    assert _v("a /30 network has 2 usable hosts") == "HOLDS"
    assert _v("a /16 has 65,534 hosts") == "HOLDS"
    assert _v("port 443 is a well-known port") == "HOLDS"
    assert _v("port 8080 is a registered port") == "HOLDS"
    assert _v("TCP port 50000 is an ephemeral port") == "HOLDS"
    assert _v("a CVSS score of 9.1 is critical") == "HOLDS"
    assert _v("a CVSS base score of 5.0 is medium") == "HOLDS"
    assert _v("TLS 1.0 is deprecated") == "HOLDS"
    assert _v("TLS 1.3 is recommended") == "HOLDS"
    assert _v("SSL 3 is insecure") == "HOLDS"
    assert _v("a 16-character password from a 94-character set has 104.9 bits of entropy") == "HOLDS"
    assert _v("a 10-character lowercase password has 47 bits of entropy") == "HOLDS"
    assert _v("a 12-character password drawn from a 62-character alphabet has an entropy of about 71.5 bits") == "HOLDS"
    assert _v("a /24 subnet has 256 usable hosts") == "BROKEN"
    assert _v("port 443 is a registered port") == "BROKEN"
    assert _v("a CVSS score of 9.1 is medium") == "BROKEN"
    assert _v("TLS 1.3 is deprecated") == "BROKEN"
    assert _v("a 16-character password from a 94-character set has 128 bits of entropy") == "BROKEN"
    assert extract("a /24 subnet in the office has 254 usable hosts") == []
    assert extract("a /24 subnet has 256 addresses") == []                        # the total, not the verifier's usable count


def test_document_validation_checksums():
    assert _v("ISBN 0-306-40615-2 is valid") == "HOLDS"
    assert _v("ISBN 978-0-306-40615-7 is valid") == "HOLDS"
    assert _v("ISBN-10 0306406152 is a valid ISBN") == "HOLDS"
    assert _v("ISBN 0-306-40615-3 is invalid") == "HOLDS"
    assert _v("79927398713 passes the Luhn check") == "HOLDS"
    assert _v("the card number 4532 0151 1283 0366 is valid") == "HOLDS"
    assert _v("UPC 036000291452 is valid") == "HOLDS"
    assert _v("ISBN 0-306-40615-3 is valid") == "BROKEN"
    assert _v("ISBN 978-0-306-40615-8 is valid") == "BROKEN"
    assert _v("79927398714 passes the Luhn check") == "BROKEN"
    assert _v("UPC 036000291453 is valid") == "BROKEN"
    assert extract("ISBN 0-306-40615-2 of the book is valid") == []
    assert extract("ISBN-13 0306406152 is valid") == []                            # ten digits labelled 13: refused


def test_manufacturing_sigma_spc_and_rss():
    assert _v("a DPMO of 233 is a 5 sigma level") == "HOLDS"
    assert _v("six sigma is 3.4 defects per million opportunities") == "HOLDS"
    assert _v("6210 defects per million opportunities corresponds to 4 sigma") == "HOLDS"
    assert _v("with a mean of 100 and a standard deviation of 2, the 3-sigma control limits are 94 and 106") == "HOLDS"
    assert _v("a process with mean 100 and sigma 2 has 2-sigma control limits of 96 and 104") == "HOLDS"
    assert _v("the RSS stack-up of tolerances 0.1, 0.2 and 0.2 is 0.3") == "HOLDS"
    assert _v("tolerances of 0.1, 0.2 and 0.2 stack up to an RSS of 0.3") == "HOLDS"
    assert _v("a DPMO of 233 is a 3 sigma level") == "BROKEN"
    assert _v("six sigma is 233 defects per million opportunities") == "BROKEN"
    assert _v("with a mean of 100 and a standard deviation of 2, the 3-sigma control limits are 96 and 104") == "BROKEN"
    assert _v("the RSS stack-up of tolerances 0.1, 0.2 and 0.2 is 0.5") == "BROKEN"
    assert extract("a DPMO of 233 at the plant is a 5 sigma level") == []


def test_molecular_geometry_from_axe_notation_and_words():
    assert _v("an AX4 molecule is tetrahedral with 109.5° bond angles") == "HOLDS"
    assert _v("AX2E2 is bent") == "HOLDS"
    assert _v("AX3E is trigonal pyramidal") == "HOLDS"
    assert _v("an AX6 molecule is octahedral with 90 degree bond angles") == "HOLDS"
    assert _v("a molecule with 4 bonding pairs and no lone pairs is tetrahedral") == "HOLDS"
    assert _v("four bonding domains and zero lone pairs give a tetrahedral geometry with bond angles of 109.5 degrees") == "HOLDS"
    assert _v("a molecule with 2 bonding pairs and 2 lone pairs is bent with 104.5 degree bond angles") == "HOLDS"
    assert _v("an AX4 molecule is linear") == "BROKEN"
    assert _v("AX2E2 is linear") == "BROKEN"
    assert _v("a molecule with 4 bonding pairs and no lone pairs is tetrahedral with 120 degree bond angles") == "BROKEN"
    assert extract("an AX4 molecule like methane is tetrahedral") == []
    # the verifier's table gives trigonal bipyramidal no single angle, so an angle claim on it is not extracted
    assert extract("an AX5 molecule is trigonal bipyramidal with 120 degree bond angles") == []


def test_philosophy_ethical_framework_catalogue():
    assert _v("consequentialism judges actions by their outcomes") == "HOLDS"
    assert _v("virtue ethics is not about outcomes") == "HOLDS"
    assert _v("deontology does not judge actions by their consequences") == "HOLDS"
    assert _v("contractarianism is not focused on outcomes") == "HOLDS"
    assert _v("deontology judges actions solely by their consequences") == "BROKEN"
    assert _v("consequentialism is not about outcomes") == "BROKEN"
    assert extract("consequentialism, some say, judges actions by their outcomes") == []


def test_photonics_photon_energy_through_h():
    assert _v("a 500 nm photon has energy 2.48 eV") == "HOLDS"
    assert _v("the energy of a 1550 nm photon is 0.8 eV") == "HOLDS"
    assert _v("a 600 THz photon has energy 2.48 eV") == "HOLDS"
    assert _v("a photon with a wavelength of 0.5 µm carries an energy of 2.48 eV") == "HOLDS"
    assert _v("light at 1 nm has photon energy 1.24 keV") == "HOLDS"
    assert _v("a 500 nm photon has energy 5 eV") == "BROKEN"
    assert _v("the energy of a 1550 nm photon is 2.48 eV") == "BROKEN"
    assert extract("a 500 nm photon in glass has energy 2.48 eV") == []


def test_sports_analytics_games_behind_elo_and_pythagorean():
    assert _v("a team at 45-35 is 5 games behind a leader at 50-30") == "HOLDS"
    assert _v("the 45-35 team is 5 games behind the 50-30 leader") == "HOLDS"
    assert _v("a 1600-rated player is expected to score 0.64 against a 1500-rated player") == "HOLDS"
    assert _v("a 1500 player against a 1600 player has an expected score of 0.36") == "HOLDS"
    assert _v("a 1600 Elo player is expected to score 64% against a 1500 Elo player") == "HOLDS"
    assert _v("a team that scored 750 runs and allowed 600 has a Pythagorean winning percentage of .610") == "HOLDS"
    assert _v("the Pythagorean expectation for 100 runs scored and 80 runs allowed is .610") == "HOLDS"
    assert _v("a team at 45-35 is 3 games behind a leader at 50-30") == "BROKEN"
    assert _v("a 1600-rated player is expected to score 0.5 against a 1500-rated player") == "BROKEN"
    assert _v("a team that scored 750 runs and allowed 600 has a Pythagorean winning percentage of .500") == "BROKEN"
    assert extract("a team at 45-35 in June is 5 games behind a leader at 50-30") == []
    assert extract("a team that scored 750 runs and allowed 600 has a winning percentage of .610") == []   # no "Pythagorean": no exponent


def test_archaeology_decay_clock():
    assert _v("a sample with 25% of its carbon-14 remaining is about 11,460 years old") == "HOLDS"
    assert _v("25% remaining carbon-14 is about 11460 years") == "HOLDS"
    assert _v("if 50% of the carbon-14 remains, the sample is 5730 years old") == "HOLDS"
    assert _v("a bone with half of its radiocarbon left dates to 5730 years") == "HOLDS"
    assert _v("12.5% remaining is 3 half-lives") == "HOLDS"
    assert _v("after 3 half-lives, only 12.5% of the original sample remains") == "HOLDS"
    assert _v("with a half-life of 1.25 billion years, 50% remaining is 1.25 billion years old") == "HOLDS"
    assert _v("a sample with 25% of its carbon-14 remaining is about 5730 years old") == "BROKEN"
    assert _v("12.5% remaining is 2 half-lives") == "BROKEN"
    assert _v("with a half-life of 1.25 billion years, 50% remaining is 2.5 billion years old") == "BROKEN"
    assert extract("a sample with 25% of its carbon-14 remaining in the lab is about 11460 years old") == []


def test_the_extractors_name_themselves_and_only_themselves():
    cases = {
        "linear_algebra": "the determinant of [[1,2],[3,4]] is -2",
        "chess": "in the starting position, e2e4 is a legal move",
        "condensed_matter": "the von Klitzing constant is 25812.807 ohms",
        "cybersecurity": "a /24 subnet has 254 usable hosts",
        "document_validation": "ISBN 0-306-40615-2 is valid",
        "manufacturing": "a DPMO of 233 is a 5 sigma level",
        "molecular_geometry": "an AX4 molecule is tetrahedral with 109.5° bond angles",
        "philosophy": "consequentialism judges actions by their outcomes",
        "photonics": "a 500 nm photon has energy 2.48 eV",
        "sports_analytics": "a team at 45-35 is 5 games behind a leader at 50-30",
        "archaeology": "25% remaining carbon-14 is about 11460 years",
    }
    for name, text in cases.items():
        steps = extract(text)
        assert [s["extractor"] for s in steps] == [name], (name, steps)     # one extractor, no older one co-firing
        assert steps[0]["domain"] == name
