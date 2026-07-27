"""Dates — verified answers for major events. The two things that MUST hold: the dates it gives are
correct, and it DECLINES the unknown rather than guess a year (the moat never states a falsehood)."""
from concordance import dates, ask
from concordance.config import EngineConfig


def test_major_dates_are_accurate():
    assert "1945" in dates.answer("when did World War 2 end")
    assert "1939" in dates.answer("when did World War 2 start")
    assert "1914" in dates.answer("when did WW1 begin")
    assert "1918" in dates.answer("when did World War I end")
    assert "1912" in dates.answer("what year did the Titanic sink")
    assert "1969" in dates.answer("when was the moon landing")
    assert "1989" in dates.answer("when did the Berlin Wall fall")
    assert "1776" in dates.answer("when was the Declaration of Independence signed")
    assert "1066" in dates.answer("what year was the Battle of Hastings")


def test_declines_the_unknown_and_never_guesses():
    # unknown events → None (a wrong year would break the core promise)
    assert dates.answer("when did the Battle of Zorptania end") is None
    assert dates.answer("when did my grandmother move to town") is None
    # not a date question at all
    assert dates.answer("what is World War 2") is None
    assert dates.answer("who won World War 2") is None
    # a 'when' with no known event must not hijack pastoral/other routing
    assert dates.answer("when should I pray") is None
    assert dates.answer("when will I feel better") is None


def test_routes_through_the_front_door():
    assert ask.classify("when did World War 2 end") == "date"
    d = ask.respond("when did World War 2 end", EngineConfig(), gate_open=True)
    assert d.get("kind") == "date" and "1945" in (d.get("message") or "")
    # a non-event 'when' must NOT be classified as a date
    assert ask.classify("when should I pray") != "date"
