#!/usr/bin/env python3
"""align_words.py - word-level timestamps for karaoke subtitles.

Uses torchaudio's MMS_FA forced aligner (wav2vec2, CTC forced alignment) on each narrated line,
so every word gets a real start/end time from the audio (never estimated from word length).
The model (~1.2 GB) is downloaded once by install.sh into $VSP_CACHE/torch (TORCH_HOME).

Output: align/words.json = [{line_index, word, start, end, score}, ...] (seconds, whole-video timeline)
Usage: python scripts/align_words.py --project DIR [--force]
"""
import argparse, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from vsp_common import load_project, cache_dir, note
os.environ.setdefault("TORCH_HOME", str(cache_dir() / "torch"))
import numpy as np
import soundfile as sf
import torch, torchaudio

TOKEN = r"[^\W_]+(?:'[^\W_]+)?"

def norm(w):
    w = unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", w)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--project", default="."); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    root, _ = load_project(a.project)
    meta = json.loads((root / "audio/voice_meta.json").read_text())
    out = root / "align/words.json"
    if not a.force and out.exists() and json.loads(out.read_text() or "{}").get("key") == meta["key"]:
        print("align: up to date, skipped"); return
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model().to("cpu"); tokenizer = bundle.get_tokenizer(); aligner = bundle.get_aligner()
    words = []
    for li, line in enumerate(meta["lines"], 1):
        audio, sr = sf.read(root / f"audio/line_{li:02d}.wav", dtype="float32")
        a16 = torchaudio.functional.resample(torch.from_numpy(audio), sr, 16000)
        tokens = [m.group() for m in re.finditer(TOKEN, line)]
        keep = [(t, norm(t)) for t in tokens if norm(t)]   # numbers/symbols must be spelled out in the script
        if len(keep) != len(tokens):
            print(f"WARNING line {li}: tokens without letters skipped (spell numbers as words): {[t for t in tokens if not norm(t)]}")
        with torch.inference_mode():
            emission, _ = model(a16.unsqueeze(0))
        emission = emission[0].cpu()
        spans = aligner(emission, tokenizer([n for _, n in keep]))
        step = len(audio) / sr / emission.shape[0]
        for (w, _), ss in zip(keep, spans):
            words.append({"line_index": li, "word": w,
                          "start": round(meta["offsets"][li - 1] + ss[0].start * step, 4),
                          "end": round(meta["offsets"][li - 1] + ss[-1].end * step, 4),
                          "score": round(float(np.mean([s.score for s in ss])), 3)})
        print(f"line {li}: {len(keep)} words aligned", flush=True)
    assert all(b["start"] >= a_["start"] for a_, b in zip(words, words[1:])), "word starts not monotonic"
    matched = len(words) / max(1, meta["word_count"])
    (root / "align").mkdir(exist_ok=True)
    out.write_text(json.dumps({"key": meta["key"], "matched_fraction": round(matched, 4), "words": words}, indent=2) + "\n")
    note(root, f"align: {len(words)}/{meta['word_count']} words ({matched:.1%})")
    print(f"aligned {len(words)} of {meta['word_count']} words ({matched:.1%})")
    if matched < 0.97: sys.exit("FAIL: fewer than 97% of words aligned")

if __name__ == "__main__":
    main()
