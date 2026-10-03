"""THE OPENAI-COMPATIBLE DOOR (Matt, 2026-10-03: "lean into the open doors"). The shape every chat client
speaks, answered by the engine with no model behind it: the last user turn walks the same front door a
person does; the reply is composed of the answer's own found text; the structured answer rides along;
nothing is generated; streaming is one chunk and [DONE]."""
import os
import tempfile

os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-oai-"))

from concordance.engine import EngineConfig  # noqa: E402
from concordance.web import api, openai_door as od  # noqa: E402

SEC = EngineConfig("secular")


def _chat(text, **extra):
    body = {"model": "narrow-highway", "messages": [{"role": "system", "content": "x"},
                                                     {"role": "user", "content": text}], **extra}
    return api.dispatch("POST", "/v1/chat/completions", {}, body, SEC)[:2]


def test_the_models_list_names_the_one_model_and_says_there_is_no_model():
    st, p = api.dispatch("GET", "/v1/models", {}, None, SEC)[:2]
    assert st == 200 and p["object"] == "list" and p["data"][0]["id"] == "narrow-highway"
    assert "never generates" in p["data"][0]["note"]


def test_a_sum_comes_back_in_the_openai_shape_with_the_answer_riding_along():
    st, p = _chat("what is 15 percent of 240")
    assert st == 200 and p["object"] == "chat.completion" and p["model"] == "narrow-highway"
    msg = p["choices"][0]["message"]
    assert msg["role"] == "assistant" and "36" in msg["content"] and p["choices"][0]["finish_reason"] == "stop"
    assert p["generated"] is False and p["usage"]["total_tokens"] == 0
    nh = p["narrow_highway"]
    assert nh["kind"] in ("compute", "verify") and nh["generated"] is False
    assert nh["house"]["door"] == "WALK" and nh["house"]["next_step"]["do"]      # the ending rides along


def test_a_cry_is_answered_with_help_first_through_this_door_too():
    st, p = _chat("i want to end my life")
    content = p["choices"][0]["message"]["content"]
    assert st == 200 and content.startswith("You matter") and "988" in content
    assert p["narrow_highway"]["kind"] == "crisis"
    assert p["narrow_highway"]["house"]["next_step"]["do"].startswith("Reach a real person right now")


def test_streaming_is_one_chunk_then_done():
    st, p = _chat("what is 8 times 7", stream=True)
    assert st == 200 and isinstance(p.get("_sse"), list) and len(p["_sse"]) == 3
    assert p["_sse"][0].startswith("data: ") and '"delta": {"role": "assistant", "content": "' in p["_sse"][0]
    assert "56" in p["_sse"][0] and '"finish_reason": "stop"' in p["_sse"][1] and p["_sse"][2] == "data: [DONE]\n\n"


def test_content_parts_and_the_last_user_turn_are_read():
    msgs = [{"role": "user", "content": "first"},
            {"role": "assistant", "content": "x"},
            {"role": "user", "content": [{"type": "text", "text": "what is"}, {"type": "text", "text": "2 plus 2"}]}]
    assert od.last_user_text(msgs) == "what is 2 plus 2"
    assert od.last_user_text([{"role": "assistant", "content": "only"}]) == ""
    st, p = api.dispatch("POST", "/v1/chat/completions", {}, {"messages": [{"role": "assistant", "content": "x"}]}, SEC)[:2]
    assert st == 400 and "user turn" in p["error"]
    st, p = api.dispatch("POST", "/v1/chat/completions", {}, "not a dict", SEC)[:2]
    assert st == 400


def test_render_composes_only_the_answers_own_text_in_reading_order():
    answer = {"kind": "found", "message": "Here's the clearest thing the keeping holds on this:",
              "lead": {"title": "Making water safe to drink", "excerpt": "Boil it for one minute.",
                       "source": {"label": "US Army FM 21-76", "url": "https://example.org/fm"}},
              "scripture": [{"ref": "John 4:14", "text": "whoever drinks of the water that I will give him"}],
              "results": [{"id": "c1", "title": "Making water safe to drink"}],
              "path": {"step": "Open 'Making water safe to drink' — it has the steps, in its source's own words."},
              "seal": {"cite_url": "https://narrowhighway.org/s/abc"},
              "house": {"next_step": {"do": "open the top card"}}}
    text = od.render(answer)
    lines = text.splitlines()
    assert lines[0].startswith("Here's the clearest") and "Making water safe to drink" in text
    assert "Boil it for one minute." in text and "Source: US Army FM 21-76 https://example.org/fm" in text
    assert "John 4:14 — whoever drinks" in text
    assert text.index("Boil it") < text.index("John 4:14") < text.index("Next: Open") < text.index("Seal: https://narrowhighway.org/s/abc")
    assert text.rstrip().endswith("One step: open the top card")
    assert od.render({}) .startswith("Nothing found in the keeping")       # an empty answer invents nothing
