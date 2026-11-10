#!/usr/bin/env python3
"""clipmeter: measure a short video instead of guessing. Needs only ffmpeg/ffprobe (and optionally faster-whisper for words per second).
Usage:  python clipmeter.py clip.mp4 [more.mp4 ...] [--words] [--json out.json]
Prints per clip: length, hard cuts and cuts per 10 s, average brightness / contrast / saturation, motion (share of frames with camera movement),
loudness, share of silence, and with --words the speaking speed (words per second). Several clips -> averages = your rule book numbers.
"""
import json, re, subprocess, sys, statistics as st
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def duration(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]).stdout.strip())

def cuts(f, thr=0.35):
    r = run(["ffmpeg", "-hide_banner", "-i", str(f), "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]

def signal_stats(f):
    r = run(["ffmpeg", "-hide_banner", "-i", str(f), "-vf", "fps=4,signalstats,metadata=print:file=-", "-an", "-f", "null", "-"])
    out = r.stdout + r.stderr
    def vals(key):
        return [float(x) for x in re.findall(r"lavfi\.signalstats\." + key + r"=([0-9.]+)", out)]
    y, yl, yh, sat = vals("YAVG"), vals("YLOW"), vals("YHIGH"), vals("SATAVG")
    # motion = how much consecutive sampled frames differ (mean abs diff of average luma is too coarse, so use the scene-change score)
    return {"brightness": round(st.mean(y), 1) if y else None, "contrast": round(st.mean([h - l for h, l in zip(yh, yl)]), 1) if y else None,
            "saturation": round(st.mean(sat), 1) if sat else None}

def motion(f):
    r = run(["ffmpeg", "-hide_banner", "-i", str(f), "-vf", "fps=10,select='gte(scene,0)',metadata=print:file=-", "-an", "-f", "null", "-"])
    sc = [float(x) for x in re.findall(r"lavfi\.scene_score=([0-9.]+)", r.stdout + r.stderr)]
    if not sc:
        return None
    moving = sum(1 for s in sc if 0.004 < s < 0.35)
    return round(100 * moving / len(sc), 1)

def audio(f, dur):
    r = run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", "silencedetect=n=-35dB:d=0.3,ebur128=peak=true", "-vn", "-f", "null", "-"])
    sil = sum(float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", r.stderr))
    lufs = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    return {"loudness_lufs": float(lufs[-1]) if lufs else None, "silence_pct": round(100 * sil / dur, 1)}

def words_per_second(f):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    tmp = Path(f).with_suffix(".16k.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", "16000", str(tmp)])
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(str(tmp), vad_filter=True, beam_size=1)
    n = sum(len(s.text.split()) for s in segs)
    tmp.unlink(missing_ok=True)
    return n

def measure(f, want_words):
    d = duration(f)
    c = cuts(f)
    m = {"file": Path(f).name, "seconds": round(d, 1), "hard_cuts": len(c), "cuts_per_10s": round(10 * len(c) / d, 2)}
    m.update(signal_stats(f)); m["moving_frames_pct"] = motion(f); m.update(audio(f, d))
    if want_words:
        n = words_per_second(f)
        if n is not None:
            m["words_per_second"] = round(n / d, 2)
    return m

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_words = "--words" in sys.argv
    outp = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if outp and outp in args:
        args.remove(outp)
    res = [measure(a, want_words) for a in args]
    for r in res:
        print(json.dumps(r, ensure_ascii=False))
    if len(res) > 1:
        avg = {k: round(st.mean([r[k] for r in res if r.get(k) is not None]), 2) for k in res[0] if k != "file" and isinstance(res[0][k], (int, float))}
        print("AVERAGE:", json.dumps(avg))
    if outp:
        Path(outp).write_text(json.dumps(res, indent=1, ensure_ascii=False))
