"""FORMAL LOGIC AS A STRENGTH (Matt, 2026-10-08). The front door reached 3 of 15 logic phrasings; now the ways
people actually write about propositional logic reach the truth-table verifier and the syllogism table, and every
false twin breaks honestly. Runs with no corpus."""
from __future__ import annotations

import os
import tempfile

TMP = tempfile.mkdtemp(prefix="nh-logic-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)

from concordance.audit import audit, extract  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig("secular")


def _v(text: str) -> str:
    return audit(text, CFG, seal=False, index=False, card=False)["verdict"]


def test_relations_equivalent_and_entails():
    assert _v("P implies Q is equivalent to not Q implies not P") == "HOLDS"          # contraposition
    assert _v("not (P and Q) is equivalent to not P or not Q") == "HOLDS"             # De Morgan
    assert _v("P or Q is equivalent to P and Q") == "BROKEN"
    assert _v("P implies Q is not equivalent to Q implies P") == "HOLDS"              # the converse is not equivalent
    assert _v("P and Q entails P") == "HOLDS"
    assert _v("P entails P and Q") == "BROKEN"
    assert _v("P does not entail P and Q") == "HOLDS"
    assert _v("P and (P implies Q) entails Q") == "HOLDS"                             # modus ponens as entailment


def test_argument_forms_are_judged_by_entailment():
    assert _v("If P then Q; P; therefore Q is valid") == "HOLDS"
    assert _v("If P then Q; Q; therefore P is a valid argument") == "BROKEN"         # affirming the consequent
    assert _v("If P then Q; Q; therefore P is invalid") == "HOLDS"
    assert _v("If P then Q; not Q; therefore not P is valid") == "HOLDS"             # modus tollens
    assert _v("If P then Q, and if Q then R, therefore if P then R is valid") == "HOLDS"   # hypothetical syllogism
    assert _v("P or Q; not P; therefore Q is a valid inference") == "HOLDS"          # disjunctive syllogism
    assert _v("P or Q; P; therefore not Q is valid") == "BROKEN"                     # affirming a disjunct
    # ordinary prose with 'therefore' is not an argument form: nothing extracted
    assert _v("The total is 4; therefore the claim is valid") == "NOTHING_TO_CHECK"


def test_categorical_syllogisms():
    assert _v("All men are mortal; Socrates is a man; therefore Socrates is mortal is valid") == "HOLDS"
    assert _v("All cats are mammals; all mammals are animals; therefore all cats are animals is a valid syllogism") == "HOLDS"
    assert _v("All mammals are animals; all cats are mammals; therefore all cats are animals is valid") == "HOLDS"   # major first
    assert _v("All cats are mammals; all dogs are mammals; therefore all cats are dogs is valid") == "BROKEN"       # undistributed middle
    assert _v("All cats are mammals; all dogs are mammals; therefore all cats are dogs is invalid") == "HOLDS"
    assert _v("No fish are mammals; all whales are mammals; therefore no whales are fish is valid") == "HOLDS"      # Cesare


def test_truth_table_counts_and_named_forms():
    assert _v("A truth table for 3 variables has 8 rows") == "HOLDS"
    assert _v("A truth table for 3 variables has 6 rows") == "BROKEN"
    assert _v("there are 16 binary boolean functions") == "HOLDS"
    assert _v("there are 8 binary boolean functions") == "BROKEN"
    assert _v("there are 4 unary boolean functions") == "HOLDS"
    assert _v("a formula with 4 variables has 16 possible assignments") == "HOLDS"
    assert _v("modus ponens is valid") == "HOLDS"
    assert _v("modus ponens is a fallacy") == "BROKEN"
    assert _v("affirming the consequent is a fallacy") == "HOLDS"
    assert _v("affirming the consequent is valid") == "BROKEN"
    assert _v("denying the antecedent is not valid") == "HOLDS"
    assert _v("modus tollens is a valid form") == "HOLDS"
    assert _v("ad hominem is an informal fallacy") == "HOLDS"
    assert _v("affirming the consequent is a formal fallacy") == "HOLDS"
    assert _v("ad hominem is a formal fallacy") == "BROKEN"


def test_the_extractors_name_themselves_and_parse_whole_clauses_only():
    names = {s["extractor"] for s in extract("P and Q entails P. If P then Q; P; therefore Q is valid. "
                                             "All men are mortal; Socrates is a man; therefore Socrates is mortal is valid.")}
    assert {"logic_relations", "argument_form", "syllogism"} <= names
    # a clause with prose inside it does not parse, so nothing is extracted from it
    assert extract("P and the moon is equivalent to Q") == []
    assert extract("If it rains then P; P; therefore Q is valid") == []
