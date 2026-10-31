#!/usr/bin/env python3
"""ONE BODY, MANY MANNERS — a LoRA adapter per expert face (Matt, 2026-10-31: "We need to build a LoRA adapter. for
each."), over one shared small base. The adapters are FUEL, not core: they live outside src/concordance's runtime
(zero model calls at the verifier core stays pinned), and an adapter may only RE-VOICE content the engine has already
found and gated — every fact in its output traces to a card (the airlock). This is the looped-transformer picture
(one tied block, a small depth-wise LoRA per use; Bae et al. 2024) carried over to the village: the same body, a
different manner per character, each learned from that character's own corpus — the found sayings
(data/faces/responses/<face>.jsonl, cited) and the operator's frames (data/faces/frames/<face>.txt, local).

    PYTHONPATH=src python tools/face_lora.py build [--data data] [--out data/faces/lora]     # per-face train.jsonl
    PYTHONPATH=src python tools/face_lora.py train --face face_coach [--base <hf id>] [--epochs 3] [--dry-run]
    PYTHONPATH=src python tools/face_lora.py status

build writes, per face, rows {"face", "prompt", "completion", "cite", "kind"}: the prompt names the face and its
manner; the completion is the line itself; "cite" is the card id (or "operator" for a frame). train runs PEFT LoRA
(r=16, alpha=32, dropout 0.05, q/k/v/o projections) on a permissively licensed small base — needs torch + peft +
transformers, a GPU to be quick; --dry-run only reports what it would train. Nothing here is imported by the engine.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_BASE = "HuggingFaceTB/SmolLM2-1.7B-Instruct"     # Apache-2.0; Qwen/Qwen2.5-1.5B-Instruct is the other fit
LORA = {"r": 16, "lora_alpha": 32, "lora_dropout": 0.05, "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"]}


def _manner(face: str) -> str:
    from concordance import faces
    f = faces.faces().get(face) or {}
    return str(f.get("manner") or "")


def build_rows(face: str, responses: List[Dict[str, Any]], frames: List[str]) -> List[Dict[str, Any]]:
    """The training rows for one face. A found line keeps its card as the citation; a frame is the operator's own
    line ("operator"). A line without text, or a found line without a card, is dropped — never a fabricated cite."""
    manner = _manner(face)
    head = f"You are {face.replace('face_', 'the ')}. {manner}".strip()
    rows: List[Dict[str, Any]] = []
    seen = set()
    for r in responses:
        text, card = str(r.get("text") or "").strip(), str(r.get("card") or "").strip()
        if not text or not card or text.lower() in seen:
            continue
        seen.add(text.lower())
        rows.append({"face": face, "prompt": f"{head}\nSpeak one line in this manner, from the keeping ({r.get('shelf', '')}).",
                     "completion": text, "cite": card, "kind": "found"})
    for line in frames:
        text = str(line or "").strip()
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        rows.append({"face": face, "prompt": f"{head}\nSpeak one line in this manner, in your own frame.",
                     "completion": text, "cite": "operator", "kind": "frame"})
    return rows


def _read_jsonl(p: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not p.exists():
        return out
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def build(data: Path, out: Path) -> Dict[str, int]:
    from concordance import faces
    counts: Dict[str, int] = {}
    for face in sorted(faces.faces()):
        responses = _read_jsonl(data / "faces" / "responses" / f"{face}.jsonl")
        # the frames: the tracked, operator-reviewed data/face_frames.json (every slot's variants), plus any local
        # data/faces/frames/<face>.txt the operator keeps beside it
        frames = [v for variants in faces.frames(face).values() for v in variants]
        fp = data / "faces" / "frames" / f"{face}.txt"
        if fp.exists():
            frames += [l for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]
        rows = build_rows(face, responses, frames)
        d = out / face
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "train.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        counts[face] = len(rows)
    return counts


def train(face: str, base: str, epochs: int, out: Path, dry_run: bool) -> int:
    rows = _read_jsonl(out / face / "train.jsonl")
    print(f"{face}: {len(rows)} rows ({sum(1 for r in rows if r['kind'] == 'found')} found, {sum(1 for r in rows if r['kind'] == 'frame')} frames) base={base} lora={LORA} epochs={epochs}")
    if not rows:
        print("  nothing to train — run `build` first (and the finder on the box)", file=sys.stderr)
        return 2
    if dry_run:
        return 0
    try:
        import torch  # type: ignore
        from datasets import Dataset  # type: ignore
        from peft import LoraConfig, get_peft_model  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments  # type: ignore
    except ImportError as e:
        print(f"  training stack missing ({e}); install torch, transformers, peft, datasets — or use --dry-run", file=sys.stderr)
        return 3
    tok = AutoTokenizer.from_pretrained(base)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32)
    model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", **LORA))

    def enc(r):
        text = f"{r['prompt']}\n{r['completion']}{tok.eos_token}"
        x = tok(text, truncation=True, max_length=384)
        x["labels"] = x["input_ids"].copy()
        return x

    ds = Dataset.from_list(rows).map(enc, remove_columns=["face", "prompt", "completion", "cite", "kind"])
    args = TrainingArguments(output_dir=str(out / face / "run"), num_train_epochs=epochs, per_device_train_batch_size=4,
                             learning_rate=2e-4, logging_steps=10, save_strategy="no", report_to=[], bf16=torch.cuda.is_available())
    Trainer(model=model, args=args, train_dataset=ds, tokenizer=tok).train()
    model.save_pretrained(str(out / face / "adapter"))
    print(f"  adapter saved: {out / face / 'adapter'}")
    return 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "train", "status"))
    ap.add_argument("--data", default=os.environ.get("CONCORDANCE_DATA_DIR") or str(ROOT / "data"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--face", default=None)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = Path(a.data)
    out = Path(a.out) if a.out else data / "faces" / "lora"
    if a.cmd == "build":
        counts = build(data, out)
        for face, n in counts.items():
            print(f"  {face:<20} {n:>4} rows")
        print(f"total {sum(counts.values())} rows → {out}")
        return 0
    if a.cmd == "status":
        for d in sorted(out.glob("face_*")):
            n = len(_read_jsonl(d / "train.jsonl"))
            print(f"  {d.name:<20} {n:>4} rows   adapter {'yes' if (d / 'adapter').exists() else 'no'}")
        return 0
    if not a.face:
        print("train needs --face", file=sys.stderr)
        return 2
    return train(a.face, a.base, a.epochs, out, a.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
